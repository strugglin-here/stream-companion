"""Repository layer for data access.

Repositories provide pure data access operations with automatic eager loading
of relationships. They handle entity-level validation (like role validation)
but do NOT contain business logic or commit transactions.

Philosophy:
- Repositories return ORM objects (not dicts)
- Always eager load relationships (RAM over latency)
- Validate entity constraints (role existence checks)
- Caller controls transaction commits
- Used by service layer and API endpoints
- Widgets use direct ORM for element creation (widget-first design)
"""

from app.repositories.element_repository import ElementRepository
from app.repositories.widget_repository import WidgetRepository
from app.repositories.media_repository import MediaRepository

__all__ = [
    "ElementRepository",
    "WidgetRepository", 
    "MediaRepository",
]
