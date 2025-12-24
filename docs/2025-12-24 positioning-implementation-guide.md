# Relative Positioning Implementation Guide

**Date:** 2025-12-24  
**Reference:** `2025-12-24 relative-positioning-specification.md`  
**Scope:** Step-by-step implementation of relative positioning system

---

## Phase 0: Pre-Implementation (Current)

### Documentation Review ✓
- [x] Relative Positioning Specification created
- [x] Property schemas defined per element type
- [x] Helper method signature documented
- [x] CSS implementation strategy outlined

### Current Code State
- **Element model:** Supports arbitrary JSON properties (no validation yet)
- **Overlay rendering:** Uses direct pixel positioning (needs update to relative coords)
- **No grid helpers:** Widgets must manually calculate positions (error-prone)

---

## Phase 1: Backend Implementation

### 1.1 Add ElementPropertyValidator Service

**File:** `app/services/element_service.py` (extend existing)

**Add constant:**
```python
ELEMENT_PROPERTY_SCHEMAS = {
    "image": ["position", "size", "opacity", "rotation", "scale_x", "scale_y", "z_index", "filter", "aspect_ratio"],
    "video": ["position", "size", "opacity", "rotation", "scale_x", "scale_y", "z_index", "volume", "autoplay", "loop", "aspect_ratio"],
    "audio": ["volume", "autoplay", "loop"],
    "text": ["position", "size", "opacity", "rotation", "scale_x", "scale_y", "z_index", "color", "font_family", "font_size", "font_weight", "text_align", "text_shadow"],
    "card": ["position", "size", "opacity", "rotation", "scale_x", "scale_y", "z_index", "revealed", "front_text", "back_text", "media_roles"],
    "timer": ["position", "size", "opacity", "rotation", "scale_x", "scale_y", "z_index", "color", "font_family", "font_size", "format"],
    "counter": ["position", "size", "opacity", "rotation", "scale_x", "scale_y", "z_index", "color", "font_family", "font_size"],
    "canvas": ["position", "size", "opacity", "rotation", "scale_x", "scale_y", "z_index", "background_color"],
    "animation": []
}

def validate_element_properties(element_type: str, properties: dict) -> Tuple[bool, List[str]]:
    """Validate properties against element type schema."""
    errors = []
    allowed_keys = ELEMENT_PROPERTY_SCHEMAS.get(element_type, [])
    
    # Check for unknown properties
    for key in properties.keys():
        if key not in allowed_keys:
            errors.append(f"Property '{key}' not allowed for {element_type} elements")
    
    # Type-specific validation
    if "position" in properties:
        errors.extend(_validate_position(properties["position"]))
    
    if "size" in properties:
        errors.extend(_validate_size(properties["size"]))
    
    if "opacity" in properties:
        opacity = properties["opacity"]
        if not isinstance(opacity, (int, float)) or not (0 <= opacity <= 1):
            errors.append("opacity must be number between 0 and 1")
    
    if "rotation" in properties:
        rotation = properties["rotation"]
        if not isinstance(rotation, (int, float)):
            errors.append("rotation must be number (degrees)")
    
    if "z_index" in properties:
        z = properties["z_index"]
        if not isinstance(z, int):
            errors.append("z_index must be integer")
    
    return len(errors) == 0, errors

def _validate_position(position: dict) -> List[str]:
    """Validate position object."""
    errors = []
    
    if not isinstance(position, dict):
        errors.append("position must be object with x and y")
        return errors
    
    # Validate x
    if "x" not in position:
        errors.append("position.x is required")
    else:
        x = position["x"]
        if not isinstance(x, (int, float)) or not (0 <= x <= 1):
            errors.append("position.x must be number between 0 and 1")
    
    # Validate y
    if "y" not in position:
        errors.append("position.y is required")
    else:
        y = position["y"]
        if not isinstance(y, (int, float)) or not (0 <= y <= 1):
            errors.append("position.y must be number between 0 and 1")
    
    # Validate anchor if present
    if "anchor" in position:
        anchor = position["anchor"]
        valid_anchors = {
            "top-left", "top-center", "top-right",
            "center-left", "center", "center-right",
            "bottom-left", "bottom-center", "bottom-right"
        }
        if anchor not in valid_anchors:
            errors.append(f"anchor must be one of: {', '.join(sorted(valid_anchors))}")
    
    return errors

def _validate_size(size: dict) -> List[str]:
    """Validate size object."""
    errors = []
    
    if not isinstance(size, dict):
        errors.append("size must be object with width and/or height")
        return errors
    
    # Validate width
    if "width" in size:
        width = size["width"]
        if isinstance(width, str) and width != "auto":
            errors.append("width must be number or 'auto'")
        elif isinstance(width, (int, float)):
            if not (0 < width <= 1):
                errors.append("width must be between 0 and 1")
    
    # Validate height
    if "height" in size:
        height = size["height"]
        if isinstance(height, str) and height != "auto":
            errors.append("height must be number or 'auto'")
        elif isinstance(height, (int, float)):
            if not (0 < height <= 1):
                errors.append("height must be between 0 and 1")
    
    return errors
```

