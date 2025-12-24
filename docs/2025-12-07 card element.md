# Card Element Feature Development - 2025-12-07

## Phase 1: Media Model Migration ✅ COMPLETE

Before implementing the card element with multiple assets (front/back backgrounds and content), we migrated the media system from filesystem-only to a database-backed approach.

### Media Model Implementation

**New Media Model (`app/models/media.py`):**
- `id`: Primary key
- `filename`: Stored filename (unique, indexed)
- `original_filename`: Original upload name
- `mime_type`: File MIME type
- `file_size`: Size in bytes
- `created_at`, `updated_at`: Timestamps from TimestampMixin
- `element_usages`: Relationship to ElementAsset

**Updated API (`app/api/media.py`):**
- Upload endpoints now create database records via `create_media_record()`
- List endpoint queries database instead of scanning filesystem
- Delete endpoint removes both DB record and physical file
- All endpoints use async SQLAlchemy sessions

**Serialization (`app/api/serializers.py`):**
- Added `serialize_media()` helper to convert Media ORM objects to API response dicts
- Maintains asset_path_to_url() pattern for consistent URL generation

**Pydantic Schema (`app/schemas/media.py`):**
- Added `id` and `original_filename` fields
- Added `model_config = ConfigDict(from_attributes=True)` for ORM compatibility
- Schema now supports both manual construction and ORM object serialization

---

## Phase 2: Element-Media Integration ✅ COMPLETE

Migrated Elements from direct asset_path strings to database-backed Media relationships.

### ElementAsset Junction Table

**New Model (`app/models/element_asset.py`):**
- Many-to-many relationship between Elements and Media
- `element_id`, `media_id` foreign keys
- `role` field for semantic asset identification (e.g., "primary", "front_background", "back_content")
- Unique constraint on `(element_id, role)` - each element can only have one asset per role
- CASCADE delete on element, RESTRICT delete on media (prevents deleting media in use)

### Element Model Updates

**Enhanced Element Model (`app/models/element.py`):**
- Added `media_assets` relationship (List[ElementAsset])
- Kept `asset_path` field with DEPRECATED comment for backward compatibility
- Added helper methods:
  - `get_media(role)` - Get Media object by role
  - `get_media_url(role)` - Get URL for media asset by role
  - `get_primary_asset_path()` - Backward-compatible accessor (prefers legacy asset_path, falls back to primary media)

### Schema Updates

**Enhanced Pydantic Schemas (`app/schemas/element.py`):**
- Added `MediaAssetRef` schema for media asset references
- Updated `ElementBase` to include both `asset_path` (deprecated) and `media_assets` (new)
- Updated `ElementUpdate` to support both patterns
- Added `media_details` to `ElementResponse` for full media information in responses

### Serializer Updates

**Enhanced Serializers (`app/api/serializers.py`):**
- Updated `serialize_element_for_widget()` to include both legacy and new fields
- Updated `serialize_element_detail()` to include both legacy and new fields  
- Returns `asset_path` (using `get_primary_asset_path()` for compatibility)
- Returns `media_assets` (list of {media_id, role})
- Returns `media_details` (full media info including id, filename, url, role, mime_type)

### Widget Base Class Updates

**Enhanced BaseWidget (`app/widgets/base.py`):**
- `_validate_asset_path()` marked as DEPRECATED, kept for backward compatibility
- Added `_validate_media_id()` for validating media exists in database
- Added `set_element_media(element_name, media_id, role)` - Assign/update media for element
- Added `remove_element_media(element_name, role)` - Remove media from element

### API Endpoint Updates

**Enhanced Widget API (`app/api/widgets.py`):**
- Updated element update endpoint to handle `media_assets` field
- Validates media IDs exist before creating ElementAsset records
- Replaces assets for updated roles while preserving others
- Maintains backward compatibility with legacy `asset_path` updates

---

## Migration Benefits Achieved

1. **Referential Integrity** - Foreign key constraints prevent orphaned references
2. **Multi-Asset Support** - Foundation for card element with front/back sides
3. **Query Capabilities** - Can find all elements using a specific media file
4. **Flexible Roles** - Semantic asset identification (primary, background, content, etc.)
5. **Backward Compatibility** - Legacy asset_path still works during migration
6. **Database Consistency** - RESTRICT delete prevents removing media still in use

---

## Next Steps for Card Element

With media now database-backed and element-media relationships established, we can proceed to:

1. ✅ Media model with database storage
2. ✅ ElementAsset many-to-many relationship  
3. ✅ Element helper methods for media management
4. **TODO:** Add `CARD` to `ElementType` enum
5. **TODO:** Design card properties schema (front/back side configurations)
6. **TODO:** Implement card rendering in overlay with anime.js
7. **TODO:** Create CardWidget with flip features

---

## Card Element Design Decisions

### Content Model (Finalized)
- **Single content type per side** (text OR image OR video, not multiple)
- **Optional background image** per side (independent from content)
- **No auto-flip** at this time (manual trigger only)
- **Flexbox alignment** for simplicity

### Asset Storage Pattern (IMPLEMENTED)
- Assets stored via ElementAsset relationship table
- Roles for card: "front_background", "front_content", "back_background", "back_content"
- Widget features use `set_element_media()` to configure assets
- No need for properties JSON storage - proper database relationships

### Animation Library
- **anime.js** selected for card flip animations
- Lightweight (~9KB), perfect for web overlays
- Handles CSS transforms, 3D effects, timing functions needed for card flips