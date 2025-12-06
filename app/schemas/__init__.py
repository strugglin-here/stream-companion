"""Pydantic schemas for request/response validation"""

from app.schemas.dashboard import (
    DashboardCreate,
    DashboardUpdate,
    DashboardResponse,
    DashboardList,
    WidgetSummary
)
from app.schemas.widget import (
    WidgetCreate,
    WidgetUpdate,
    WidgetResponse,
    WidgetTypeResponse,
    WidgetTypeList,
    ElementResponse,
    FeatureResponse,
    FeatureExecute
)
from app.schemas.element import (
    ElementBase,
    ElementCreate,
    ElementUpdate,
    ElementResponse as ElementDetailResponse,
    ElementList
)
from app.schemas.media import (
    MediaItem,
    MediaList
)

__all__ = [
    # Dashboard schemas
    "DashboardCreate",
    "DashboardUpdate",
    "DashboardResponse",
    "DashboardList",
    "WidgetSummary",
    # Widget schemas
    "WidgetCreate",
    "WidgetUpdate",
    "WidgetResponse",
    "WidgetTypeResponse",
    "WidgetTypeList",
    "ElementResponse",
    "FeatureResponse",
    "FeatureExecute",
    # Element schemas
    "ElementBase",
    "ElementCreate",
    "ElementUpdate",
    "ElementDetailResponse",
    "ElementList",
    # Media schemas
    "MediaItem",
    "MediaList",
]

__all__ = [
    "ElementBase",
    "ElementCreate",
    "ElementUpdate",
    "ElementResponse",
    "ElementList",
]
