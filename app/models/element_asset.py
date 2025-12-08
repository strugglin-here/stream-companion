"""ElementAsset junction table - Many-to-many relationship between Elements and Media"""

from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.element import Element
    from app.models.media import Media

from app.models.base import Base


class ElementAsset(Base):
    """
    Junction table linking Elements to Media assets.
    
    Enables elements to reference multiple media files with semantic roles:
    - Single-asset elements: role="primary" (images, videos, audio)
    - Multi-asset elements: role="front_background", "back_content", etc. (cards)
    
    The relationship is many-to-many:
    - One element can reference multiple media files (e.g., card with front/back images)
    - One media file can be used by multiple elements (e.g., shared logo across widgets)
    """
    __tablename__ = "element_assets"
    
    # Table constraints
    __table_args__ = (
        # Ensure each element can only have one asset per role
        UniqueConstraint('element_id', 'role', name='uq_element_role'),
    )
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    element_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("elements.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    media_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("media.id", ondelete="RESTRICT"),  # Prevent deleting media still in use
        nullable=False,
        index=True
    )
    
    # Asset role within the element (e.g., "primary", "background", "front_content", "back_background")
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="primary")
    
    # Relationships
    element: Mapped["Element"] = relationship(
        "Element",
        back_populates="media_assets",
        lazy="selectin"
    )
    
    media: Mapped["Media"] = relationship(
        "Media",
        back_populates="element_usages",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<ElementAsset(element_id={self.element_id}, media_id={self.media_id}, role='{self.role}')>"