**Usage in API endpoint (`app/api/widgets.py`):**
```python
from app.services.element_service import validate_element_properties

@router.patch("/widgets/{widget_id}/elements/{element_id}")
async def update_element(widget_id: int, element_id: int, data: ElementUpdate, db: AsyncSession = Depends(get_db)):
    # ... existing code ...
    
    # Validate properties before updating
    if "properties" in data.model_dump(exclude_unset=True):
        is_valid, errors = validate_element_properties(element.element_type, data.properties or {})
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid properties: {'; '.join(errors)}")
    
    # ... continue with update ...
```

---

### 1.2 Add Grid Position Helper

**File:** `app/widgets/position_helper.py` (new)

```python
"""Helper for calculating element positions in grid layouts."""

from math import ceil
from typing import List, Dict

def calculate_element_grid_positions(
    num_cards: int,
    total_width: float,
    total_height: float,
    vertical_spacing: float,
    horizontal_spacing: float,
    columns: int = 2
) -> List[Dict[str, float]]:
    """
    Calculate element positions for a grid layout.
    
    All parameters are relative fractions (0-1) of overlay dimensions.
    
    Args:
        num_cards: Total number of elements to position (1-10 typical)
        total_width: Total grid width as fraction of overlay (e.g., 0.8 = 80%)
        total_height: Total grid height as fraction of overlay (e.g., 0.9 = 90%)
        vertical_spacing: Space between rows as fraction of overlay height (e.g., 0.02 = 2%)
        horizontal_spacing: Space between columns as fraction of overlay width (e.g., 0.05 = 5%)
        columns: Number of columns in grid (default: 2)
    
    Returns:
        List of position dicts with x, y coordinates for each element.
        Example: [{"x": 0.1, "y": 0.05}, {"x": 0.55, "y": 0.05}, ...]
    
    Example:
        positions = calculate_element_grid_positions(
            num_cards=10,
            total_width=0.8,
            total_height=0.85,
            vertical_spacing=0.03,
            horizontal_spacing=0.05,
            columns=2,
        )
    """
    if num_cards <= 0:
        return []
    
    if columns <= 0:
        raise ValueError("columns must be positive")
    
    rows = ceil(num_cards / columns)
    
    # Calculate individual card dimensions
    # Subtract spacing between cards (which is columns-1 and rows-1 gaps)
    available_width = total_width - (columns - 1) * horizontal_spacing
    available_height = total_height - (rows - 1) * vertical_spacing
    
    card_width = available_width / columns
    card_height = available_height / rows
    
    positions = []
    for index in range(num_cards):
        col = index % columns
        row = index // columns
        
        # Calculate top-left position of card
        x = col * (card_width + horizontal_spacing)
        y = row * (card_height + vertical_spacing)
        
        positions.append({"x": x, "y": y})
    
    return positions


def calculate_centered_grid_positions(
    num_cards: int,
    card_width: float,
    card_height: float,
    vertical_spacing: float,
    horizontal_spacing: float,
    columns: int = 2
) -> List[Dict[str, float]]:
    """
    Calculate grid positions centered on overlay.
    
    Args:
        num_cards: Total number of elements
        card_width: Width of each card as fraction (e.g., 0.15)
        card_height: Height of each card as fraction (e.g., 0.2)
        vertical_spacing: Space between rows
        horizontal_spacing: Space between columns
        columns: Number of columns
    
    Returns:
        Centered grid positions
    
    Example:
        positions = calculate_centered_grid_positions(
            num_cards=10,
            card_width=0.15,
            card_height=0.2,
            vertical_spacing=0.03,
            horizontal_spacing=0.05,
            columns=2
        )
    """
    rows = ceil(num_cards / columns)
    
    # Calculate total grid dimensions
    total_width = columns * card_width + (columns - 1) * horizontal_spacing
    total_height = rows * card_height + (rows - 1) * vertical_spacing
    
    return calculate_element_grid_positions(
        num_cards=num_cards,
        total_width=total_width,
        total_height=total_height,
        vertical_spacing=vertical_spacing,
        horizontal_spacing=horizontal_spacing,
        columns=columns,
    )
```

