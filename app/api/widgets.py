"""Widget API endpoints"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.widget import Widget
from app.models.element import Element, ElementType
from app.widgets import get_widget_class, list_widget_types


router = APIRouter(prefix="/widgets", tags=["widgets"])


# Pydantic schemas

class WidgetCreate(BaseModel):
    """Schema for creating a widget"""
    widget_class: str = Field(..., description="Widget class identifier (e.g., 'ConfettiAlertWidget')")
    name: str = Field(..., min_length=1, max_length=255, description="User-given name for this widget")
    widget_parameters: Optional[Dict[str, Any]] = Field(None, description="Optional widget configuration")
    dashboard_ids: Optional[List[int]] = Field(None, description="Optional list of dashboard IDs to add widget to")


class WidgetUpdate(BaseModel):
    """Schema for updating a widget"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    widget_parameters: Optional[Dict[str, Any]] = None


class ElementResponse(BaseModel):
    """Element details in widget response"""
    id: int
    element_type: str
    name: str
    asset_path: Optional[str]
    properties: Dict[str, Any]
    behavior: Dict[str, Any]
    enabled: bool
    visible: bool
    
    model_config = {"from_attributes": True}


class FeatureResponse(BaseModel):
    """Feature definition in widget response"""
    method_name: str
    display_name: str
    description: str
    parameters: List[Dict[str, Any]]


class WidgetResponse(BaseModel):
    """Schema for widget response with elements and features"""
    id: int
    widget_class: str
    name: str
    widget_parameters: Dict[str, Any]
    created_at: str
    updated_at: str
    elements: List[ElementResponse] = []
    features: List[FeatureResponse] = []
    dashboard_ids: List[int] = []
    
    model_config = {"from_attributes": True}


class WidgetTypeResponse(BaseModel):
    """Widget type definition from registry"""
    widget_class: str
    display_name: str
    description: str
    default_parameters: Dict[str, Any]
    features: List[FeatureResponse]


class WidgetTypeList(BaseModel):
    """List of available widget types"""
    widget_types: List[WidgetTypeResponse]
    total: int


class FeatureExecute(BaseModel):
    """Schema for executing a widget feature"""
    feature_name: str = Field(..., description="Method name of the feature to execute")
    feature_params: Optional[Dict[str, Any]] = Field(None, description="Parameters for the feature")


# API endpoints

@router.get("/types", response_model=WidgetTypeList)
async def get_widget_types():
    """
    List all available widget types from the registry.
    
    Returns metadata about each widget class including:
    - Widget class identifier
    - Display name and description
    - Default parameters
    - Available features with parameter definitions
    
    Returns:
        List of widget type definitions
    """
    widget_types = list_widget_types()
    
    return WidgetTypeList(
        widget_types=[
            WidgetTypeResponse(
                widget_class=wt["widget_class"],
                display_name=wt["display_name"],
                description=wt["description"],
                default_parameters=wt["default_parameters"],
                features=[
                    FeatureResponse(
                        method_name=f["method_name"],
                        display_name=f["display_name"],
                        description=f["description"],
                        parameters=f["parameters"]
                    )
                    for f in wt["features"]
                ]
            )
            for wt in widget_types
        ],
        total=len(widget_types)
    )


