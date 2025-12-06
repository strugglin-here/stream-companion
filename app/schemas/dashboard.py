"""Pydantic schemas for Dashboard model"""

from typing import List, Optional
from pydantic import BaseModel, Field


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