**Usage in FriendlyFeudWidget:**
```python
from app.widgets.position_helper import calculate_centered_grid_positions

async def start_new_round(self, answers: List[Dict[str, Any]]):
    # Calculate card positions (centered, 2 columns)
    positions = calculate_centered_grid_positions(
        num_cards=len(answers),
        card_width=0.15,
        card_height=0.2,
        vertical_spacing=0.03,
        horizontal_spacing=0.05,
        columns=2
    )
    
    # Apply positions to card elements
    for i, pos in enumerate(positions):
        card = self.get_element(f"card_{i+1}")
        card.properties["position"] = {
            "x": pos["x"],
            "y": pos["y"],
            "anchor": "top-left"
        }
```

---

### 1.3 Update Element Model Documentation

**File:** `app/models/element.py`

Add docstring to `properties` column with schema reference:

```python
# Display properties (stored as JSON for flexibility)
# Schema varies by element_type - see ELEMENT_PROPERTY_SCHEMAS in services
# Common properties: position, size, opacity, rotation, scale_x, scale_y, z_index
# Type-specific: color, font_size, etc.
# See: docs/2025-12-24 relative-positioning-specification.md
properties: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
```

---

## Phase 2: Frontend Implementation

### 2.1 Update renderElement() in Overlay

**File:** `frontend/overlay/index.html`

**Update the `renderElement()` function:**

```javascript
function renderElement(element) {
    let elementDiv = document.getElementById(`element-${element.id}`);
    
    // Create element if not exists
    if (!elementDiv) {
        elementDiv = document.createElement('div');
        elementDiv.id = `element-${element.id}`;
        elementDiv.className = 'element';
        elementDiv.dataset.elementId = element.id;
        elementDiv.dataset.elementType = element.element_type;
        document.body.appendChild(elementDiv);
    }
    
    // Apply positioning and sizing
    applyElementPositioning(elementDiv, element);
    applyElementSize(elementDiv, element);
    applyElementTransforms(elementDiv, element);
    
    // Render content based on type
    renderElementContent(elementDiv, element);
    
    // Handle animation state
    if (element.playing) {
        elementDiv.classList.add('playing');
        elementDiv.classList.remove('stopped');
        startElementAnimation(elementDiv, element);
    } else {
        elementDiv.classList.add('stopped');
        elementDiv.classList.remove('playing');
        stopElementAnimation(elementDiv);
    }
    
    return elementDiv;
}

function applyElementPositioning(elementDiv, element) {
    const props = element.properties || {};
    
    // Skip positioning if no position defined (e.g., audio)
    if (!props.position) {
        elementDiv.style.display = 'none';
        return;
    }
    
    elementDiv.style.display = 'block';
    
    const position = props.position;
    const x = position.x; // 0-1
    const y = position.y; // 0-1
    const anchor = position.anchor || 'top-left';
    
    // Use percentage-based CSS (auto-scales on resize)
    elementDiv.style.position = 'absolute';
    elementDiv.style.left = (x * 100) + '%';
    elementDiv.style.top = (y * 100) + '%';
    
    // Apply anchor adjustment
    const offset = calculateAnchorOffset(anchor, elementDiv);
    if (offset.x !== 0 || offset.y !== 0) {
        elementDiv.style.transform = `translate(${offset.x}px, ${offset.y}px)`;
    }
}

function applyElementSize(elementDiv, element) {
    const props = element.properties || {};
    
    if (!props.size) {
        return;
    }
    
    const size = props.size;
    
    // Width
    if (size.width && size.width !== 'auto') {
        elementDiv.style.width = (size.width * 100) + '%';
    }
    
    // Height
    if (size.height === 'auto') {
        // Calculate from aspect ratio
        const aspectRatio = props.aspect_ratio || calculateMediaAspectRatio(element);
        if (aspectRatio && size.width) {
            const calculatedHeight = (size.width / aspectRatio) * 100;
            elementDiv.style.height = calculatedHeight + '%';
        } else {
            elementDiv.style.height = 'auto';
        }
    } else if (size.height && size.height !== 'auto') {
        elementDiv.style.height = (size.height * 100) + '%';
    }
}

function applyElementTransforms(elementDiv, element) {
    const props = element.properties || {};
    
    let transforms = [];
    
    // Rotation
    if (props.rotation) {
        transforms.push(`rotate(${props.rotation}deg)`);
    }
    
    // Scale
    const scaleX = props.scale_x !== undefined ? props.scale_x : 1;
    const scaleY = props.scale_y !== undefined ? props.scale_y : 1;
    if (scaleX !== 1 || scaleY !== 1) {
        transforms.push(`scaleX(${scaleX}) scaleY(${scaleY})`);
    }
    
    // Apply transforms
    if (transforms.length > 0) {
        elementDiv.style.transform = transforms.join(' ');
    }
    
    // Opacity
    if (props.opacity !== undefined) {
        elementDiv.style.opacity = props.opacity;
    }
    
    // Z-index
    if (props.z_index !== undefined) {
        elementDiv.style.zIndex = props.z_index;
    }
}

function calculateAnchorOffset(anchor, elementDiv) {
    const width = elementDiv.offsetWidth || 0;
    const height = elementDiv.offsetHeight || 0;
    
    const offsets = {
        "top-left": { x: 0, y: 0 },
        "top-center": { x: -width / 2, y: 0 },
        "top-right": { x: -width, y: 0 },
        "center-left": { x: 0, y: -height / 2 },
        "center": { x: -width / 2, y: -height / 2 },
        "center-right": { x: -width, y: -height / 2 },
        "bottom-left": { x: 0, y: -height },
        "bottom-center": { x: -width / 2, y: -height },
        "bottom-right": { x: -width, y: -height }
    };
    
    return offsets[anchor] || offsets["top-left"];
}

function calculateMediaAspectRatio(element) {
    // Try to get aspect ratio from media
    // This is element-specific (image vs video vs card background)
    // For now, return null (use element's aspect_ratio property)
    return null;
}

// Handle window resize to recalculate positions
window.addEventListener('resize', () => {
    elements.forEach((element, id) => {
        const div = document.getElementById(`element-${id}`);
        if (div) {
            applyElementPositioning(div, element);
        }
    });
});
```