@router.get("/", response_model=List[WidgetResponse])
async def list_widgets(
    exclude_dashboard_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List all widget instances in the database.
    
    Args:
        exclude_dashboard_id: Optional dashboard ID to exclude widgets that are already on that dashboard
        db: Database session
    
    Returns:
        List of all widget instances with their elements and features
    """
    try:
        # Get all widgets
        result = await db.execute(select(Widget))
        widgets = result.scalars().all()
        
        widget_responses = []
        for widget in widgets:
            try:
                # Get dashboard IDs
                dashboard_ids = [d.id for d in widget.dashboards]
                
                # If filtering by dashboard, skip widgets already on that dashboard
                if exclude_dashboard_id is not None and exclude_dashboard_id in dashboard_ids:
                    continue
                
                # Load widget class to get features
                widget_cls = get_widget_class(widget.widget_class)
                if not widget_cls:
                    continue
                
                widget_instance = await widget_cls.load(db, widget.id)
                
                # Get elements - handle both dict and list
                elements_list = (
                    list(widget_instance.elements.values()) 
                    if isinstance(widget_instance.elements, dict) 
                    else widget_instance.elements
                )
                
                widget_responses.append(WidgetResponse(
                    id=widget.id,
                    widget_class=widget.widget_class,
                    name=widget.name,
                    widget_parameters=widget.widget_parameters,
                    created_at=widget.created_at.isoformat(),
                    updated_at=widget.updated_at.isoformat(),
                    elements=[
                        ElementResponse(
                            id=elem.id,
                            element_type=elem.element_type.value if hasattr(elem.element_type, 'value') else elem.element_type,
                            name=elem.name,
                            asset_path=elem.asset_path,
                            properties=elem.properties,
                            behavior=elem.behavior,
                            enabled=elem.enabled,
                            visible=elem.visible
                        )
                        for elem in elements_list
                    ],
                    features=[
                        FeatureResponse(
                            method_name=f["method_name"],
                            display_name=f["display_name"],
                            description=f["description"],
                            parameters=f["parameters"]
                        )
                        for f in widget_cls.get_features()
                    ],
                    dashboard_ids=dashboard_ids
                ))
            except Exception as widget_error:
                # Log error but continue with other widgets
                print(f"Error loading widget {widget.id} ({widget.widget_class}): {widget_error}")
                import traceback
                traceback.print_exc()
                continue
        
        return widget_responses
    except Exception as e:
        print(f"Error in list_widgets: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to list widgets: {str(e)}")


@router.post("/", response_model=WidgetResponse, status_code=201)
async def create_widget(
    widget_data: WidgetCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new widget instance.
    
    This will:
    1. Instantiate the widget class
    2. Create default elements
    3. Optionally add to specified dashboards
    
    Args:
        widget_data: Widget creation data
        db: Database session
    
    Returns:
        Created widget with elements and features
    
    Raises:
        HTTPException: If widget class not found or creation fails
    """
    # Get widget class from registry
    widget_cls = get_widget_class(widget_data.widget_class)
    
    if not widget_cls:
        raise HTTPException(
            status_code=400,
            detail=f"Widget class '{widget_data.widget_class}' not found. "
                   f"Use GET /api/widgets/types to see available widget types."
        )
    
    try:
        # Create widget instance (this also creates default elements)
        widget_instance = await widget_cls.create(
            db=db,
            name=widget_data.name,
            widget_parameters=widget_data.widget_parameters,
            dashboard_ids=widget_data.dashboard_ids
        )
        
        # Refresh to get all relationships
        await db.refresh(widget_instance.db_widget)
        
        # Build response
        return WidgetResponse(
            id=widget_instance.db_widget.id,
            widget_class=widget_instance.db_widget.widget_class,
            name=widget_instance.db_widget.name,
            widget_parameters=widget_instance.db_widget.widget_parameters,
            created_at=widget_instance.db_widget.created_at.isoformat(),
            updated_at=widget_instance.db_widget.updated_at.isoformat(),
            elements=[
                ElementResponse(
                    id=elem.id,
                    element_type=elem.element_type.value if hasattr(elem.element_type, 'value') else elem.element_type,
                    name=elem.name,
                    asset_path=elem.asset_path,
                    properties=elem.properties,
                    behavior=elem.behavior,
                    enabled=elem.enabled,
                    visible=elem.visible
                )
                for elem in widget_instance.elements.values()
            ],
            features=[
                FeatureResponse(
                    method_name=f["method_name"],
                    display_name=f["display_name"],
                    description=f["description"],
                    parameters=f["parameters"]
                )
                for f in widget_cls.get_features()
            ],
            dashboard_ids=[d.id for d in widget_instance.db_widget.dashboards]
        )
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating widget: {str(e)}"
        )


