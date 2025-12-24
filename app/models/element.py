"""Element database model"""

from __future__ import annotations  # Enable postponed evaluation of annotations

from typing import TYPE_CHECKING, List
from enum import Enum
from sqlalchemy import Boolean, Integer, String, ForeignKey, JSON, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.widget import Widget
    from app.models.element_asset import ElementAsset

from app.models.base import Base, TimestampMixin


class ElementType(str, Enum):
    """Type of overlay element"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    TIMER = "timer"
    COUNTER = "counter"
    ANIMATION = "animation"
    CANVAS = "canvas"  # HTML5 canvas for custom rendering (particles, effects, etc.)


class Element(Base, TimestampMixin):
    """
    Overlay element that can be displayed on stream.
    
    Elements are owned by Widgets. Each Element belongs to exactly one Widget.
    Widgets control their Elements by manipulating state (playing), properties, and behavior
    through Features executed by users or triggered by events.
    
    Animation Framework:
    - playing: bool - Controls animation execution. When True, element executes its behavior steps.
               When False, element is hidden and idle. Behavior steps (appear/disappear) control visibility.
    - behavior: list - Step-based animation sequence. Each step is a dict with type and parameters.
               Step types: appear, animate_property, animate, wait, set, disappear
    """
    
    __tablename__ = "elements"
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('widget_id', 'name', name='uq_widget_element_name'),
    )
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to Widget (each Element belongs to one Widget)
    widget_id: Mapped[int | None] = mapped_column(
        Integer, 
        ForeignKey("widgets.id", ondelete="CASCADE"), 
        nullable=True,  # Nullable for backward compatibility with orphaned elements
        index=True
    )
    
    # Basic properties
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    element_type: Mapped[ElementType] = mapped_column(SQLEnum(ElementType), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    
    # Element state
    playing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Display properties (stored as JSON for flexibility)
    # Examples: position, size, opacity, z-index, css properties, etc.
    properties: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Animation/behavior settings (stored as JSON array of steps)
    # Step-based animation: each step has type and parameters (appear, animate_property, animate, wait, set, disappear)
    behavior: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    
    # Relationships
    # Many-to-one with Widget (each Element belongs to one Widget)
    widget: Mapped["Widget"] = relationship(
        "Widget",
        back_populates="elements",
        lazy="selectin"
    )
    
    # Many-to-many with Media through ElementAsset junction table
    media_assets: Mapped[List["ElementAsset"]] = relationship(
        "ElementAsset",
        back_populates="element",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def get_media(self, role: str = "primary"):
        """Get media asset by role.
        
        Args:
            role: Asset role (default: "primary"). For multi-asset elements like cards,
                  use roles like "front_background", "back_content", etc.
        
        Returns:
            Media object if found, None otherwise
        """
        for asset in self.media_assets:
            if asset.role == role:
                return asset.media
        return None
    
    def get_media_url(self, role: str = "primary"):
        """Get URL for media asset by role.
        
        Args:
            role: Asset role (default: "primary")
        
        Returns:
            URL path (e.g., "/uploads/image.png") if media found, None otherwise
        """
        media = self.get_media(role)
        if media:
            return f"/uploads/{media.filename}"
        return None
    
    def __repr__(self) -> str:
        return f"<Element(id={self.id}, name='{self.name}', type={self.element_type}, widget_id={self.widget_id})>"