---

### 2.2 Update CSS for Percentage-Based Positioning

**File:** `frontend/overlay/index.html` (CSS section)

```css
.element {
    position: absolute;
    box-sizing: border-box;
    /* Positioning handled by JavaScript (left/top in %) */
    /* Size handled by JavaScript (width/height in %) */
}

.element.playing {
    /* Element is executing animation */
    /* GSAP timeline controls visibility and transforms */
}

.element.stopped {
    opacity: 0;
    pointer-events: none;
    visibility: hidden;
}

/* Element-type specific styling */

.element[data-element-type="image"],
.element[data-element-type="video"] {
    /* Media fills element */
}

.element[data-element-type="image"] img,
.element[data-element-type="video"] video {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}

.element[data-element-type="text"] {
    display: flex;
    align-items: center;
    justify-content: center;
}

.element[data-element-type="card"] {
    perspective: 1000px;
}

.card-inner {
    position: relative;
    width: 100%;
    height: 100%;
    transform-style: preserve-3d;
}

.card-front,
.card-back {
    position: absolute;
    width: 100%;
    height: 100%;
    backface-visibility: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
}

.card-back {
    transform: rotateY(180deg);
}
```

---

### 2.3 Update CARD Rendering Logic

**File:** `frontend/overlay/index.html`

