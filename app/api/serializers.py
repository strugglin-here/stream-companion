"""Serialization helpers for API endpoints.

Centralize conversion from ORM objects to response dicts used by FastAPI
endpoints. These helpers return plain Python dicts compatible with the
Pydantic response models declared on the routes.
"""
from typing import Any, Dict, Iterable, List, Optional
from datetime import datetime

from app.models.element import Element
from app.models.widget import Widget


def _elem_type_to_str(element: Element) -> str:
    et = getattr(element, "element_type", None)
    if et is None:
        return ""
    if hasattr(et, "value"):
        return et.value
    return str(et)


def serialize_element_for_widget(element: Element) -> Dict[str, Any]:
    """Serialize an Element for inclusion inside a WidgetResponse.

    This returns the fields expected by `app.schemas.widget.ElementResponse`.
    """
    return {
        "id": element.id,
        "element_type": _elem_type_to_str(element),
        "name": element.name,
        "asset_path": element.asset_path,
        "properties": element.properties,
        "behavior": element.behavior,
        "enabled": element.enabled,
        "visible": element.visible,
    }


def serialize_element_detail(element: Element) -> Dict[str, Any]:
    """Serialize an Element for detailed element responses.

    This keeps datetime objects for created_at/updated_at because the
    ElementResponse in `app.schemas.element` expects datetimes.
    """
    return {
        "id": element.id,
        "name": element.name,
        "element_type": _elem_type_to_str(element),
        "description": element.description,
        "asset_path": element.asset_path,
        "enabled": element.enabled,
        "visible": element.visible,
        "properties": element.properties,
        "behavior": element.behavior,
        "created_at": element.created_at,
        "updated_at": element.updated_at,
    }


def serialize_widget_response(
    db_widget: Widget,
    elements: Optional[Iterable[Element]] = None,
    features: Optional[Iterable[Dict[str, Any]]] = None,
    dashboard_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """Serialize a Widget DB object into the shape expected by
    `app.schemas.widget.WidgetResponse`.

    - `elements` may be provided as an iterable of Element objects. If omitted
      the serializer will use db_widget.elements (which requires the
      relationship to be loaded).
    - `features` is expected to be the list returned by a widget class's
      `get_features()` method (a list of metadata dicts).
    """
    elems = elements if elements is not None else getattr(db_widget, "elements", [])

    return {
        "id": db_widget.id,
        "widget_class": db_widget.widget_class,
        "name": db_widget.name,
        "widget_parameters": db_widget.widget_parameters or {},
    "created_at": db_widget.created_at,
    "updated_at": db_widget.updated_at,
        "elements": [serialize_element_for_widget(e) for e in elems],
        "features": list(features) if features is not None else [],
        "dashboard_ids": dashboard_ids or [d.id for d in getattr(db_widget, "dashboards", [])],
    }


def serialize_widget_type(widget_cls: Any) -> Dict[str, Any]:
    """Serialize widget class metadata for the widget types endpoint."""
    return {
        "widget_class": widget_cls.widget_class,
        "display_name": getattr(widget_cls, "display_name", ""),
        "description": getattr(widget_cls, "description", ""),
        "default_parameters": widget_cls.get_default_parameters(),
        "features": widget_cls.get_features(),
    }


def serialize_dashboard(dashboard: Any) -> Dict[str, Any]:
    """Serialize a Dashboard model into the shape expected by
    `app.schemas.dashboard.DashboardResponse`.
    """
    widgets = getattr(dashboard, "widgets", []) or []

    return {
        "id": dashboard.id,
        "name": dashboard.name,
        "description": dashboard.description,
        "is_active": dashboard.is_active,
    "created_at": dashboard.created_at,
    "updated_at": dashboard.updated_at,
        "widgets": [
            {"id": w.id, "widget_class": w.widget_class, "name": w.name}
            for w in widgets
        ],
    }
