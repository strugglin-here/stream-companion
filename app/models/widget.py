"""Widget database model"""

from sqlalchemy import String, Integer, JSON, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


# Association table for many-to-many relationship between Dashboard and Widget
dashboard_widgets = Table(
    "dashboard_widgets",
    Base.metadata,
    Column("dashboard_id", Integer, ForeignKey("dashboards.id", ondelete="CASCADE"), primary_key=True),
    Column("widget_id", Integer, ForeignKey("widgets.id", ondelete="CASCADE"), primary_key=True),
)


class Widget(Base, TimestampMixin):
    """
    Widget represents an instantiated widget with its configuration.
    
    Widgets are reusable components that own Elements and provide Features.
    The same Widget instance can appear on multiple Dashboards (shared state).
    Each Widget instance has a widget_class (e.g., "ConfettiAlertWidget") that
    determines its behavior, and widget_parameters that configure its operation.
    """
    
    __tablename__ = "widgets"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Widget class identifier (maps to Python class)
    widget_class: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # User-given name for this widget instance
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Widget configuration stored as JSON
    # Examples: {blast_duration: 2.5, particle_count: 100, default_color: "#FF5733"}
    widget_parameters: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Relationships
    # Many-to-many with Dashboard through association table
    dashboards: Mapped[list["Dashboard"]] = relationship(
        "Dashboard",
        secondary="dashboard_widgets",
        back_populates="widgets",
        lazy="selectin"
    )
    
    # One-to-many with Element (Widget owns Elements)
    elements: Mapped[list["Element"]] = relationship(
        "Element",
        back_populates="widget",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Widget(id={self.id}, class='{self.widget_class}', name='{self.name}')>"
