"""Widget API endpoints"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.widget import Widget
from app.models.element import Element
from app.widgets import get_widget_class, list_widget_types
from app.schemas.widget import (
    WidgetCreate,
    WidgetUpdate,
    WidgetResponse,
    WidgetTypeResponse,
    WidgetTypeList,
    ElementResponse,
    FeatureResponse,
    FeatureExecute
)
from app.schemas.element import ElementUpdate
from app.api.serializers import (
    serialize_widget_response,
    serialize_widget_type,
    serialize_element_detail,
)


router = APIRouter(prefix="/widgets", tags=["widgets"])


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

    # list_widget_types already returns metadata dicts; convert them to the
    # response format expected by the schema (FeatureResponse objects will be
    # validated by FastAPI/Pydantic on return).
    return {
        "widget_types": widget_types,
        "total": len(widget_types),
    }


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

                widget_responses.append(
                    serialize_widget_response(
                        widget_instance.db_widget,
                        elements=elements_list,
                        features=widget_cls.get_features(),
                        dashboard_ids=dashboard_ids,
                    )
                )

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
            dashboard_ids=widget_data.dashboard_ids,
        )

        # Refresh to get all relationships
        await db.refresh(widget_instance.db_widget)

        # Build response using serializer
        return serialize_widget_response(
            widget_instance.db_widget,
            elements=widget_instance.elements.values(),
            features=widget_cls.get_features(),
            dashboard_ids=[d.id for d in widget_instance.db_widget.dashboards],
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating widget: {str(e)}")


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
    try:
        result = await db.execute(select(Widget).where(Widget.id == widget_id))
        db_widget = result.scalar_one_or_none()

        if not db_widget:
            raise HTTPException(status_code=404, detail="Widget not found")

        # Get widget class to extract features
        widget_cls = get_widget_class(db_widget.widget_class)

        if not widget_cls:
            raise HTTPException(status_code=500, detail=f"Widget class '{db_widget.widget_class}' not registered")

        # Get elements
        elem_result = await db.execute(select(Element).where(Element.widget_id == widget_id))
        elements = elem_result.scalars().all()

        return serialize_widget_response(
            db_widget,
            elements=elements,
            features=widget_cls.get_features(),
            dashboard_ids=[d.id for d in db_widget.dashboards],
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_widget({widget_id}): {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


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
    
    # Update parameters if provided (replace, not merge)
    if widget_data.widget_parameters is not None:
        db_widget.widget_parameters = widget_data.widget_parameters
    
    await db.commit()
    await db.refresh(db_widget)

    # Get widget class and elements for response
    widget_cls = get_widget_class(db_widget.widget_class)

    if not widget_cls:
        raise HTTPException(status_code=500, detail=f"Widget class '{db_widget.widget_class}' not registered")

    elem_result = await db.execute(select(Element).where(Element.widget_id == widget_id))
    elements = elem_result.scalars().all()

    return serialize_widget_response(
        db_widget,
        elements=elements,
        features=widget_cls.get_features(),
        dashboard_ids=[d.id for d in db_widget.dashboards],
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
    
    try:
        # Get widget from database
        result = await db.execute(select(Widget).where(Widget.id == widget_id))
        db_widget = result.scalar_one_or_none()

        if not db_widget:
            raise HTTPException(status_code=404, detail="Widget not found")

        # Get widget class
        widget_cls = get_widget_class(db_widget.widget_class)

        if not widget_cls:
            raise HTTPException(status_code=500, detail=f"Widget class '{db_widget.widget_class}' not registered")

        try:
            # Load widget instance
            widget_instance = await widget_cls.load(db, widget_id)

            # Execute feature
            result = await widget_instance.execute_feature(
                execution_data.feature_name, execution_data.feature_params
            )

            return {
                "status": "success",
                "widget_id": widget_id,
                "feature_name": execution_data.feature_name,
                "result": result,
            }

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error executing feature: {str(e)}")

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{widget_id}/elements", response_model=List[ElementResponse])
async def get_widget_elements(
    widget_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all elements for a specific widget.

    Args:
        widget_id: Widget ID
        db: Database session

    Returns:
        List of elements owned by the widget

    Raises:
        HTTPException: If widget not found
    """
    # Verify widget exists
    result = await db.execute(select(Widget).where(Widget.id == widget_id))
    db_widget = result.scalar_one_or_none()

    if not db_widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    # Get elements
    elem_result = await db.execute(select(Element).where(Element.widget_id == widget_id))
    elements = elem_result.scalars().all()

    return [serialize_element_detail(elem) for elem in elements]


@router.patch("/{widget_id}/elements/{element_id}", response_model=ElementResponse)
async def update_widget_element(
    widget_id: int,
    element_id: int,
    element_update: ElementUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a widget's element.
    
    This endpoint allows updating element properties directly without
    going through widget features. Useful for administrative changes.
    
    Args:
        widget_id: Widget ID
        element_id: Element ID
        element_update: Fields to update
        db: Database session
    
    Returns:
        Updated element
    
    Raises:
        HTTPException: If widget or element not found, or element doesn't belong to widget
    """
    # Verify widget exists
    result = await db.execute(
        select(Widget).where(Widget.id == widget_id)
    )
    db_widget = result.scalar_one_or_none()
    
    if not db_widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    
    # Get element and verify ownership
    elem_result = await db.execute(
        select(Element).where(Element.id == element_id)
    )
    element = elem_result.scalar_one_or_none()
    
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    
    if element.widget_id != widget_id:
        raise HTTPException(
            status_code=403,
            detail="Element does not belong to this widget"
        )
    
    try:
        # Update only provided fields
        update_data = element_update.model_dump(exclude_unset=True)
        
        # Normalize asset_path: strip /uploads/ prefix if present to store just filename
        if 'asset_path' in update_data and update_data['asset_path']:
            asset_path = update_data['asset_path']
            if asset_path.startswith('/uploads/'):
                update_data['asset_path'] = asset_path.replace('/uploads/', '', 1)

        for field, value in update_data.items():
            setattr(element, field, value)

        await db.commit()
        await db.refresh(element)

        # Broadcast element update via WebSocket
        from app.core.websocket import manager
        await manager.broadcast_element_update(element, action="update")

        return serialize_element_detail(element)
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating element: {str(e)}"
        )
