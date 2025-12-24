# Relative Positioning Specification v1.0

**Date:** 2025-12-24  
**Status:** SPECIFICATION (Ready for implementation)  
**Scope:** All element positioning, sizing, and transforms in Stream Companion overlay

---

## 1. Overview

Stream Companion uses a **relative coordinate system** where all positions and sizes are defined as fractions between 0 and 1, relative to the overlay dimensions. This enables:

- **Resolution independence:** Overlay can be resized without recalculating element positions
- **Precise control:** Python widgets calculate exact positions via helper methods
- **Flexible layouts:** Different dashboards can use different overlay dimensions
- **Responsive scaling:** CSS percentage-based positioning auto-scales on resize

**Overlay Reference Dimensions:** 1920×1080 pixels (configurable per dashboard)

---

## 2. Coordinate System

### Origin and Axes
- **Origin (0, 0):** Top-left corner of overlay
- **X-axis:** Horizontal, ranges 0 (left) to 1 (right)
- **Y-axis:** Vertical, ranges 0 (top) to 1 (bottom)
- **All coordinates:** Relative fractions (0 ≤ x, y ≤ 1)

### Example
```
(0, 0) ─────────────────────────── (1, 0)
  │                                   │
  │          (0.5, 0.5)               │
  │              ●                    │
  │                                   │
(0, 1) ─────────────────────────── (1, 1)
```

---

## 3. Position Property

### Definition
```json
{
  "position": {
    "x": 0.5,
    "y": 0.5
  },
  "anchor": "center"
}
```

### Anchor Point
The `anchor` property determines which part of the element aligns with the position coordinates.

**Valid anchor values:**
- `"top-left"` (default) - Element's top-left corner at (x, y)
- `"top-center"` - Element's top-center at (x, y)
- `"top-right"` - Element's top-right corner at (x, y)
- `"center-left"` - Element's center-left at (x, y)
- `"center"` - Element's center at (x, y)
- `"center-right"` - Element's center-right at (x, y)
- `"bottom-left"` - Element's bottom-left corner at (x, y)
- `"bottom-center"` - Element's bottom-center at (x, y)
- `"bottom-right"` - Element's bottom-right corner at (x, y)

**Default anchor:** `"top-left"` (if not specified)

### Position Optionality
- **Required for:** IMAGE, VIDEO, TEXT, TIMER, COUNTER, CANVAS, **CARD**
- **Optional for:** AUDIO, ANIMATION (no visual render)

**Behavior:** Elements without `position` key are not rendered visually (no DOM element created).

### CSS Implementation
Position is implemented via `position: absolute; left/top` with percentage-based calculations:

```css
.element {
  position: absolute;
  left: <calculated-x-percent>;
  top: <calculated-y-percent>;
}
```

**Anchor adjustment calculation (JavaScript):**
```javascript
function calculateOffsetFromAnchor(anchor, elementWidth, elementHeight) {
  const offsets = {
    "top-left": { x: 0, y: 0 },
    "top-center": { x: -elementWidth / 2, y: 0 },
    "top-right": { x: -elementWidth, y: 0 },
    "center-left": { x: 0, y: -elementHeight / 2 },
    "center": { x: -elementWidth / 2, y: -elementHeight / 2 },
    "center-right": { x: -elementWidth, y: -elementHeight / 2 },
    "bottom-left": { x: 0, y: -elementHeight },
    "bottom-center": { x: -elementWidth / 2, y: -elementHeight },
    "bottom-right": { x: -elementWidth, y: -elementHeight }
  };
  return offsets[anchor] || offsets["top-left"];
}
```

---

## 4. Size Property

### Definition
```json
{
  "size": {
    "width": 0.25,
    "height": "auto"
  },
  "aspect_ratio": 1.777
}
```

### Width and Height Values

| Value Type | Example | Meaning |
|------------|---------|---------|
| **Relative fraction** | `0.25` | 25% of overlay dimension |
| **"auto"** | `"auto"` | Calculated from aspect ratio or media dimensions |
| **Null/undefined** | omitted | Default based on element type (optional) |

### Aspect Ratio Handling

**When `height: "auto"` or `width: "auto"`:**

1. **Check element properties for explicit `aspect_ratio`:**
   ```json
   {
     "size": {"width": 0.25, "height": "auto"},
     "aspect_ratio": 1.5
   }
   // height = width / 1.5
   ```

2. **If not specified, use media's native aspect ratio (overlay-level):**
   ```javascript
   // In overlay, when rendering image/video with auto height
   const aspectRatio = mediaElement.naturalWidth / mediaElement.naturalHeight;
   const calculatedHeight = calculatedWidth / aspectRatio;
   ```

