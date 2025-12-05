"""Dashboard database model"""

from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Dashboard(Base, TimestampMixin):
    """
    Dashboard represents a tab in the admin interface that groups related Widgets.
    
    Dashboards organize widgets for different stream scenes (e.g., "Starting Soon",
    "Main Stream", "Break Screen"). Only one Dashboard can be active at a time.
    """
    
    __tablename__ = "dashboards"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Basic properties
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    
    # Active state - only one dashboard can be active at a time
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    
    # Relationships
    # Many-to-many with Widget through association table
    widgets: Mapped[list["Widget"]] = relationship(
        "Widget",
        secondary="dashboard_widgets",
        back_populates="dashboards",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Dashboard(id={self.id}, name='{self.name}', active={self.is_active})>"
