"""Media upload and management endpoints"""

import os
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.core.config import settings


router = APIRouter(prefix="/media", tags=["media"])


# Pydantic models for API responses
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
    items: list[MediaItem]
    total: int


# Allowed file extensions and MIME types
ALLOWED_EXTENSIONS = {
    # Images
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.svg': 'image/svg+xml',
    # Videos
    '.mp4': 'video/mp4',
    '.webm': 'video/webm',
    '.mov': 'video/quicktime',
    # Audio
    '.mp3': 'audio/mpeg',
    '.wav': 'audio/wav',
    '.ogg': 'audio/ogg',
}

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


def get_media_directory() -> Path:
    """Get the media directory path, create if doesn't exist"""
    media_dir = Path(settings.upload_directory)
    media_dir.mkdir(parents=True, exist_ok=True)
    return media_dir


def get_file_info(file_path: Path) -> MediaItem:
    """Get metadata for a media file"""
    stat = file_path.stat()
    ext = file_path.suffix.lower()
    mime_type = ALLOWED_EXTENSIONS.get(ext, 'application/octet-stream')
    
    return MediaItem(
        filename=file_path.name,
        path=str(file_path.relative_to(get_media_directory())),
        size=stat.st_size,
        mime_type=mime_type,
        uploaded_at=datetime.fromtimestamp(stat.st_mtime),
        url=f"/uploads/{file_path.name}"
    )


@router.post("/upload", response_model=MediaItem, status_code=201)
async def upload_media(
    file: UploadFile = File(..., description="Media file to upload")
) -> MediaItem:
    """
    Upload a media file (image, video, or audio).
    
    Supported formats:
    - Images: PNG, JPEG, GIF, WebP, SVG
    - Videos: MP4, WebM, MOV
    - Audio: MP3, WAV, OGG
    
    Maximum file size: 100MB
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        allowed = ', '.join(ALLOWED_EXTENSIONS.keys())
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Supported types: {allowed}"
        )
    
    # Validate file size (if content_length is available)
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Ensure unique filename
    media_dir = get_media_directory()
    base_name = Path(file.filename).stem
    counter = 1
    target_path = media_dir / file.filename
    
    while target_path.exists():
        new_name = f"{base_name}_{counter}{file_ext}"
        target_path = media_dir / new_name
        counter += 1
    
    # Save the file
    try:
        with target_path.open('wb') as f:
            # Read in chunks to handle large files
            chunk_size = 1024 * 1024  # 1MB chunks
            total_size = 0
            
            while chunk := await file.read(chunk_size):
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    # Clean up partial file
                    target_path.unlink()
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
                    )
                f.write(chunk)
        
        return get_file_info(target_path)
    
    except Exception as e:
        # Clean up on error
        if target_path.exists():
            target_path.unlink()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/", response_model=MediaList)
async def list_media(
    type: Optional[str] = Query(None, description="Filter by type: image, video, audio"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of files to return"),
) -> MediaList:
    """
    List all uploaded media files.
    
    Can optionally filter by media type (image, video, audio).
    """
    media_dir = get_media_directory()
    
    # Collect all media files
    media_items = []
    
    for file_path in media_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in ALLOWED_EXTENSIONS:
            # Filter by type if specified
            if type:
                mime_type = ALLOWED_EXTENSIONS.get(file_path.suffix.lower(), '')
                if not mime_type.startswith(f"{type}/"):
                    continue
            
            try:
                media_items.append(get_file_info(file_path))
            except Exception:
                # Skip files that can't be read
                continue
    
    # Sort by upload time (newest first)
    media_items.sort(key=lambda x: x.uploaded_at, reverse=True)
    
    # Apply limit
    media_items = media_items[:limit]
    
    return MediaList(
        items=media_items,
        total=len(media_items)
    )


@router.get("/{filename}")
async def get_media(filename: str) -> FileResponse:
    """
    Serve a media file.
    
    This endpoint is used to access uploaded media files.
    """
    media_dir = get_media_directory()
    file_path = media_dir / filename
    
    # Security: prevent directory traversal
    if not file_path.resolve().is_relative_to(media_dir.resolve()):
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get MIME type
    mime_type = ALLOWED_EXTENSIONS.get(file_path.suffix.lower(), 'application/octet-stream')
    
    return FileResponse(
        path=file_path,
        media_type=mime_type,
        filename=filename
    )


@router.delete("/{filename}", status_code=204)
async def delete_media(filename: str) -> None:
    """
    Delete a media file.
    
    This will permanently remove the file from the media directory.
    """
    media_dir = get_media_directory()
    file_path = media_dir / filename
    
    # Security: prevent directory traversal
    if not file_path.resolve().is_relative_to(media_dir.resolve()):
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")
    
    try:
        file_path.unlink()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