3. **If no media, use element type defaults:**
   - CARD: 3:4 (portrait)
   - IMAGE: 16:9 (landscape)
   - VIDEO: 16:9 (landscape)
   - TEXT: 1:1 (square, if height auto)

### Size Optionality
- **All positioned elements** require size (width and height, or width + aspect_ratio)
- **AUDIO elements** do not have size

### CSS Implementation
```css
.element {
  width: calc(25% * 1920px);  /* Relative to overlay reference width */
  height: auto;              /* Calculated from aspect_ratio */
}
```

---

## 5. Transform Properties

Transform properties live in `properties` and control element appearance during animation.

### Standard Transforms
```json
{
  "opacity": 1.0,        // 0 (transparent) to 1 (opaque)
  "rotation": 0,         // Degrees (0-360), CSS transform: rotate()
  "scale_x": 1.0,        // Horizontal multiplier, CSS transform: scaleX()
  "scale_y": 1.0,        // Vertical multiplier, CSS transform: scaleY()
  "z_index": 0           // Integer, CSS z-index property
}
```

### Updates During Animation
- **Properties can be updated while `playing: true`** without interrupting behavior
- **Behavior steps can animate properties** via `animate_property` step type
- **Widgets update transforms** to control layering and visibility

### Example: Z-Index Control
```json
{
  "position": {"x": 0.5, "y": 0.5},
  "size": {"width": 0.2, "height": 0.3},
  "z_index": 100,
  "opacity": 1.0
}
```

---

## 6. Element Type-Specific Schemas

### Common Properties (All Positioned Elements)
```json
{
  "position": {"x": 0, "y": 0, "anchor": "top-left"},
  "size": {"width": 0.25, "height": 0.3},
  "opacity": 1.0,
  "rotation": 0,
  "scale_x": 1.0,
  "scale_y": 1.0,
  "z_index": 0
}
```

### IMAGE
```json
{
  ...common...,
  "filter": "brightness(1.0) contrast(1.0)",  // Optional CSS filters
  "aspect_ratio": 1.777  // Optional, overrides media ratio
}
```

### VIDEO
```json
{
  ...common...,
  "volume": 0.7,         // 0-1
  "autoplay": false,
  "loop": false,
  "aspect_ratio": 1.777  // Optional, overrides media ratio
}
```

### TEXT
```json
{
  ...common...,
  "color": "#FFFFFF",
  "font_family": "Arial",
  "font_size": 24,       // Pixels (absolute, not relative)
  "font_weight": 400,
  "text_align": "center",
  "text_shadow": "2px 2px 4px rgba(0,0,0,0.5)"
}
```

### CARD
```json
{
  ...common...,
  "revealed": false,     // Current state (front/back)
  "front_text": "?",     // Text shown on front side
  "back_text": "ANSWER", // Text shown on back side
  "media_roles": [
    "front_background",  // Background image for face-down
    "back_background",   // Background image for face-up
    "back_content"       // Optional content overlay on back
  ]
}
```

### AUDIO
```json
{
  "volume": 0.7,         // 0-1
  "autoplay": false,
  "loop": false
}
// No position or size
```

### TIMER / COUNTER
```json
{
  ...common...,
  "color": "#FFFFFF",
  "font_family": "Arial",
  "font_size": 24,
  "format": "MM:SS"      // For TIMER
}
```

### CANVAS
```json
{
  ...common...,
  "background_color": "transparent"
}
```

### ANIMATION
```json
{
  // No position or size (managed by animation library)
}
```

---

## 7. Media Positioning Within Elements

**Principle:** Media inside elements are positioned **relative to the element's origin**, not the overlay.

### Card Media Example
For a CARD element at overlay position (0.5, 0.5) with media inside:

```javascript
// Element position in overlay coordinates
elementX = 0.5 * 1920 = 960px;
elementY = 0.5 * 1080 = 540px;
elementWidth = 0.15 * 1920 = 288px;
elementHeight = 0.2 * 1080 = 216px;

// Media (background image) inside card
// Media is ALWAYS stretched to fill the card (100% x 100%)
mediaWidth = 288px;  // 100% of card width
mediaHeight = 216px; // 100% of card height
```

### CSS Implementation
```css
.element.card {
  position: absolute;
  left: 960px;
  top: 540px;
  width: 288px;
  height: 216px;
}

.element.card .card-front,
.element.card .card-back {
  width: 100%;      /* Fill card */
  height: 100%;     /* Fill card */
  background-size: cover;
  background-position: center;
}
```

---

## 8. Viewport Scaling on Overlay Resize

### CSS-Based Scaling (Recommended)

