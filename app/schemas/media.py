"""Pydantic schemas for Media API"""

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class MediaItem(BaseModel):
    """Single media file information"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    filename: str
    original_filename: str
    path: str  # For backward compatibility, same as filename
    size: int = Field(..., description="File size in bytes")
    mime_type: str
    uploaded_at: datetime
    url: str = Field(..., description="URL to access the file")


class MediaList(BaseModel):
    """List of media files"""
    files: list[MediaItem]  # Changed from 'items' to 'files' for frontend compatibility
    total: int
