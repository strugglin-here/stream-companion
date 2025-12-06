# Stream Companion - AI Agent Instructions

## Project Architecture

**Dashboard/Widget/Feature Model:**
- **Dashboard**: Organizational tab in admin UI (one active at a time, `is_active` flag)
- **Widget**: Reusable component instance with configuration (many-to-many with Dashboards)
  - Single widget instance can exist on multiple dashboards
  - Shared state across dashboards (not duplicated per dashboard)
- **Element**: Media asset owned by Widget (images, videos, audio, text, canvas)
- **Feature**: Executable action provided by Widget (decorated methods like `@feature`)

**Data Flow:** Dashboard ↔ Widget (shared state) → Element (owned assets) → Feature (actions)

**Widget Instance Sharing:**
- "Add Existing" workflow: Select from available widget instances not on current dashboard
- "Create New" workflow: Create widget instance AND add to current dashboard
- Removing widget from dashboard doesn't delete it, just removes the association

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
**Media Storage:**
  - Static files (HTML, JS, CSS): `./media/` served at `/media`
  - User uploads: `./data/media/` served at `/uploads`
**Database:** SQLite at `data/stream_companion.db` (async with aiosqlite)

## Widget Development

**BaseWidget Structure:**
- Abstract class in `app/widgets/base.py`
- `@feature` decorator for executable actions
- `create_default_elements()` method (imperative pattern)
- `execute_feature(feature_name, params)` dispatcher
- `get_features()` class method returns feature metadata

**Element Creation (Imperative Pattern):**
- Widgets implement `create_default_elements()` method
- Elements created manually with full control over properties
- Elements stored in `self.elements` dict (keyed by element name)
- Called automatically during `BaseWidget.create()`

Example:
```python
async def create_default_elements(self):
    canvas = Element(
        widget_id=self.db_widget.id,
        name="confetti_canvas",
        element_type=ElementType.CANVAS,
        properties={"width": 1920, "height": 1080},
        behavior={"animation": "particles"}
    )
    self.db.add(canvas)
    await self.db.flush()
    self.elements["confetti_canvas"] = canvas
```

**Element Updates and Broadcasting:**
- Widget features update element properties directly via `self.elements[name]`
- Use manual broadcasting: features call `broadcast_element_update()` when ready
- Supports batch updates: modify multiple elements, then broadcast once
- Pattern: Update → Flush to DB → Broadcast to overlay

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
- Dashboard API: `app/api/dashboards.py` (CRUD, activation, widget association)
- Widget API: `app/api/widgets.py` (types, CRUD, feature execution)
- Media API: `app/api/media.py` (upload, list, serve, delete)
- WebSocket: `app/api/websocket.py` (overlay communication)
- **No Elements API** (Elements are managed through Widget methods only)

## Important Notes

- **Encapsulation:** Elements are never exposed directly; always accessed through Widgets
- **Element Management:** Elements are NEVER exposed via direct API endpoints. All element 
  manipulation happens through Widget methods and features. This maintains proper encapsulation 
  and prevents state corruption.
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
  widgets/         # Widget classes (BaseWidget, ConfettiAlertWidget)
data/
  media/           # User-uploaded media files (served at /uploads)
  stream_companion.db  # SQLite database
media/
  overlay.html     # Main overlay for OBS (1920x1080)
  admin/           # Admin UI (Vue 3 SPA)
  js/              # Reusable components
```

## Next Implementation Steps

1. Implement `create_default_elements()` in `ConfettiAlertWidget`
2. Update `BaseWidget.create()` to call `create_default_elements()`
3. Add element update methods to widget features
4. Implement overlay rendering for confetti elements
5. Build additional widget types (alerts, timers, etc.)

---
*Reference: See README.md for complete architectural specification*