Use CSS percentage-based positioning with viewport dimensions:

```css
.element {
  position: absolute;
  left: <x-percent>%;
  top: <y-percent>%;
  width: <width-percent>%;
  height: <height-percent>%;
}
```

**Advantage:** Automatic scaling, no JavaScript event listeners needed.

### Example
```css
/* Element at (0.5, 0.5) with size 0.25 × 0.3 */
.element {
  position: absolute;
  left: 50%;           /* 0.5 * 100% */
  top: 50%;            /* 0.5 * 100% */
  width: 25%;          /* 0.25 * 100% */
  height: 30%;         /* 0.3 * 100% */
  transform-origin: <anchor-adjusted>;
}
```

### Overlay Resize Handler (JavaScript)
If dynamic recalculation needed:

```javascript
window.addEventListener('resize', () => {
  const elements = document.querySelectorAll('.element');
  
  elements.forEach(el => {
    const data = el.dataset; // {x, y, width, height, anchor}
    
    // Calculate pixel position from relative coordinates
    const pixelX = parseFloat(data.x) * window.innerWidth;
    const pixelY = parseFloat(data.y) * window.innerHeight;
    const pixelWidth = parseFloat(data.width) * window.innerWidth;
    const pixelHeight = parseFloat(data.height) * window.innerHeight;
    
    // Apply anchor adjustment
    const offset = calculateOffsetFromAnchor(data.anchor, pixelWidth, pixelHeight);
    
    el.style.left = (pixelX + offset.x) + 'px';
    el.style.top = (pixelY + offset.y) + 'px';
    el.style.width = pixelWidth + 'px';
    el.style.height = pixelHeight + 'px';
  });
});
```

---

## 9. Position Calculation Helper (Python)

### Purpose
Widgets calculate card positions using a helper method that converts grid layout parameters to relative coordinates.

### Signature
```python
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
    
    Args:
        num_cards: Total number of cards (1-10)
        total_width: Total grid width as fraction of overlay (e.g., 0.8)
        total_height: Total grid height as fraction of overlay (e.g., 0.9)
        vertical_spacing: Space between rows as fraction of overlay height (e.g., 0.02)
        horizontal_spacing: Space between columns as fraction of overlay width (e.g., 0.05)
        columns: Number of columns (default: 2)
    
    Returns:
        List of position dicts: [{"x": 0.1, "y": 0.1}, {"x": 0.55, "y": 0.1}, ...]
    """
```

### Implementation Logic

**Algorithm:**

1. Calculate rows needed: `rows = ceil(num_cards / columns)`
2. Calculate card dimensions:
   - **Card width:** `(total_width - (columns-1)*horizontal_spacing) / columns`
   - **Card height:** `(total_height - (rows-1)*vertical_spacing) / rows`
3. For each card (0 to num_cards-1):
   - Calculate column: `col = index % columns`
   - Calculate row: `row = index // columns`
   - Calculate position:
     - `x = (col * (card_width + horizontal_spacing))`
     - `y = (row * (card_height + vertical_spacing))`

### Example (FriendlyFeud)
```python
# 10 cards, 2 columns, centered with spacing
positions = calculate_element_grid_positions(
    num_cards=10,
    total_width=0.8,        # Cards occupy 80% of overlay width
    total_height=0.9,       # Cards occupy 90% of overlay height
    vertical_spacing=0.02,  # 2% of overlay height between rows
    horizontal_spacing=0.05, # 5% of overlay width between columns
    columns=2
)

# Results in positions like:
# [
#   {"x": 0.1, "y": 0.05},  # Card 1 (col 0, row 0)
#   {"x": 0.55, "y": 0.05}, # Card 2 (col 1, row 0)
#   {"x": 0.1, "y": 0.27},  # Card 3 (col 0, row 1)
#   {"x": 0.55, "y": 0.27}, # Card 4 (col 1, row 1)
#   ...
# ]
```

### Python Code Template
```python
from math import ceil

def calculate_element_grid_positions(
    num_cards: int,
    total_width: float,
    total_height: float,
    vertical_spacing: float,
    horizontal_spacing: float,
    columns: int = 2
) -> List[Dict[str, float]]:
    
    rows = ceil(num_cards / columns)
    
    # Calculate card dimensions
    card_width = (total_width - (columns - 1) * horizontal_spacing) / columns
    card_height = (total_height - (rows - 1) * vertical_spacing) / rows
    
    positions = []
    for index in range(num_cards):
        col = index % columns
        row = index // columns
        
        x = col * (card_width + horizontal_spacing)
        y = row * (card_height + vertical_spacing)
        
        positions.append({"x": x, "y": y})
    
    return positions
```

