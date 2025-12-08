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

**Widget-First Programming Philosophy:**
Widgets are the primary extension point for adding functionality to Stream Companion.
By defining elements directly in widget classes, developers can focus solely on widget
development to expand the program's capabilities. Widgets use direct ORM access for
element creation - they own their element lifecycle and schemas.

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

# CRITICAL: Eager load nested relationships when serializing
# Elements have media_assets -> each asset has media
# ALWAYS use explicit selectinload for elements returned in API responses:
from sqlalchemy.orm import selectinload
result = await db.execute(
    select(Element)
    .options(selectinload(Element.media_assets).selectinload(ElementAsset.media))
    .where(Element.widget_id == widget_id)
)
elements = result.scalars().all()
# This prevents "greenlet_spawn" errors when accessing relationships outside session context
```

**Many-to-many:** Dashboard ↔ Widget via `dashboard_widgets` association table  
**One-to-many:** Widget → Element with cascade delete  
**Eager Loading Philosophy:** Proactively load all relationships for snappy interfaces (RAM over latency)

## Key Conventions

**Models Location:** `app/models/` with declarative base in `base.py`  
**Repositories:** `app/repositories/` - Pure data access with automatic eager loading  
**Services:** `app/services/` - Business logic orchestration (does NOT commit transactions)  
**Pydantic Schemas:** Use `datetime` type for timestamp fields. FastAPI automatically serializes datetime objects to ISO 8601 strings in JSON responses. Use `model_config = {"from_attributes": True}` for ORM object mapping.  
**Media Asset Pattern:** 
  - Elements use `media_assets` relationship (many-to-many via `element_assets` table)
  - Each asset has a `role` (e.g., "image", "sound") defined in element's `properties["media_roles"]`
  - Database stores: Media filename in `media` table, role in `element_assets` table
  - API returns: `media_assets` (media_id + role) and `media_details` (full media info with URL)
  - URL conversion: Direct f-string formatting `f"/uploads/{filename}"`
**Serialization:** Centralized in `app/api/serializers.py` - single source of truth for Element→dict conversion, used by API and WebSocket  
**WebSocket Protocol:** Events like `element_update`, `dashboard_activated`, `dashboard_deactivated`  
**Static File Mounts:**
  - Admin UI: `frontend/admin/` served at `/admin` (html=True for SPA routing)
  - Overlay UI: `frontend/overlay/` served at `/overlay` (html=True for SPA routing)
  - Shared components: `frontend/shared/` served at `/shared`
  - User uploads: Configured via `settings.upload_directory` (default: `./data/media/`), served at `/uploads`
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
- **DO NOT call `commit()` or `flush()` in `create_default_elements()`** - parent handles transaction

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
    # DO NOT call flush/commit - parent BaseWidget.create() handles it
    self.elements["confetti_canvas"] = canvas
```

**Element Access and Validation:**
- Use `self.get_element(name, validate_asset=True/False)` to retrieve elements
- Automatically validates element existence (raises ValueError if not found)
- `validate_asset` parameter is legacy and no longer performs validation (media validated at assignment time)
- Never use `self.elements.get()` directly - always use `get_element()`
- **Element names are immutable** - set once during `create_default_elements()`, never changed
- Database enforces uniqueness via `UniqueConstraint('widget_id', 'name')`

Example:
```python
async def trigger_blast(self, intensity: str):
    # Get element with automatic existence validation
    confetti = self.get_element("confetti_particle")
    sound = self.get_element("pop_sound")
    
    confetti.visible = True
    # ... modify properties
```

**Element Updates and Broadcasting:**
- Widget features update element properties directly via element objects
- **CRITICAL PATTERN: Commit BEFORE broadcasting** to prevent race conditions
- Pattern: **Update → Commit to DB → Broadcast to overlay**
- WebSocket broadcasts include `element_id` separately for delete actions

