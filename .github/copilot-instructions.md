# Stream Companion - AI Agent Instructions

## Project Architecture

**Dashboard/Widget/Feature Model:**
- **Dashboard**: Organizational tab in admin UI (one active at a time, `is_active` flag)
- **Widget**: Reusable component instance with configuration (many-to-many with Dashboards)
- **Element**: Media asset owned by Widget (images, videos, audio, text)
- **Feature**: Executable action provided by Widget (decorated methods like `@feature`)

**Data Flow:** Dashboard ↔ Widget (shared state) → Element (owned assets) → Feature (actions)

## Database Patterns

**SQLAlchemy 2.0+ Async:**
```python
# Always use async session methods
async with AsyncSessionLocal() as session:
    result = await session.execute(select(Dashboard))
    dashboards = result.scalars().all()

# Use lazy="selectin" for relationships to avoid N+1 queries
widgets: Mapped[List["Widget"]] = relationship(
    "Widget",
    secondary="dashboard_widgets",
    back_populates="dashboards",
    lazy="selectin"
)

# Cascade delete for owned relationships
elements: Mapped[List["Element"]] = relationship(
    "Element",
    back_populates="widget",
    cascade="all, delete-orphan",
    lazy="selectin"
)
```

**Many-to-many:** Dashboard ↔ Widget via `dashboard_widgets` association table  
**One-to-many:** Widget → Element with cascade delete

## Key Conventions

**Models Location:** `app/models/` with declarative base in `base.py`  
**Pydantic Schemas:** Use `mode='json'` for datetime serialization in `model_config`  
**WebSocket Protocol:** Events like `element_update`, `dashboard_activated`, `dashboard_deactivated`  
**Media Storage:** `data/media/` (configurable via `settings.media_directory`)  
**Database:** SQLite at `data/stream_companion.db` (async with aiosqlite)

## Widget Development

**BaseWidget Structure (to be implemented):**
- Abstract class in `app/widgets/base.py`
- `@feature` decorator for executable actions
- `create_default_elements()` method
- `execute_feature(feature_name, params)` dispatcher

**Widget Instance:**
- `widget_class`: String name mapping to Python class
- `widget_parameters`: JSON field for configuration
- Owns Elements via `widget_id` foreign key

## Development Workflows

**Adding a Model:**
1. Create in `app/models/`
2. Add to `app/models/__init__.py`
3. Database recreates automatically on app startup (lifespan event)

**Testing Relationships:**
- Use async patterns: `widget.dashboards.append(dashboard)` then `session.add(widget)`
- Avoid greenlet errors by accessing relationships within async session context

**API Structure:**
- Media API: `app/api/media.py` (upload, list, serve, delete)
- WebSocket: `app/api/websocket.py` (overlay communication)
- **No Elements API** (Elements are managed through Widget API only)

## Important Notes

- **Encapsulation:** Elements are never exposed directly; always accessed through Widgets
- **Forward References:** Use `from __future__ import annotations` or `TYPE_CHECKING` imports
- **Async Everywhere:** All database operations are async (SQLAlchemy 2.0+)
- **Router Ordering:** Mount API routers BEFORE StaticFiles in `main.py`
- **Dependencies:** python-multipart required for file uploads

## File Structure

```
app/
  models/          # SQLAlchemy models (Dashboard, Widget, Element)
  schemas/         # Pydantic schemas for validation
  api/             # FastAPI routers (media, websocket)
  core/            # Config, database, WebSocket manager
  widgets/         # Widget classes (to be implemented)
data/
  media/           # User-uploaded media files
  stream_companion.db  # SQLite database
media/
  overlay.html     # Main overlay for OBS (1920x1080)
  js/              # Reusable components (MediaUploader, MediaLibrary)
```

## Next Implementation Steps

1. Fix forward reference in `app/models/element.py` (add annotations import)
2. Create `app/widgets/base.py` with BaseWidget class and @feature decorator
3. Implement example `ConfettiAlertWidget` as validation
4. Build Widget API endpoints (`/api/widgets/`, `/api/widget-types/`)
5. Create widget registry system for dynamic loading

---
*Reference: See README.md for complete architectural specification*
