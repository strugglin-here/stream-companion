"""Widget registry and initialization"""

from typing import Dict, Type, Optional
from app.widgets.base import BaseWidget


# Global widget registry: widget_class -> Widget class
WIDGET_REGISTRY: Dict[str, Type[BaseWidget]] = {}


def register_widget(widget_cls: Type[BaseWidget]) -> Type[BaseWidget]:
    """
    Decorator to register a widget class in the global registry.
    
    Usage:
        @register_widget
        class MyWidget(BaseWidget):
            widget_class = "MyWidget"
            ...
    
    Args:
        widget_cls: Widget class to register
    
    Returns:
        The same class (unmodified)
    
    Raises:
        ValueError: If widget_class is empty or already registered
    """
    if not widget_cls.widget_class:
        raise ValueError(
            f"Widget class {widget_cls.__name__} must define 'widget_class' attribute"
        )
    
    if widget_cls.widget_class in WIDGET_REGISTRY:
        existing = WIDGET_REGISTRY[widget_cls.widget_class]
        raise ValueError(
            f"Widget class '{widget_cls.widget_class}' is already registered "
            f"by {existing.__name__}"
        )
    
    WIDGET_REGISTRY[widget_cls.widget_class] = widget_cls
    print(f"[OK] Registered widget: {widget_cls.widget_class} ({widget_cls.display_name})")
    
    return widget_cls


def get_widget_class(widget_class_name: str) -> Optional[Type[BaseWidget]]:
    """
    Get a widget class by its widget_class identifier.
    
    Args:
        widget_class_name: The widget_class string (e.g., "ConfettiAlertWidget")
    
    Returns:
        Widget class or None if not found
    """
    return WIDGET_REGISTRY.get(widget_class_name)


def list_widget_types() -> list[dict]:
    """
    Get list of all registered widget types with metadata.
    
    Returns:
        List of widget type definitions:
        [
            {
                "widget_class": "ConfettiAlertWidget",
                "display_name": "Confetti Alert",
                "description": "Celebratory particle explosion",
                "default_parameters": {...},
                "features": [...]
            }
        ]
    """
    widget_types = []
    
    for widget_class_name, widget_cls in WIDGET_REGISTRY.items():
        widget_types.append({
            "widget_class": widget_class_name,
            "display_name": widget_cls.display_name,
            "description": widget_cls.description,
            "default_parameters": widget_cls.get_default_parameters(),
            "features": widget_cls.get_features()
        })
    
    return widget_types


# Import all widget modules here to trigger registration
# This ensures widgets are registered when the app starts

from app.widgets.confetti_alert import ConfettiAlertWidget

# Add more widgets as they are created:
# from app.widgets.donation_goal import DonationGoalWidget
