"""Element service for business operations.

Unified service layer used by both API endpoints and widget methods.
Orchestrates repository operations but does NOT commit transactions.
"""

from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.repositories.element_repository import ElementRepository
from app.repositories.media_repository import MediaRepository
from app.models.element import Element, ElementType


# Element type-specific property schemas
# Each element type has a list of allowed properties
ELEMENT_PROPERTY_SCHEMAS = {
    ElementType.IMAGE: ["position", "size", "opacity", "rotation", "scale_x", "scale_y", "z_index", "filter", "aspect_ratio"],
    ElementType.VIDEO: ["position", "size", "opacity", "rotation", "scale_x", "scale_y", "z_index", "volume", "autoplay", "loop", "aspect_ratio"],
    ElementType.AUDIO: ["volume", "autoplay", "loop"],
    ElementType.TEXT: ["position", "size", "opacity", "rotation", "scale_x", "scale_y", "z_index", "color", "font_family", "font_size", "font_weight", "text_align", "text_shadow"],
    ElementType.CARD: ["position", "size", "opacity", "rotation", "scale_x", "scale_y", "z_index", "revealed", "front_text", "back_text", "media_roles"],
    ElementType.TIMER: ["position", "size", "opacity", "rotation", "scale_x", "scale_y", "z_index", "color", "font_family", "font_size", "format"],
    ElementType.COUNTER: ["position", "size", "opacity", "rotation", "scale_x", "scale_y", "z_index", "color", "font_family", "font_size"],
    ElementType.CANVAS: ["position", "size", "opacity", "rotation", "scale_x", "scale_y", "z_index", "background_color"],
    ElementType.ANIMATION: []
}


def validate_element_properties(element_type: ElementType, properties: dict) -> Tuple[bool, List[str]]:
    """
    Validate that properties match element type schema.
    
    Args:
        element_type: ElementType enum value
        properties: Dictionary of properties to validate
    
    Returns:
        Tuple of (is_valid: bool, errors: List[str])
        - is_valid: True if all properties valid, False otherwise
        - errors: List of error messages (empty if valid)
    """
    errors = []
    allowed_keys = ELEMENT_PROPERTY_SCHEMAS.get(element_type, [])
    
    # Check for unknown properties (strict validation)
    for key in properties.keys():
        if key not in allowed_keys:
            errors.append(f"Property '{key}' not allowed for {element_type.value} elements")
    
    # Type-specific validation
    if "position" in properties:
        position_errors = _validate_position(properties["position"])
        errors.extend(position_errors)
    
    if "size" in properties:
        size_errors = _validate_size(properties["size"])
        errors.extend(size_errors)
    
    if "opacity" in properties:
        opacity = properties["opacity"]
        if not isinstance(opacity, (int, float)) or not (0 <= opacity <= 1):
            errors.append("opacity must be number between 0 and 1")
    
    if "rotation" in properties:
        rotation = properties["rotation"]
        if not isinstance(rotation, (int, float)):
            errors.append("rotation must be number (degrees)")
    
    if "scale_x" in properties:
        scale_x = properties["scale_x"]
        if not isinstance(scale_x, (int, float)) or scale_x <= 0:
            errors.append("scale_x must be positive number")
    
    if "scale_y" in properties:
        scale_y = properties["scale_y"]
        if not isinstance(scale_y, (int, float)) or scale_y <= 0:
            errors.append("scale_y must be positive number")
    
    if "z_index" in properties:
        z = properties["z_index"]
        if not isinstance(z, int):
            errors.append("z_index must be integer")
    
    if "revealed" in properties:
        revealed = properties["revealed"]
        if not isinstance(revealed, bool):
            errors.append("revealed must be boolean")
    
    return len(errors) == 0, errors


def _validate_position(position: Any) -> List[str]:
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


def _validate_size(size: Any) -> List[str]:
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


class ElementService:
    """Service for element business operations."""
    
    @staticmethod
    async def assign_media(
        element_id: int,
        media_id: int,
        role: str,
        db: AsyncSession,
        replace_existing: bool = True
    ) -> Element:
        """Assign media to an element with role validation.
        
        Unified media assignment operation used by both API and widgets.
        
        Process:
        1. Load element and media (with eager loading)
        2. Validate role against element schema
        3. Clear existing role assignment (if replace_existing)
        4. Create new ElementAsset
        5. Return updated element
        
        Does NOT commit - caller controls transaction.
        
        Args:
            element_id: Element ID
            media_id: Media ID to assign
            role: Role for the media (e.g., "image", "sound")
            db: Database session
            replace_existing: If True, clear existing media for this role
            
        Returns:
            Updated element (not yet committed)
            
        Raises:
            HTTPException: If element or media not found
            ValueError: If role is invalid for element
        """
        # Load element with media relationships
        element = await ElementRepository.get_by_id(element_id, db)
        if not element:
            raise HTTPException(status_code=404, detail=f"Element {element_id} not found")
        
        # Validate media exists
        media = await MediaRepository.get_by_id(media_id, db)
        if not media:
            raise HTTPException(status_code=404, detail=f"Media {media_id} not found")
        
        # Validate role against element schema
        await ElementRepository.validate_media_role(element, role)
        
        # Clear existing role assignment if requested
        if replace_existing:
            await ElementRepository.clear_element_role(element, role)
        
        # Create new assignment
        new_asset = await ElementRepository.create_element_asset(
            element_id=element_id,
            media_id=media_id,
            role=role,
            db=db
        )
        
        # Add to element's relationships
        element.media_assets.append(new_asset)
        
        return element
    
    @staticmethod
    async def assign_multiple_media(
        element_id: int,
        media_assignments: List[Dict[str, Any]],
        db: AsyncSession
    ) -> Element:
        """Assign multiple media to an element at once.
        
        Used by API endpoints that update multiple roles simultaneously.
        
        Args:
            element_id: Element ID
            media_assignments: List of {"media_id": int, "role": str} dicts
            db: Database session
            
        Returns:
            Updated element (not yet committed)
            
        Raises:
            HTTPException: If element or any media not found
            ValueError: If any role is invalid
        """
        # Load element once
        element = await ElementRepository.get_by_id(element_id, db)
        if not element:
            raise HTTPException(status_code=404, detail=f"Element {element_id} not found")
        
        # Validate all roles first (fail fast)
        for assignment in media_assignments:
            role = assignment.get('role', 'default')
            await ElementRepository.validate_media_role(element, role)
        
        # Collect roles being updated
        updated_roles = {assignment.get('role', 'default') for assignment in media_assignments}
        
        # Clear all roles being updated
        element.media_assets = [
            asset for asset in element.media_assets
            if asset.role not in updated_roles
        ]
        
        # Add new assignments
        for assignment in media_assignments:
            media_id = assignment['media_id']
            role = assignment.get('role', 'default')
            
            # Validate media exists
            media = await MediaRepository.get_by_id(media_id, db)
            if not media:
                raise HTTPException(status_code=404, detail=f"Media {media_id} not found")
            
            # Create new asset
            new_asset = await ElementRepository.create_element_asset(
                element_id=element_id,
                media_id=media_id,
                role=role,
                db=db
            )
            element.media_assets.append(new_asset)
        
        return element
