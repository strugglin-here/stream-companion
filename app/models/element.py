"""Element database model"""

from sqlalchemy import String, Integer, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum

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
    
    Elements are individual components (images, videos, text, etc.) that can be
    combined into Compositions. The compositions control the elements on behalf of the user
    by exposing standard controls via their associated ControlPanel, as well as through 
    API/chat commands.
    """
    
    __tablename__ = "elements"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Basic properties
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
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
    
    def __repr__(self) -> str:
        return f"<Element(id={self.id}, name='{self.name}', type={self.element_type})>"
