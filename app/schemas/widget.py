"""Pydantic schemas for Widget model"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


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