---

## 10. Property Validation

### Service Layer Validation
The `element_service.py` validates properties against element type schemas before persistence.

### Validation Rules
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
```

### Validation Logic
```python
def validate_element_properties(element_type: str, properties: dict) -> Tuple[bool, List[str]]:
    """Validate that properties match element type schema."""
    errors = []
    allowed_keys = ELEMENT_PROPERTY_SCHEMAS.get(element_type, [])
    
    for key in properties.keys():
        if key not in allowed_keys:
            errors.append(f"Property '{key}' not allowed for {element_type} elements")
    
    # Type-specific validation
    if "position" in properties:
        pos = properties["position"]
        if not isinstance(pos.get("x"), (int, float)) or not (0 <= pos["x"] <= 1):
            errors.append("position.x must be number between 0 and 1")
        if not isinstance(pos.get("y"), (int, float)) or not (0 <= pos["y"] <= 1):
            errors.append("position.y must be number between 0 and 1")
    
    if "opacity" in properties:
        if not isinstance(properties["opacity"], (int, float)) or not (0 <= properties["opacity"] <= 1):
            errors.append("opacity must be number between 0 and 1")
    
    return len(errors) == 0, errors
```

---

## 11. Implementation Checklist

### Backend (Python)
- [ ] Update `Element` model to document position/size schema
- [ ] Create `ElementPropertyValidator` in element_service.py
- [ ] Add `calculate_element_grid_positions()` helper to widget utils
- [ ] Update AlertWidget as reference implementation
- [ ] Validate all property updates via service layer

### Frontend (JavaScript/HTML)
- [ ] Update `renderElement()` to calculate CSS position from relative coords
- [ ] Implement anchor adjustment logic
- [ ] Handle "auto" size calculation (from aspect_ratio or media)
- [ ] Add window resize handler for dynamic scaling
- [ ] Test CSS percentage-based positioning

### CARD Element (Phase 1 Dependency)
- [ ] Add CARD to ElementType enum
- [ ] Define CARD properties schema
- [ ] Implement card rendering (front/back structure)
- [ ] Implement flip animation

---

## 12. Examples

### Example 1: Text Element at Center
```json
{
  "element_type": "text",
  "properties": {
    "position": {"x": 0.5, "y": 0.5, "anchor": "center"},
    "size": {"width": 0.4, "height": 0.1},
    "color": "#FFFFFF",
    "font_size": 48,
    "text_align": "center",
    "z_index": 100
  }
}
```

**CSS Result:**
```css
left: 50%;
top: 50%;
width: 40%;
height: 10%;
transform: translate(-50%, -50%); /* Anchor adjustment */
color: white;
font-size: 48px;
z-index: 100;
```

### Example 2: Card Element in Grid
```python
# Widget code
positions = calculate_element_grid_positions(
    num_cards=10,
    total_width=0.8,
    total_height=0.85,
    vertical_spacing=0.03,
    horizontal_spacing=0.05,
    columns=2
)

for i, pos in enumerate(positions):
    card = self.get_element(f"card_{i+1}")
    card.properties["position"] = {
        "x": pos["x"],
        "y": pos["y"],
        "anchor": "top-left"
    }
    card.properties["size"] = {
        "width": 0.15,
        "height": 0.2
    }
    card.properties["z_index"] = 10
```

### Example 3: Image with Auto Height
```json
{
  "element_type": "image",
  "properties": {
    "position": {"x": 0.1, "y": 0.2, "anchor": "top-left"},
    "size": {"width": 0.3, "height": "auto"},
    "aspect_ratio": 1.777,
    "z_index": 5
  }
}
```

**Calculated:**
- Width: 0.3 × 1920 = 576px
- Height: 576 / 1.777 = 324px (from aspect ratio)

---

## 13. Future Considerations

- **3D Transforms:** `skew_x`, `skew_y`, `perspective` (future)
- **Filters:** More complex CSS filter chains (future)
- **Constraints:** Position/size constraints (min/max bounds) (future)
- **Responsive Breakpoints:** Different layouts for different overlay sizes (future)

---

## 14. Glossary

| Term | Definition |
|------|-----------|
| **Overlay** | The 1920×1080 (or custom) canvas where all elements render |
| **Relative coordinate** | Position/size as fraction 0-1, relative to overlay dimension |
| **Anchor point** | The part of an element that aligns with its position coordinate |
| **Aspect ratio** | Width-to-height ratio, used for "auto" dimension calculation |
| **Grid layout** | Multi-element positioning calculated via helper method |
| **Viewport scaling** | Automatic CSS-based resizing when overlay changes dimensions |

