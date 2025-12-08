"""Media upload and management endpoints"""

from pathlib import Path
from typing import Optional
from datetime import datetime

from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.files import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    validate_file_extension,
    validate_file_size,
    get_unique_filepath,
    save_upload_file,
)
from app.schemas.media import MediaItem, MediaList
from app.models.media import Media
from app.api.serializers import serialize_media


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


async def create_media_record(
    db: AsyncSession,
    filename: str,
    original_filename: str,
    file_size: int,
    mime_type: str
) -> Media:
    """Create a Media database record for an uploaded file.
    
    Args:
        db: Database session
        filename: Stored filename (may be deduplicated)
        original_filename: Original uploaded filename
        file_size: File size in bytes
        mime_type: MIME type of the file
    
    Returns:
        Created Media object
    """
    media = Media(
        filename=filename,
        original_filename=original_filename,
        file_size=file_size,
        mime_type=mime_type
    )
    db.add(media)
    await db.commit()
    await db.refresh(media)
    return media


@router.post("/upload", response_model=MediaItem, status_code=201)
async def upload_media(
    file: UploadFile = File(..., description="Media file to upload"),
    db: AsyncSession = Depends(get_db)
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
    
    # Get MIME type
    ext = target_path.suffix.lower()
    mime_type = ALLOWED_EXTENSIONS.get(ext, 'application/octet-stream')
    
    # Create database record
    media = await create_media_record(
        db=db,
        filename=target_path.name,
        original_filename=file.filename,
        file_size=target_path.stat().st_size,
        mime_type=mime_type
    )
    
    return MediaItem(**serialize_media(media))


@router.post("/", response_model=BatchUploadResponse, status_code=201)
async def upload_multiple_media(
    files: list[UploadFile] = File(..., description="Media files to upload"),
    db: AsyncSession = Depends(get_db)
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
            
            # Get MIME type
            ext = target_path.suffix.lower()
            mime_type = ALLOWED_EXTENSIONS.get(ext, 'application/octet-stream')
            
            # Create database record
            media = await create_media_record(
                db=db,
                filename=target_path.name,
                original_filename=file.filename,
                file_size=target_path.stat().st_size,
                mime_type=mime_type
            )
            
            uploaded.append(MediaItem(**serialize_media(media)))
            
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
    db: AsyncSession = Depends(get_db)
) -> MediaList:
    """
    List all uploaded media files from the database.
    
    Can optionally filter by media type (image, video, audio).
    """
    # Build query
    query = select(Media)
    
    # Filter by type if specified
    if type:
        query = query.where(Media.mime_type.like(f"{type}/%"))
    
    # Order by most recent first
    query = query.order_by(Media.created_at.desc())
    
    # Apply limit
    query = query.limit(limit)
    
    # Execute query
    result = await db.execute(query)
    media_items = result.scalars().all()
    
    # Serialize to response format
    serialized_items = [MediaItem(**serialize_media(m)) for m in media_items]
    
    return MediaList(
        files=serialized_items,
        total=len(serialized_items)
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
async def delete_media(
    filename: str,
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a media file from both database and filesystem.
    
    This will permanently remove the file from the media directory and its database record.
    """
    # Find media record in database
    result = await db.execute(
        select(Media).where(Media.filename == filename)
    )
    media = result.scalar_one_or_none()
    
    if not media:
        raise HTTPException(status_code=404, detail="Media file not found in database")
    
    # Delete file from filesystem
    media_dir = get_media_directory()
    file_path = media_dir / filename
    
    # Security: prevent directory traversal
    if not file_path.resolve().is_relative_to(media_dir.resolve()):
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Delete physical file if it exists
    if file_path.exists() and file_path.is_file():
        try:
            file_path.unlink()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
    
    # Delete database record
    await db.delete(media)
    await db.commit()
