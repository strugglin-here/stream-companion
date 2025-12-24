"""Image utility functions for widget image handling.

Provides reusable image processing functions used across widgets that
work with image elements (Alert, FriendlyFeud, etc.).

These functions handle:
- Reading image dimensions from files
- Calculating responsive sizing (fractions of overlay)
- Aspect ratio calculations
"""

from pathlib import Path
from PIL import Image


def get_image_dimensions(media_path: Path) -> tuple[int, int]:
    """
    Get image dimensions (width, height) from file.
    
    Args:
        media_path: Path to image file
    
    Returns:
        Tuple of (width, height) in pixels
    
    Raises:
        FileNotFoundError: If file doesn't exist
        Exception: If file cannot be read or is not a valid image
    
    Example:
        width, height = get_image_dimensions(Path("data/media/image.png"))
        # Returns: (1920, 1080)
    """
    if not media_path.exists():
        raise FileNotFoundError(f"Image file not found: {media_path}")
    
    try:
        with Image.open(media_path) as img:
            return img.size
    except Exception as e:
        raise Exception(f"Failed to read image dimensions from {media_path}: {e}")


def calculate_width_fraction(
    image_width_px: int,
    overlay_width_px: int = 1920
) -> float:
    """
    Calculate image width as fraction of overlay width.
    
    Converts pixel dimensions to relative fractions (0-1) for responsive
    positioning. Used to size elements relative to the overlay viewport.
    
    Args:
        image_width_px: Image width in pixels
        overlay_width_px: Overlay width in pixels (default: 1920 for 1080p)
    
    Returns:
        Width as fraction of overlay (0-1)
        - Result is clamped between 0.05 and 1.0
        - Returns 0.2 as fallback if overlay_width_px <= 0
    
    Example:
        # 400px image on 1920px overlay = 0.208 (about 21%)
        fraction = calculate_width_fraction(400, 1920)
        # Returns: 0.208...
    """
    if overlay_width_px <= 0:
        return 0.2  # Fallback to default
    
    fraction = image_width_px / overlay_width_px
    # Clamp between 0.05 and 1.0 to keep reasonable bounds
    return max(0.05, min(fraction, 1.0))


def calculate_height_from_width(
    image_width_px: int,
    image_height_px: int,
    target_width_fraction: float,
    overlay_width_px: int = 1920
) -> float:
    """
    Calculate height fraction based on width and aspect ratio.
    
    Given a desired width fraction and image aspect ratio, calculates
    the corresponding height fraction to maintain proportions.
    
    Args:
        image_width_px: Original image width in pixels
        image_height_px: Original image height in pixels
        target_width_fraction: Desired width as fraction of overlay (0-1)
        overlay_width_px: Overlay width in pixels (default: 1920)
    
    Returns:
        Height as fraction of overlay (0-1)
    
    Example:
        # 1920x1080 image, display at 0.5 width
        height = calculate_height_from_width(1920, 1080, 0.5, 1920)
        # Returns: 0.25 (maintains 16:9 aspect ratio)
    """
    if image_width_px <= 0 or overlay_width_px <= 0:
        return 0.2  # Fallback
    
    aspect_ratio = image_height_px / image_width_px
    width_px = target_width_fraction * overlay_width_px
    height_px = width_px * aspect_ratio
    
    return calculate_width_fraction(int(height_px), overlay_width_px)


def get_aspect_ratio(width_px: int, height_px: int) -> float:
    """
    Calculate aspect ratio (width:height) from dimensions.
    
    Args:
        width_px: Image width in pixels
        height_px: Image height in pixels
    
    Returns:
        Aspect ratio as float (width / height)
    
    Example:
        ratio = get_aspect_ratio(1920, 1080)
        # Returns: 1.777... (16:9)
    """
    if height_px <= 0:
        return 1.0  # Square fallback
    
    return width_px / height_px
