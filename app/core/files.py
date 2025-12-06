"""Shared file handling utilities for media uploads"""

from pathlib import Path
from typing import Optional
from fastapi import HTTPException, UploadFile


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


def validate_file_extension(filename: str) -> str:
    """
    Validate file extension.
    
    Args:
        filename: The filename to validate
        
    Returns:
        The file extension (lowercase)
        
    Raises:
        HTTPException: If the file extension is not allowed
    """
    file_ext = Path(filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        allowed = ', '.join(ALLOWED_EXTENSIONS.keys())
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Supported types: {allowed}"
        )
    return file_ext


def validate_file_size(size: Optional[int]) -> None:
    """
    Validate file size.
    
    Args:
        size: File size in bytes (if available)
        
    Raises:
        HTTPException: If the file is too large
    """
    if size and size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )


def get_unique_filepath(media_dir: Path, filename: str) -> Path:
    """
    Get a unique filepath by appending a counter if the file already exists.
    
    Args:
        media_dir: The media directory path
        filename: The desired filename
        
    Returns:
        A unique Path object that doesn't exist yet
    """
    file_ext = Path(filename).suffix.lower()
    base_name = Path(filename).stem
    target_path = media_dir / filename
    counter = 1
    
    while target_path.exists():
        new_name = f"{base_name}_{counter}{file_ext}"
        target_path = media_dir / new_name
        counter += 1
    
    return target_path


async def save_upload_file(
    file: UploadFile,
    target_path: Path,
    chunk_size: int = 1024 * 1024  # 1MB chunks
) -> None:
    """
    Save an uploaded file to disk with chunked reading for large files.
    
    Args:
        file: The UploadFile object to save
        target_path: The destination path
        chunk_size: Size of chunks to read (default 1MB)
        
    Raises:
        HTTPException: If the file exceeds MAX_FILE_SIZE or save fails
    """
    try:
        with target_path.open('wb') as f:
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
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Clean up on error
        if target_path.exists():
            target_path.unlink()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
