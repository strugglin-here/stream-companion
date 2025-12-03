"""Pydantic schemas for Element model"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.element import ElementType


class ElementBase(BaseModel):
    """Base schema with common fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Unique element name")
    element_type: ElementType = Field(..., description="Type of element")
    description: Optional[str] = Field(None, max_length=1000, description="Element description")
    asset_path: Optional[str] = Field(None, max_length=500, description="Path to media asset in /media directory")
    enabled: bool = Field(True, description="Whether element is enabled")
    visible: bool = Field(False, description="Whether element is currently visible")
    properties: dict = Field(default_factory=dict, description="Display properties (position, size, style)")
    behavior: dict = Field(default_factory=dict, description="Animation and interaction behavior")


class ElementCreate(ElementBase):
    """Schema for creating a new element"""
    pass


class ElementUpdate(BaseModel):
    """Schema for updating an element (all fields optional for partial updates)"""
    model_config = ConfigDict(extra='forbid')
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    element_type: Optional[ElementType] = None
    description: Optional[str] = Field(None, max_length=1000)
    asset_path: Optional[str] = Field(None, max_length=500)
    enabled: Optional[bool] = None
    visible: Optional[bool] = None
    properties: Optional[dict] = None
    behavior: Optional[dict] = None


class ElementResponse(ElementBase):
    """Schema for element responses (includes DB-generated fields)"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


class ElementList(BaseModel):
    """Schema for paginated element list"""
    items: list[ElementResponse]
    total: int
    page: int = 1
    page_size: int = 50