Example:
```python
async def my_feature(self):
    element = self.get_element("my_element")
    element.visible = True
    element.properties["color"] = "#FF0000"
    
    # Commit FIRST to ensure database consistency
    await self.db.commit()
    
    # Broadcast AFTER commit
    await self.broadcast_element_update(element, action="show")

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
- Repositories: `app/repositories/` (data access with eager loading)
  - `element_repository.py` - Element queries with automatic media loading
  - `widget_repository.py` - Widget queries
  - `media_repository.py` - Media queries
- Services: `app/services/` (business logic, does NOT commit)
  - `element_service.py` - Media assignment, validation (used by API & widgets)
- Serializers: `app/api/serializers.py` (centralized ORM→dict conversion, used by API & WebSocket)
- WebSocket: `app/api/websocket.py` (overlay communication)
- **No Elements API** (Elements are managed through Widget methods only)

## Important Notes

- **Widget-First Development:** Widgets are the primary programming interface for extending functionality.
  Developers should focus on creating widgets to add features. Widgets use direct ORM for element
  creation in `create_default_elements()` - they own the element lifecycle and schemas.
- **Repository Pattern:** Use repositories for querying elements (automatic eager loading). Widgets
  can still use direct ORM for element creation. API endpoints use repositories + services.
- **Service Layer:** Services contain business logic (like media assignment with validation) but
  do NOT commit transactions. Used by both API endpoints and widget methods for unified code paths.
- **Encapsulation:** Elements are never exposed directly; always accessed through Widgets
- **Element Management:** Elements are NEVER exposed via direct API endpoints. All element 
  manipulation happens through Widget methods and features. This maintains proper encapsulation 
  and prevents state corruption.
- **Element Name Immutability:** Element names are set during widget creation and CANNOT be changed
  - Widget features rely on stable element names (e.g., `get_element("confetti_particle")`)
  - Database enforces `UniqueConstraint('widget_id', 'name')`
  - `ElementUpdate` schema excludes `name` field
  - Admin UI displays element name as read-only (modal header only)
- **Transaction Safety:** Caller controls commits. ALWAYS commit before broadcasting WebSocket events to prevent race conditions
- **Element Retrieval:** Use `get_element(name)` in widgets (validate_asset param is legacy)
- **JSON Mutation Tracking:** SQLAlchemy 2.0+ tracks JSON column mutations automatically - no need for `flag_modified()`
- **Forward References:** Use `from __future__ import annotations` or `TYPE_CHECKING` imports
- **Async Everywhere:** All database operations are async (SQLAlchemy 2.0+)
- **Router Ordering:** Mount API routers BEFORE StaticFiles in `main.py`
- **Dependencies:** python-multipart required for file uploads
- **Type Hints:** Use `Optional[Type]` for parameters that can be `None`

## File Structure

```
app/
  models/          # SQLAlchemy models (Dashboard, Widget, Element)
  repositories/    # Data access layer with eager loading
    element_repository.py  # Element queries (auto-loads media)
    widget_repository.py   # Widget queries
    media_repository.py    # Media queries
  services/        # Business logic (does NOT commit)
    element_service.py     # Media assignment, validation
  schemas/         # Pydantic schemas for validation
  api/             # FastAPI routers
    dashboards.py  # Dashboard CRUD and management
    widgets.py     # Widget CRUD and feature execution
    media.py       # Media upload, list, serve, delete
    serializers.py # Centralized ORM→dict conversion (used by API & WebSocket)
    websocket.py   # WebSocket overlay communication
  core/            # Config, database, WebSocket manager, file utilities
    config.py      # Pydantic settings (host, port, database_url, etc.)
    database.py    # SQLAlchemy async session management
    websocket.py   # WebSocket connection manager singleton
    files.py       # Shared file upload/validation utilities
  widgets/         # Widget classes (BaseWidget, AlertWidget)
data/
  media/           # User-uploaded media files (served at /uploads)
  stream_companion.db  # SQLite database
frontend/
  admin/           # Admin UI (Vue 3 SPA) served at /admin
  overlay/         # Overlay UI (HTML/JS) served at /overlay
  shared/          # Shared frontend components served at /shared
```

*Reference: See README.md for complete architectural specification*