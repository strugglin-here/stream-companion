"""Dashboard API endpoints"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.websocket import manager
from app.models.dashboard import Dashboard
from app.models.widget import Widget


router = APIRouter(prefix="/dashboards", tags=["dashboards"])


# Pydantic schemas for request/response

class DashboardCreate(BaseModel):
    """Schema for creating a dashboard"""
    name: str = Field(..., min_length=1, max_length=255, description="Dashboard name")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description")


class DashboardUpdate(BaseModel):
    """Schema for updating a dashboard"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class WidgetSummary(BaseModel):
    """Summary of a widget for dashboard response"""
    id: int
    widget_class: str
    name: str
    
    model_config = {"from_attributes": True}


class DashboardResponse(BaseModel):
    """Schema for dashboard response"""
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str
    widgets: List[WidgetSummary] = []
    
    model_config = {"from_attributes": True}


class DashboardList(BaseModel):
    """List of dashboards"""
    dashboards: List[DashboardResponse]
    total: int


# API endpoints

@router.get("/", response_model=DashboardList)
async def list_dashboards(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    List all dashboards.
    
    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session
    
    Returns:
        List of dashboards with their widgets
    """
    # Get total count
    count_result = await db.execute(select(Dashboard))
    all_dashboards = count_result.scalars().all()
    total = len(all_dashboards)
    
    # Get paginated results
    result = await db.execute(
        select(Dashboard)
        .offset(skip)
        .limit(limit)
        .order_by(Dashboard.created_at.desc())
    )
    dashboards = result.scalars().all()
    
    return DashboardList(
        dashboards=[
            DashboardResponse(
                id=d.id,
                name=d.name,
                description=d.description,
                is_active=d.is_active,
                created_at=d.created_at.isoformat(),
                updated_at=d.updated_at.isoformat(),
                widgets=[
                    WidgetSummary(
                        id=w.id,
                        widget_class=w.widget_class,
                        name=w.name
                    )
                    for w in d.widgets
                ]
            )
            for d in dashboards
        ],
        total=total
    )


@router.post("/", response_model=DashboardResponse, status_code=201)
async def create_dashboard(
    dashboard_data: DashboardCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new dashboard.
    
    Args:
        dashboard_data: Dashboard creation data
        db: Database session
    
    Returns:
        Created dashboard
    
    Raises:
        HTTPException: If dashboard name already exists
    """
    # Check for duplicate name
    result = await db.execute(
        select(Dashboard).where(Dashboard.name == dashboard_data.name)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Dashboard with name '{dashboard_data.name}' already exists"
        )
    
    # Create dashboard
    dashboard = Dashboard(
        name=dashboard_data.name,
        description=dashboard_data.description,
        is_active=False  # New dashboards start inactive
    )
    
    db.add(dashboard)
    await db.commit()
    await db.refresh(dashboard)
    
    return DashboardResponse(
        id=dashboard.id,
        name=dashboard.name,
        description=dashboard.description,
        is_active=dashboard.is_active,
        created_at=dashboard.created_at.isoformat(),
        updated_at=dashboard.updated_at.isoformat(),
        widgets=[]
    )


@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific dashboard by ID.
    
    Args:
        dashboard_id: Dashboard ID
        db: Database session
    
    Returns:
        Dashboard details with widgets
    
    Raises:
        HTTPException: If dashboard not found
    """
    result = await db.execute(
        select(Dashboard).where(Dashboard.id == dashboard_id)
    )
    dashboard = result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    return DashboardResponse(
        id=dashboard.id,
        name=dashboard.name,
        description=dashboard.description,
        is_active=dashboard.is_active,
        created_at=dashboard.created_at.isoformat(),
        updated_at=dashboard.updated_at.isoformat(),
        widgets=[
            WidgetSummary(
                id=w.id,
                widget_class=w.widget_class,
                name=w.name
            )
            for w in dashboard.widgets
        ]
    )


@router.patch("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: int,
    dashboard_data: DashboardUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a dashboard's name or description.
    
    Args:
        dashboard_id: Dashboard ID
        dashboard_data: Fields to update
        db: Database session
    
    Returns:
        Updated dashboard
    
    Raises:
        HTTPException: If dashboard not found or name conflicts
    """
    result = await db.execute(
        select(Dashboard).where(Dashboard.id == dashboard_id)
    )
    dashboard = result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    # Check for name conflict if name is being updated
    if dashboard_data.name and dashboard_data.name != dashboard.name:
        name_check = await db.execute(
            select(Dashboard).where(Dashboard.name == dashboard_data.name)
        )
        existing = name_check.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Dashboard with name '{dashboard_data.name}' already exists"
            )
        dashboard.name = dashboard_data.name
    
    # Update description if provided
    if dashboard_data.description is not None:
        dashboard.description = dashboard_data.description
    
    await db.commit()
    await db.refresh(dashboard)
    
    return DashboardResponse(
        id=dashboard.id,
        name=dashboard.name,
        description=dashboard.description,
        is_active=dashboard.is_active,
        created_at=dashboard.created_at.isoformat(),
        updated_at=dashboard.updated_at.isoformat(),
        widgets=[
            WidgetSummary(
                id=w.id,
                widget_class=w.widget_class,
                name=w.name
            )
            for w in dashboard.widgets
        ]
    )