@router.get("/{widget_id}", response_model=WidgetResponse)
async def get_widget(
    widget_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific widget by ID.
    
    Returns widget details including:
    - Configuration (widget_parameters)
    - Owned elements
    - Available features
    - Dashboard associations
    
    Args:
        widget_id: Widget ID
        db: Database session
    
    Returns:
        Widget details
    
    Raises:
        HTTPException: If widget not found
    """
    result = await db.execute(
        select(Widget).where(Widget.id == widget_id)
    )
    db_widget = result.scalar_one_or_none()
    
    if not db_widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    
    # Get widget class to extract features
    widget_cls = get_widget_class(db_widget.widget_class)
    
    if not widget_cls:
        raise HTTPException(
            status_code=500,
            detail=f"Widget class '{db_widget.widget_class}' not registered"
        )
    
    # Get elements
    elem_result = await db.execute(
        select(Element).where(Element.widget_id == widget_id)
    )
    elements = elem_result.scalars().all()
    
    return WidgetResponse(
        id=db_widget.id,
        widget_class=db_widget.widget_class,
        name=db_widget.name,
        widget_parameters=db_widget.widget_parameters,
        created_at=db_widget.created_at.isoformat(),
        updated_at=db_widget.updated_at.isoformat(),
        elements=[
            ElementResponse(
                id=elem.id,
                element_type=elem.element_type.value if hasattr(elem.element_type, 'value') else elem.element_type,
                name=elem.name,
                asset_path=elem.asset_path,
                properties=elem.properties,
                behavior=elem.behavior,
                enabled=elem.enabled,
                visible=elem.visible
            )
            for elem in elements
        ],
        features=[
            FeatureResponse(
                method_name=f["method_name"],
                display_name=f["display_name"],
                description=f["description"],
                parameters=f["parameters"]
            )
            for f in widget_cls.get_features()
        ],
        dashboard_ids=[d.id for d in db_widget.dashboards]
    )


@router.patch("/{widget_id}", response_model=WidgetResponse)
async def update_widget(
    widget_id: int,
    widget_data: WidgetUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a widget's name or parameters.
    
    Args:
        widget_id: Widget ID
        widget_data: Fields to update
        db: Database session
    
    Returns:
        Updated widget
    
    Raises:
        HTTPException: If widget not found
    """
    result = await db.execute(
        select(Widget).where(Widget.id == widget_id)
    )
    db_widget = result.scalar_one_or_none()
    
    if not db_widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    
    # Update name if provided
    if widget_data.name:
        db_widget.name = widget_data.name
    
    # Update parameters if provided (merge with existing)
    if widget_data.widget_parameters is not None:
        current_params = db_widget.widget_parameters or {}
        current_params.update(widget_data.widget_parameters)
        db_widget.widget_parameters = current_params
    
    await db.commit()
    await db.refresh(db_widget)
    
    # Get widget class and elements for response
    widget_cls = get_widget_class(db_widget.widget_class)
    
    if not widget_cls:
        raise HTTPException(
            status_code=500,
            detail=f"Widget class '{db_widget.widget_class}' not registered"
        )
    
    elem_result = await db.execute(
        select(Element).where(Element.widget_id == widget_id)
    )
    elements = elem_result.scalars().all()
    
    return WidgetResponse(
        id=db_widget.id,
        widget_class=db_widget.widget_class,
        name=db_widget.name,
        widget_parameters=db_widget.widget_parameters,
        created_at=db_widget.created_at.isoformat(),
        updated_at=db_widget.updated_at.isoformat(),
        elements=[
            ElementResponse(
                id=elem.id,
                element_type=elem.element_type.value if hasattr(elem.element_type, 'value') else elem.element_type,
                name=elem.name,
                asset_path=elem.asset_path,
                properties=elem.properties,
                behavior=elem.behavior,
                enabled=elem.enabled,
                visible=elem.visible
            )
            for elem in elements
        ],
        features=[
            FeatureResponse(
                method_name=f["method_name"],
                display_name=f["display_name"],
                description=f["description"],
                parameters=f["parameters"]
            )
            for f in widget_cls.get_features()
        ],
        dashboard_ids=[d.id for d in db_widget.dashboards]
    )


@router.delete("/{widget_id}", status_code=204)
async def delete_widget(
    widget_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a widget and all its owned elements.
    
    This will:
    1. Remove widget from all dashboards
    2. Delete all owned elements (cascade)
    3. Delete the widget
    
    Args:
        widget_id: Widget ID
        db: Database session
    
    Raises:
        HTTPException: If widget not found
    """
    result = await db.execute(
        select(Widget).where(Widget.id == widget_id)
    )
    db_widget = result.scalar_one_or_none()
    
    if not db_widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    
    await db.delete(db_widget)
    await db.commit()


@router.post("/{widget_id}/execute")
async def execute_widget_feature(
    widget_id: int,
    execution_data: FeatureExecute,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute a widget feature.
    
    This will:
    1. Load the widget instance
    2. Validate the feature exists
    3. Execute the feature with provided parameters
    4. Commit any database changes
    5. Broadcast updates via WebSocket
    
    Args:
        widget_id: Widget ID
        execution_data: Feature name and parameters
        db: Database session
    
    Returns:
        Result from feature execution (if any)
    
    Raises:
        HTTPException: If widget not found or feature execution fails
    """
    # Get widget from database
    result = await db.execute(
        select(Widget).where(Widget.id == widget_id)
    )
    db_widget = result.scalar_one_or_none()
    
    if not db_widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    
    # Get widget class
    widget_cls = get_widget_class(db_widget.widget_class)
    
    if not widget_cls:
        raise HTTPException(
            status_code=500,
            detail=f"Widget class '{db_widget.widget_class}' not registered"
        )
    
    try:
        # Load widget instance
        widget_instance = await widget_cls.load(db, widget_id)
        
        # Execute feature
        result = await widget_instance.execute_feature(
            execution_data.feature_name,
            execution_data.feature_params
        )
        
        return {
            "status": "success",
            "widget_id": widget_id,
            "feature_name": execution_data.feature_name,
            "result": result
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error executing feature: {str(e)}"
        )
