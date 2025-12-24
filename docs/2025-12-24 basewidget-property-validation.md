# BaseWidget Property Validation Integration

## Overview

Added centralized property validation to `BaseWidget` class to minimize code redundancy. Validation is now applied in both API endpoints and widget methods using the same logic.

## Changes Made

### 1. **BaseWidget Enhancement** (`app/widgets/base.py`)

**Added Import:**
```python
from app.services.element_service import validate_element_properties
```

**New Method: `update_element_properties()`**

```python
async def update_element_properties(
    self,
    element_name: str,
    properties: Dict[str, Any]
) -> None:
    """
    Update element properties with validation.
    
    Validates properties against element type schema before applying updates.
    Centralizes validation logic used by both API endpoints and widget methods.
    
    Args:
        element_name: Name of the element to update
        properties: Dictionary of property name -> value
    
    Raises:
        ValueError: If element not found or properties are invalid
    
    Example:
        await widget.update_element_properties("my_card", {
            "position": {"x": 0.5, "y": 0.3},
            "revealed": True,
            "opacity": 0.8
        })
    """
```

**Key Features:**
- Validates properties against element type schema (IMAGE, VIDEO, AUDIO, TEXT, CARD, etc.)
- Raises `ValueError` with descriptive error messages if validation fails
- Applies validated properties directly to element object
- Does NOT commit transaction (caller controls transaction lifecycle)

## Usage Patterns

### In Widget Features

```python
@feature(display_name="Update Card State")
async def update_card(self, card_name: str):
    # Update with validation
    await self.update_element_properties(card_name, {
        "position": {"x": 0.4, "y": 0.5},
        "revealed": True,
        "opacity": 0.9
    })
    
    # Commit changes
    await self.db.commit()
    
    # Broadcast to overlay
    element = self.get_element(card_name)
    await self.broadcast_element_update(element)
```

### In API Endpoints

The validation is already integrated in `app/api/widgets.py`:

```python
if 'properties' in update_data:
    is_valid, errors = validate_element_properties(element.element_type, update_data['properties'])
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid properties: {'; '.join(errors)}")
```

## Property Structure

Properties follow element type-specific schemas:

**IMAGE/VIDEO/TEXT/CARD elements:**
```python
{
    "position": {"x": 0.5, "y": 0.3, "anchor": "center"},
    "size": {"width": 0.2, "height": 0.3},
    "opacity": 0.8,
    "rotation": 45,
    "scale_x": 1.0,
    "scale_y": 1.0,
    "z_index": 100
}
```

**CARD-specific:**
```python
{
    "position": {...},
    "revealed": True,  # Boolean state
    "front_text": "Question",
    "back_text": "Answer"
}
```

**AUDIO elements:**
```python
{
    "volume": 0.7,
    "autoplay": False,
    "loop": False
}
```

## Validation Rules

**Strict Validation:**
- Unknown properties are rejected
- Each element type has explicit allowed properties list
- Type checking enforced (e.g., `revealed` must be boolean)

**Range Validation:**
- Position x, y: [0, 1] fractions
- Opacity: [0, 1]
- Scale: > 0 (positive numbers)
- z_index: integers

**Anchor Support:**
- 9 valid anchor points: top-left, top-center, top-right, center-left, center, center-right, bottom-left, bottom-center, bottom-right
- Optional field (defaults if not specified)

## Test Coverage

**28 comprehensive tests** in `tests/test_positioning.py`:

- **7 tests**: Grid position calculation
- **15 tests**: Property validation (all element types)
- **6 tests**: BaseWidget `update_element_properties()` method

All tests passing ✅

**Run tests:**
```bash
python -m pytest tests/test_positioning.py -v
```

## Code Reusability

Same validation function used in:
1. **API Endpoints** - `app/api/widgets.py`
2. **Widget Methods** - `BaseWidget.update_element_properties()`
3. **Direct Service Access** - `validate_element_properties()` function

This eliminates redundancy and ensures consistent validation everywhere.

## Integration Example: FriendlyFeud Widget

```python
class FriendlyFeudWidget(BaseWidget):
    
    @feature(display_name="Flip Card")
    async def flip_card(self, card_index: int):
        element = self.get_element(f"card_{card_index}")
        
        # Update with validation
        await self.update_element_properties(f"card_{card_index}", {
            "revealed": not element.properties.get("revealed", False)
        })
        
        await self.db.commit()
        await self.broadcast_element_update(element)
```

## Migration Path

Existing widget features that directly modify `element.properties` can be updated to use `update_element_properties()`:

**Before:**
```python
element.properties["opacity"] = 0.5
element.properties["x"] = 0.3  # BAD: x not allowed directly
```

**After:**
```python
await self.update_element_properties("my_element", {
    "opacity": 0.5,
    "position": {"x": 0.3, "y": 0.2}  # GOOD: validated
})
```