@router.delete("/{dashboard_id}", status_code=204)
async def delete_dashboard(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a dashboard.
    
    Note: This does NOT delete widgets, only removes the association.
    Widgets can exist on multiple dashboards.
    
    Args:
        dashboard_id: Dashboard ID
        db: Database session
    
    Raises:
        HTTPException: If dashboard not found
    """
    result = await db.execute(
        select(Dashboard).where(Dashboard.id == dashboard_id)
    )
    dashboard = result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    # If this was the active dashboard, broadcast deactivation
    if dashboard.is_active:
        await manager.broadcast_dashboard_event("dashboard_deactivated", dashboard_id)
    
    await db.delete(dashboard)
    await db.commit()


@router.post("/{dashboard_id}/activate", response_model=DashboardResponse)
async def activate_dashboard(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Activate a dashboard (deactivates all others).
    
    When a dashboard is activated:
    1. Previous active dashboard is deactivated
    2. WebSocket event sent: dashboard_deactivated (old)
    3. New dashboard becomes active
    4. WebSocket event sent: dashboard_activated (new)
    
    Args:
        dashboard_id: Dashboard ID to activate
        db: Database session
    
    Returns:
        Activated dashboard
    
    Raises:
        HTTPException: If dashboard not found
    """
    # Get the target dashboard
    result = await db.execute(
        select(Dashboard).where(Dashboard.id == dashboard_id)
    )
    dashboard = result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    # If already active, nothing to do
    if dashboard.is_active:
        return DashboardResponse(
            id=dashboard.id,
            name=dashboard.name,
            description=dashboard.description,
            is_active=dashboard.is_active,
            created_at=dashboard.created_at.isoformat(),
            updated_at=dashboard.updated_at.isoformat(),
            widgets=[
                WidgetSummary(
                    id=w.id,
                    widget_class=w.widget_class,
                    name=w.name
                )
                for w in dashboard.widgets
            ]
        )
    
    # Find currently active dashboard
    active_result = await db.execute(
        select(Dashboard).where(Dashboard.is_active == True)
    )
    current_active = active_result.scalar_one_or_none()
    
    # Deactivate current active dashboard
    if current_active:
        current_active.is_active = False
        await manager.broadcast_dashboard_event("dashboard_deactivated", current_active.id)
    
    # Activate new dashboard
    dashboard.is_active = True
    await db.commit()
    await db.refresh(dashboard)
    
    # Broadcast activation event
    await manager.broadcast_dashboard_event("dashboard_activated", dashboard.id)
    
    return DashboardResponse(
        id=dashboard.id,
        name=dashboard.name,
        description=dashboard.description,
        is_active=dashboard.is_active,
        created_at=dashboard.created_at.isoformat(),
        updated_at=dashboard.updated_at.isoformat(),
        widgets=[
            WidgetSummary(
                id=w.id,
                widget_class=w.widget_class,
                name=w.name
            )
            for w in dashboard.widgets
        ]
    )


@router.post("/{dashboard_id}/widgets/{widget_id}", status_code=204)
async def add_widget_to_dashboard(
    dashboard_id: int,
    widget_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Add an existing widget to a dashboard.
    
    Args:
        dashboard_id: Dashboard ID
        widget_id: Widget ID to add
        db: Database session
    
    Raises:
        HTTPException: If dashboard or widget not found, or already associated
    """
    # Get dashboard
    dash_result = await db.execute(
        select(Dashboard).where(Dashboard.id == dashboard_id)
    )
    dashboard = dash_result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    # Get widget
    widget_result = await db.execute(
        select(Widget).where(Widget.id == widget_id)
    )
    widget = widget_result.scalar_one_or_none()
    
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    
    # Check if already associated
    if widget in dashboard.widgets:
        raise HTTPException(
            status_code=400,
            detail="Widget already on this dashboard"
        )
    
    # Add association
    dashboard.widgets.append(widget)
    await db.commit()


@router.delete("/{dashboard_id}/widgets/{widget_id}", status_code=204)
async def remove_widget_from_dashboard(
    dashboard_id: int,
    widget_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a widget from a dashboard.
    
    Note: This does NOT delete the widget, only removes the association.
    
    Args:
        dashboard_id: Dashboard ID
        widget_id: Widget ID to remove
        db: Database session
    
    Raises:
        HTTPException: If dashboard or widget not found, or not associated
    """
    # Get dashboard
    dash_result = await db.execute(
        select(Dashboard).where(Dashboard.id == dashboard_id)
    )
    dashboard = dash_result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    # Get widget
    widget_result = await db.execute(
        select(Widget).where(Widget.id == widget_id)
    )
    widget = widget_result.scalar_one_or_none()
    
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    
    # Check if associated
    if widget not in dashboard.widgets:
        raise HTTPException(
            status_code=400,
            detail="Widget not on this dashboard"
        )
    
    # Remove association
    dashboard.widgets.remove(widget)
    await db.commit()
