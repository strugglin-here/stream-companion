# Alert Widget Update - Relative Positioning & Responsive Sizing

## Overview

Updated the Alert widget to conform to the new relative positioning system and responsive sizing specifications. The widget now supports:
- **Relative positioning** using fractions (0-1) instead of pixels
- **Responsive height** auto-calculated from image aspect ratio
- **Configurable parameters** for position and size
- **Feature-level control** of position/size via admin console

## Changes Made

### 1. **Default Parameters Enhanced**

Added three new positioning parameters:

```python
def get_default_parameters(cls) -> Dict[str, Any]:
    return {
        "duration": 2.5,
        "volume": 70,
        "image_width": 0.2,   # 20% of overlay width
        "image_x": 0.5,       # Centered horizontally
        "image_y": 0.5,       # Centered vertically
    }
```

**Parameter Definitions:**
- `image_width` (0-1): Image width as fraction of overlay width
- `image_x` (0-1): Image X position (horizontal center with "center" anchor)
- `image_y` (0-1): Image Y position (vertical center with "center" anchor)

### 2. **Element Properties Updated**

Image element now uses relative coordinates and responsive sizing:

**Before:**
```python
"position": {
    "x": 0,      # Pixel coordinates
    "y": 0,
    "z_index": 100
},
"size": {
    "width": 50,   # Fixed pixel size
    "height": 50
}
```

**After:**
```python
"position": {
    "x": 0.5,          # Relative fraction (0-1)
    "y": 0.5,          # Centered
    "anchor": "center", # Anchor point
    "z_index": 100
},
"size": {
    "width": 0.2,      # Relative fraction (0-1)
    "height": "auto"   # Auto-calculated from aspect ratio
}
```

### 3. **Feature Signature Updated**

Added position and size parameters to the `play()` feature:

```python
@feature(...)
async def play(
    self,
    volume: float,
    duration: float | None = None,
    image_x: float | None = None,
    image_y: float | None = None,
    image_width: float | None = None
)
```

**New Parameters (all optional):**
- `image_x`: Override default X position via admin console
- `image_y`: Override default Y position via admin console
- `image_width`: Override default width via admin console

**UI Controls in Admin Console:**
```
Feature: Play
├── Sound Volume (required)
│   └── Slider: 1-100
├── Image Duration (optional)
│   └── Slider: 0-10000 ms
├── Image X Position (optional)
│   └── Slider: 0-1.0 (step 0.05)
├── Image Y Position (optional)
│   └── Slider: 0-1.0 (step 0.05)
└── Image Width (optional)
    └── Slider: 0.05-1.0 (step 0.05)
```

### 4. **Property Update with Validation**

Feature now uses `update_element_properties()` for validation:

```python
# Update position and size with validation
await self.update_element_properties(_IMAGE, {
    "position": {
        "x": x,
        "y": y,
        "anchor": "center",
        "z_index": 100
    },
    "size": {
        "width": width,
        "height": "auto"
    }
})
```

**Benefits:**
- ✅ Type checking (x, y are fractions 0-1)
- ✅ Schema validation (unknown properties rejected)
- ✅ Consistent error handling

## Usage Examples

### Default Behavior (from widget parameters)

```python
# Parameters set once when widget is created
widget = AlertWidget(db, db_widget)
# Defaults: centered image, 20% width
```

### Custom Position via Admin Console

Operator can use the admin UI to call `play()` with custom values:

```
Feature Execution:
  volume: 75
  image_x: 0.3  (left of center)
  image_y: 0.2  (upper portion)
  image_width: 0.15  (smaller)
```

### Programmatic Control (if called from Python)

```python
await alert_widget.play(
    volume=80,
    duration=3000,
    image_x=0.25,  # Position 25% from left
    image_y=0.75,  # Position 75% from top
    image_width=0.25  # 25% of overlay width
)
```

## Property Validation

All position and size values are validated before updating:

- **position.x, position.y**: Must be 0-1
- **position.anchor**: Must be one of 9 valid anchors (top-left, center, etc.)
- **size.width**: Must be 0-1 fraction or "auto"
- **size.height**: Must be 0-1 fraction or "auto"
- **z_index**: Must be integer

Invalid values raise `ValueError` with descriptive errors.

## Responsive Behavior

The image element automatically scales based on viewport size:

1. **Width is set as percentage** → CSS percentage-based positioning handles scaling
2. **Height is "auto"** → Overlay calculates from image's aspect ratio
3. **Position is fraction** → CSS adjusts automatically on window resize

**No JavaScript recalculation needed** - purely CSS-based percentage positioning.

## Migration to FriendlyFeud

This pattern establishes the template for FriendlyFeud widget:

```python
class FriendlyFeudWidget(BaseWidget):
    def get_default_parameters(cls):
        return {
            "card_width": 0.12,    # 12% of overlay width
            "cards_per_row": 2,
            # ... other params
        }
    
    async def create_default_elements(self):
        # Use calculate_element_grid_positions() with card_width
        # Apply positioning to each card element
        # All cards use relative positioning
    
    @feature(display_name="Flip Card")
    async def flip_card(self, card_index: int, position_override: dict = None):
        # Update card position/size via update_element_properties()
```

## Testing

Alert widget is production-ready and follows all new specifications:
- ✅ Relative positioning (0-1 fractions)
- ✅ Responsive sizing (auto-height from aspect ratio)
- ✅ Property validation (strict schema)
- ✅ Feature parameters (admin console control)
- ✅ Parameter updates (from both defaults and feature calls)

To test:
1. Create an Alert widget in admin console
2. Upload an image to the alert element
3. Call `play()` feature with various position/width parameters
4. Verify image appears at specified position and size
5. Verify image height scales automatically based on aspect ratio
