"""Media upload and management endpoints"""

from pathlib import Path
from typing import Optional
from datetime import datetime

from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.files import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    validate_file_extension,
    validate_file_size,
    get_unique_filepath,
    save_upload_file,
)
from app.schemas.media import MediaItem, MediaList


router = APIRouter(prefix="/media", tags=["media"])

# Response model for batch uploads
class BatchUploadResponse(BaseModel):
    uploaded: list[MediaItem]
    failed: list[dict]
    total: int


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
    # Validate file extension and size
    validate_file_extension(file.filename)
    validate_file_size(file.size)
    
    # Get unique filepath
    media_dir = get_media_directory()
    target_path = get_unique_filepath(media_dir, file.filename)
    
    # Save the file
    await save_upload_file(file, target_path)
    
    return get_file_info(target_path)


@router.post("/", response_model=BatchUploadResponse, status_code=201)
async def upload_multiple_media(
    files: list[UploadFile] = File(..., description="Media files to upload")
) -> BatchUploadResponse:
    """
    Upload multiple media files at once.
    
    Supported formats:
    - Images: PNG, JPEG, GIF, WebP, SVG
    - Videos: MP4, WebM, MOV
    - Audio: MP3, WAV, OGG
    
    Maximum file size per file: 100MB
    """
    uploaded = []
    failed = []
    media_dir = get_media_directory()
    
    for file in files:
        try:
            # Validate file extension and size
            validate_file_extension(file.filename)
            validate_file_size(file.size)
            
            # Get unique filepath
            target_path = get_unique_filepath(media_dir, file.filename)
            
            # Save file
            await save_upload_file(file, target_path)
            
            uploaded.append(get_file_info(target_path))
            
        except HTTPException as e:
            failed.append({
                "filename": file.filename,
                "error": e.detail
            })
        except Exception as e:
            failed.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return BatchUploadResponse(
        uploaded=uploaded,
        failed=failed,
        total=len(files)
    )


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
        files=media_items,
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
