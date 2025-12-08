"""Pydantic schemas for Element model"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from app.models.element import ElementType


class MediaAssetRef(BaseModel):
    """Reference to a media asset with role"""
    media_id: int = Field(..., description="ID of media file")
    role: str = Field(default="primary", description="Asset role (primary, background, front_content, etc.)")


class ElementBase(BaseModel):
    """Base schema with common fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Unique element name within widget (immutable after creation)")
    element_type: ElementType = Field(..., description="Type of element")
    description: Optional[str] = Field(None, max_length=1000, description="Element description")
    
    # Media relationship field
    media_assets: Optional[List[MediaAssetRef]] = Field(None, description="Media assets with roles")
    
    visible: bool = Field(False, description="Whether element is currently visible")
    properties: dict = Field(default_factory=dict, description="Display properties (position, size, style)")
    behavior: dict = Field(default_factory=dict, description="Animation and interaction behavior")


class ElementCreate(ElementBase):
    """Schema for creating a new element"""
    pass


class ElementUpdate(BaseModel):
    """Schema for updating an element (all fields optional for partial updates).
    
    Note: Element name is immutable after creation and cannot be updated.
    This is because widget features reference elements by name.
    """
    model_config = ConfigDict(extra='forbid')
    
    # name is NOT included - element names are immutable after creation
    element_type: Optional[ElementType] = None
    description: Optional[str] = Field(None, max_length=1000)
    
    # Media relationship field
    media_assets: Optional[List[MediaAssetRef]] = None
    
    visible: Optional[bool] = None
    properties: Optional[dict] = None
    behavior: Optional[dict] = None


class ElementResponse(ElementBase):
    """Schema for element responses (includes DB-generated fields).
    
    Frontend can use whichever is most convenient.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime
    
    # Computed field: media assets with their full details
    media_details: Optional[List[Dict[str, Any]]] = Field(None, description="Full media details for each asset (id, filename, url, role)")


class ElementList(BaseModel):
    """Schema for paginated element list"""
    items: list[ElementResponse]
    total: int
    page: int = 1
    page_size: int = 50
