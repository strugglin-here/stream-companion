"""Element database model"""

from __future__ import annotations  # Enable postponed evaluation of annotations

from typing import TYPE_CHECKING
from enum import Enum
from sqlalchemy import Boolean, Integer, String, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.widget import Widget

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


class Element(Base, TimestampMixin):
    """
    Overlay element that can be displayed on stream.
    
    Elements are owned by Widgets. Each Element belongs to exactly one Widget.
    Widgets control their Elements by manipulating visibility, properties, and behavior
    through Features executed by users or triggered by events.
    """
    
    __tablename__ = "elements"
    
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
    
    # File/Asset reference (for image/video/audio types)
    asset_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Element state
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    visible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Display properties (stored as JSON for flexibility)
    # Examples: position, size, opacity, z-index, css properties, etc.
    properties: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Animation/behavior settings (stored as JSON)
    # Examples: entrance animation, exit animation, loop settings, triggers
    behavior: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Relationships
    # Many-to-one with Widget (each Element belongs to one Widget)
    widget: Mapped["Widget"] = relationship(
        "Widget",
        back_populates="elements",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Element(id={self.id}, name='{self.name}', type={self.element_type}, widget_id={self.widget_id})>"
