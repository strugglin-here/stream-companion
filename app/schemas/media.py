"""Pydantic schemas for Media API"""

from datetime import datetime
from pydantic import BaseModel, Field


class MediaItem(BaseModel):
    """Single media file information"""
    filename: str
    path: str
    size: int = Field(..., description="File size in bytes")
    mime_type: str
    uploaded_at: datetime
    url: str = Field(..., description="URL to access the file")


class MediaList(BaseModel):
    """List of media files"""
    files: list[MediaItem]  # Changed from 'items' to 'files' for frontend compatibility
    total: int
