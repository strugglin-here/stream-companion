"""Media file model"""

from __future__ import annotations

from typing import TYPE_CHECKING, List
from sqlalchemy import String, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.element_asset import ElementAsset

from app.models.base import Base, TimestampMixin


class Media(Base, TimestampMixin):
    """Media file stored in the upload directory.
    
    Tracks metadata for uploaded media files (images, videos, audio).
    The actual file is stored in the filesystem at settings.upload_directory.
    """
    __tablename__ = "media"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Filename in the upload directory (unique)
    filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    
    # MIME type (e.g., 'image/png', 'video/mp4', 'audio/mp3')
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # File size in bytes
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Original filename when uploaded (may differ from stored filename due to deduplication)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('filename', name='uq_media_filename'),
    )
    
    # Relationships
    # Many-to-many with Elements through ElementAsset junction table
    element_usages: Mapped[List["ElementAsset"]] = relationship(
        "ElementAsset",
        back_populates="media",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Media(id={self.id}, filename='{self.filename}', type='{self.mime_type}')>"