```javascript
function renderElementContent(elementDiv, element) {
    // Clear existing content
    elementDiv.innerHTML = '';
    
    switch (element.element_type) {
        case 'image':
            renderImageElement(elementDiv, element);
            break;
        case 'video':
            renderVideoElement(elementDiv, element);
            break;
        case 'audio':
            renderAudioElement(elementDiv, element);
            break;
        case 'text':
            renderTextElement(elementDiv, element);
            break;
        case 'card':
            renderCardElement(elementDiv, element);
            break;
        // ... other types ...
    }
}

function renderCardElement(elementDiv, element) {
    const props = element.properties || {};
    const mediaDetails = element.media_details || {};
    
    // Create card structure
    const cardInner = document.createElement('div');
    cardInner.className = 'card-inner';
    
    // Front side (face-down)
    const cardFront = document.createElement('div');
    cardFront.className = 'card-front';
    cardFront.style.backgroundColor = '#333';
    cardFront.style.color = 'white';
    cardFront.style.fontSize = '48px';
    cardFront.textContent = props.front_text || '?';
    
    // Back side (face-up with answer)
    const cardBack = document.createElement('div');
    cardBack.className = 'card-back';
    cardBack.style.backgroundColor = '#666';
    cardBack.style.color = 'white';
    cardBack.style.fontSize = '24px';
    cardBack.textContent = props.back_text || 'ANSWER';
    
    // Apply background images if provided
    if (mediaDetails.front_background) {
        cardFront.style.backgroundImage = `url(${mediaDetails.front_background.url})`;
        cardFront.style.backgroundSize = 'cover';
        cardFront.style.backgroundPosition = 'center';
    }
    
    if (mediaDetails.back_background) {
        cardBack.style.backgroundImage = `url(${mediaDetails.back_background.url})`;
        cardBack.style.backgroundSize = 'cover';
        cardBack.style.backgroundPosition = 'center';
    }
    
    cardInner.appendChild(cardFront);
    cardInner.appendChild(cardBack);
    elementDiv.appendChild(cardInner);
    
    // Set initial flip state
    if (props.revealed) {
        cardInner.style.transform = 'rotateY(180deg)';
    }
}
```

---

## Phase 3: Testing

### 3.1 Backend Testing

**Test file:** `tests/test_positioning.py` (new)

```python
import pytest
from app.services.element_service import validate_element_properties
from app.widgets.position_helper import calculate_element_grid_positions

def test_valid_position():
    props = {"position": {"x": 0.5, "y": 0.5}}
    is_valid, errors = validate_element_properties("image", props)
    assert is_valid
    assert len(errors) == 0

def test_invalid_position_out_of_range():
    props = {"position": {"x": 1.5, "y": 0.5}}
    is_valid, errors = validate_element_properties("image", props)
    assert not is_valid
    assert any("between 0 and 1" in e for e in errors)

def test_grid_positions_10_cards_2_columns():
    positions = calculate_element_grid_positions(
        num_cards=10,
        total_width=0.8,
        total_height=0.85,
        vertical_spacing=0.03,
        horizontal_spacing=0.05,
        columns=2
    )
    
    assert len(positions) == 10
    # First card
    assert positions[0]["x"] == pytest.approx(0.1)
    assert positions[0]["y"] == pytest.approx(0.05)
    # Second card (same row, different column)
    assert positions[1]["x"] > positions[0]["x"]
    # Third card (second row)
    assert positions[2]["y"] > positions[0]["y"]
```

### 3.2 Frontend Testing

**Manual test in overlay:**

```javascript
// Create test element
const testElement = {
    id: 999,
    element_type: 'text',
    playing: true,
    properties: {
        position: { x: 0.5, y: 0.5, anchor: 'center' },
        size: { width: 0.3, height: 0.1 },
        color: '#FFFFFF',
        font_size: 24,
        text_align: 'center',
        z_index: 100
    }
};

renderElement(testElement);
// Should appear centered on overlay
```

---

## Phase 4: Migration

### 4.1 Existing Widgets

Update AlertWidget to use relative positioning:

```python
# Before
image_element.properties = {
    "media_roles": ["image"],
    "position": {"x": 0, "y": 0},  # Direct pixel-like coords
    "size": {"width": 50, "height": 50}
}

# After (using relative positioning)
image_element.properties = {
    "media_roles": ["image"],
    "position": {"x": 0.5, "y": 0.5, "anchor": "center"},
    "size": {"width": 0.1, "height": 0.1},  # 10% of overlay
    "z_index": 100
}
```

---

## Implementation Checklist

### Backend
- [ ] Add `validate_element_properties()` to element_service.py
- [ ] Add `calculate_element_grid_positions()` to new position_helper.py
- [ ] Update element update API endpoint to validate properties
- [ ] Update Element model docstring
- [ ] Update AlertWidget example

### Frontend
- [ ] Update `renderElement()` to use relative positioning
- [ ] Implement `applyElementPositioning()` with anchor support
- [ ] Implement `applyElementSize()` with auto-height calculation
- [ ] Implement `applyElementTransforms()`
- [ ] Update card rendering with 3D CSS
- [ ] Add window resize handler

### Testing
- [ ] Unit tests for validation
- [ ] Unit tests for grid calculation
- [ ] Manual overlay tests

### Documentation
- [ ] Relative Positioning Specification ✓
- [ ] Implementation Guide (this file) ✓
- [ ] Update README with positioning examples
- [ ] Update widget development guide

