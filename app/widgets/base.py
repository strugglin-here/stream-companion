"""Base Widget class and feature decorator"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional
from functools import wraps
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.widget import Widget
from app.models.element import Element
from app.core.websocket import manager


# Feature metadata storage
FEATURE_METADATA_ATTR = "_feature_metadata"


def feature(
    display_name: str,
    description: str = "",
    parameters: Optional[List[Dict[str, Any]]] = None
):
    """
    Decorator to mark a widget method as an executable feature.
    
    Args:
        display_name: Human-readable name shown in UI
        description: Optional description of what the feature does
        parameters: List of parameter definitions for the feature
            Each parameter dict should have:
            - name: str - Parameter identifier
            - type: str - Input type (dropdown, text, color-picker, number, checkbox, multiselect)
            - label: str - Display label (defaults to name)
            - optional: bool - Whether parameter is optional (default False)
            - default: Any - Default value if optional
            - options: List[str] - For dropdown/multiselect types
            - min/max: int/float - For number type
            - placeholder: str - For text inputs
    
    Example:
        @feature(
            display_name="Trigger Confetti Blast",
            description="Launch confetti particles with customizable settings",
            parameters=[
                {
                    "name": "intensity",
                    "type": "dropdown",
                    "label": "Intensity Level",
                    "options": ["Low", "Medium", "High"],
                    "optional": False
                },
                {
                    "name": "color",
                    "type": "color-picker",
                    "label": "Confetti Color",
                    "optional": True,
                    "default": "#FF5733"
                }
            ]
        )
        async def trigger_blast(self, intensity: str, color: str = "#FF5733"):
            # Implementation here
            pass
    """
    def decorator(func: Callable) -> Callable:
        # Store metadata on the function
        metadata = {
            "method_name": func.__name__,
            "display_name": display_name,
            "description": description,
            "parameters": parameters or []
        }
        setattr(func, FEATURE_METADATA_ATTR, metadata)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


class BaseWidget(ABC):
    """
    Abstract base class for all widget types.
    
    Widgets are reusable components that:
    - Own Elements (media assets, display components)
    - Provide Features (executable actions)
    - Maintain configuration via widget_parameters
    - Can appear on multiple Dashboards (shared state)
    
    Subclasses must:
    1. Set class-level metadata (widget_class, display_name, description)
    2. Implement create_default_elements() to create owned Elements
    3. Implement get_default_parameters() to define default configuration
    4. Define features using @feature decorator
    """
    
    # Class metadata (must be overridden by subclasses)
    widget_class: str = ""  # Unique identifier, e.g., "ConfettiAlertWidget"
    display_name: str = ""  # Human-readable name
    description: str = ""   # Description for widget library
    
    def __init__(self, db: AsyncSession, db_widget: Widget):
        """
        Initialize widget instance.
        
        Args:
            db: Async database session
            db_widget: Database Widget record
        """
        self.db = db
        self.db_widget = db_widget
        self.widget_parameters = db_widget.widget_parameters or {}
        self.elements: Dict[str, Element] = {}  # Element name -> Element instance
    
    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        name: str,
        widget_parameters: Optional[Dict[str, Any]] = None,
        dashboard_ids: Optional[List[int]] = None
    ) -> 'BaseWidget':
        """
        Create a new widget instance with default elements.
        
        Args:
            db: Async database session
            name: User-given name for this widget instance
            widget_parameters: Optional configuration (uses defaults if not provided)
            dashboard_ids: Optional list of dashboard IDs to add widget to
        
        Returns:
            Initialized widget instance
        """
        # Merge provided parameters with defaults
        params = cls.get_default_parameters()
        if widget_parameters:
            params.update(widget_parameters)
        
        # Create database record
        from app.models.dashboard import Dashboard
        
        db_widget = Widget(
            widget_class=cls.widget_class,
            name=name,
            widget_parameters=params
        )
        
        # Add to dashboards if specified
        if dashboard_ids:
            from sqlalchemy import select
            result = await db.execute(
                select(Dashboard).where(Dashboard.id.in_(dashboard_ids))
            )
            dashboards = result.scalars().all()
            db_widget.dashboards.extend(dashboards)
        
        db.add(db_widget)
        await db.commit()
        await db.refresh(db_widget)
        
        # Create widget instance
        instance = cls(db, db_widget)
        
        # Create default elements
        await instance.create_default_elements()
        
        # Load elements into memory
        await instance.load_elements()
        
        return instance
    
    @classmethod
    async def load(cls, db: AsyncSession, widget_id: int) -> 'BaseWidget':
        """
        Load existing widget from database.
        
        Args:
            db: Async database session
            widget_id: Widget ID to load
        
        Returns:
            Initialized widget instance
        """
        from sqlalchemy import select
        
        result = await db.execute(
            select(Widget).where(Widget.id == widget_id)
        )
        db_widget = result.scalar_one()
        
        instance = cls(db, db_widget)
        await instance.load_elements()
        
        return instance
    
    async def load_elements(self):
        """Load widget's elements from database into memory."""
        from sqlalchemy import select
        
        result = await self.db.execute(
            select(Element).where(Element.widget_id == self.db_widget.id)
        )
        elements = result.scalars().all()
        
        self.elements = {elem.name: elem for elem in elements}
    
    @classmethod
    @abstractmethod
    def get_default_parameters(cls) -> Dict[str, Any]:
        """
        Return default widget parameters.
        
        These are configuration values that affect widget behavior across
        all features (e.g., animation durations, default colors, particle counts).
        
        Returns:
            Dictionary of parameter name -> default value
        
        Example:
            {
                "blast_duration": 2.5,
                "particle_count": 100,
                "default_color": "#FF5733"
            }
        """
        pass
    
    @abstractmethod
    async def create_default_elements(self):
        """
        Create default elements for this widget.
        
        Subclasses should create Element instances with sensible defaults.
        Elements should be added to the database session but not committed
        (the create() method handles the commit).
        
        Example:
            element = Element(
                widget_id=self.db_widget.id,
                element_type=ElementType.IMAGE,
                name="confetti_particle",
                asset_path=None,  # User will configure later
                properties={
                    "position": {"x": 960, "y": 540, "z_index": 100},
                    "size": {"width": 50, "height": 50},
                    "opacity": 1.0
                },
                behavior={
                    "entrance": {"type": "explosion", "duration": 2.5},
                    "exit": {"type": "fade", "duration": 0.5}
                },
                enabled=True,
                visible=False
            )
            self.db.add(element)
        """
        pass
    
    @classmethod
    def get_features(cls) -> List[Dict[str, Any]]:
        """
        Extract feature metadata from decorated methods.
        
        Returns:
            List of feature definitions with metadata
        
        Example:
            [
                {
                    "method_name": "trigger_blast",
                    "display_name": "Trigger Confetti Blast",
                    "description": "Launch confetti particles",
                    "parameters": [...]
                }
            ]
        """
        features = []
        
        # Iterate through class methods
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            
            # Check if method has feature metadata
            if hasattr(attr, FEATURE_METADATA_ATTR):
                metadata = getattr(attr, FEATURE_METADATA_ATTR)
                features.append(metadata)
        
        return features
    
    async def execute_feature(
        self,
        feature_name: str,
        feature_params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute a named feature with parameters.
        
        Args:
            feature_name: Method name of the feature to execute
            feature_params: Dictionary of parameter name -> value
        
        Returns:
            Result from feature method (if any)
        
        Raises:
            ValueError: If feature doesn't exist or parameters are invalid
        """
        # Check if feature exists
        if not hasattr(self, feature_name):
            raise ValueError(f"Feature '{feature_name}' not found on {self.widget_class}")
        
        method = getattr(self, feature_name)
        
        # Verify it's actually a feature
        if not hasattr(method, FEATURE_METADATA_ATTR):
            raise ValueError(f"Method '{feature_name}' is not a feature")
        
        # Execute with provided parameters
        params = feature_params or {}
        result = await method(**params)
        
        return result
    
    async def broadcast_element_update(
        self,
        element: Element,
        action: str = "update"
    ):
        """
        Broadcast element update via WebSocket.
        
        Args:
            element: Element that was updated
            action: Type of update (update, show, hide, delete)
        """
        await manager.broadcast_element_update(element, action)
    
    async def update_parameters(self, new_parameters: Dict[str, Any]):
        """
        Update widget parameters.
        
        Args:
            new_parameters: New parameter values (merged with existing)
        """
        self.widget_parameters.update(new_parameters)
        self.db_widget.widget_parameters = self.widget_parameters
        await self.db.commit()
        await self.db.refresh(self.db_widget)
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.db_widget.id}, name='{self.db_widget.name}')>"
