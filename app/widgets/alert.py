"""Alert Widget - Example widget implementation"""

from typing import Dict, Any
from pathlib import Path
from app.widgets.base import BaseWidget, feature
from app.widgets import register_widget
from app.widgets.image_utils import get_image_dimensions, calculate_width_fraction
from app.models.element import Element, ElementType
from app.core.config import settings

_IMAGE = "alert image element"
_AUDIO = "alert audio element"

@register_widget
class AlertWidget(BaseWidget):
    
    widget_class = "AlertWidget"
    display_name = "Alert"
    description = "Animation and sound"
    
    @classmethod
    def get_default_parameters(cls) -> Dict[str, Any]:
        """
        Default widget parameters.
        
        Parameters:
        - duration: Animation duration in milliseconds
        - volume: Default sound volume (0-100)
        - image_width: Image width as fraction of overlay width (0-1)
        - image_x: Image X position as fraction (0-1)
        - image_y: Image Y position as fraction (0-1)
        """
        return {
            "duration": 2.5,
            "volume": 70,
            "image_width": 0.2,   # 20% of overlay width (default fallback)
            "image_x": 0.5,       # Centered horizontally
            "image_y": 0.5,       # Centered vertically
        }
    
    async def create_default_elements(self):
        """
        Create default elements for widget.
        
        Creates:
        1. image_element - Image element with responsive sizing based on parameters
           - Width: Calculated from actual image dimensions if available, 
                    otherwise uses image_width parameter
           - Height: Auto-calculated from image aspect ratio
           - Position: Controlled by image_x, image_y parameters
        2. audio_element - Audio element (user will select from media library)
        """
        # Get positioning parameters
        image_x = self.widget_parameters.get("image_x", 0.5)
        image_y = self.widget_parameters.get("image_y", 0.5)
        
        # Calculate image width from actual image dimensions if media exists
        image_width = self.widget_parameters.get("image_width", 0.2)
        
        # Try to get actual image width from stored media
        if self.elements.get(_IMAGE) is None:  # Element not yet created
            # Try to get media from database
            from sqlalchemy import select
            from app.models.media import Media
            from app.models.element_asset import ElementAsset
            
            try:
                # This will be refined once element is created and media is assigned
                # For now, we'll use the parameter value
                pass
            except Exception:
                # If we can't read image, fall back to parameter
                pass
        
        # Image element with relative positioning and auto-height
        image_element = Element(
            widget_id=self.db_widget.id,
            element_type=ElementType.IMAGE,
            name=_IMAGE,
            properties={
                "media_roles": ["image"],  # Define required media roles
                "position": {
                    "x": image_x,      # Fraction of overlay width (0-1)
                    "y": image_y,      # Fraction of overlay height (0-1)
                    "anchor": "center", # Center anchor for positioning
                    "z_index": 100
                },
                "size": {
                    "width": image_width,    # Fraction of overlay width (0-1)
                    "height": "auto"         # Auto-calculated from aspect ratio
                },
                "opacity": 1.0
            },
            behavior=[
                {"type": "appear", "animation": "explosion", "duration": 500},
                {"type": "wait", "duration": self.widget_parameters.get("duration", 2500)},
                {"type": "disappear", "animation": "fade-out", "duration": 500}
            ],
            playing=False
        )
        
        audio_element = Element(
            widget_id=self.db_widget.id,
            element_type=ElementType.AUDIO,
            name=_AUDIO,
            properties={
                "media_roles": ["sound"],  # Define required media roles
                "volume": 0.7,
                "autoplay": False  # Will be set to True when feature is triggered
            },
            behavior=[],
            playing=False
        )
        
        self.db.add(image_element)
        self.db.add(audio_element)
        
        # Store in memory (no commit - parent handles it)
        self.elements[_IMAGE] = image_element
        self.elements[_AUDIO] = audio_element
    
    async def _update_image_width_from_media(self):
        """
        Update image width based on actual uploaded media dimensions.
        
        Reads the image file dimensions and calculates the appropriate width
        as a fraction of the overlay width. Call this after media is assigned.
        
        Assumes overlay resolution is 1920x1080 by default.
        """
        try:
            image_element = self.elements.get(_IMAGE)
            if not image_element:
                return
            
            # Get image media asset
            image_media = image_element.get_media("image")
            if not image_media:
                return
            
            # Construct path to media file
            media_path = Path(settings.upload_directory) / image_media.filename
            if not media_path.exists():
                return
            
            # Get image dimensions
            width_px, _ = get_image_dimensions(media_path)
            
            # Calculate width fraction (assuming 1920px overlay width)
            image_width_fraction = calculate_width_fraction(width_px, overlay_width_px=1920)
            
            # Update element properties
            await self.update_element_properties(_IMAGE, {
                "size": {
                    "width": image_width_fraction,
                    "height": "auto"
                }
            })
            
            # Update widget parameters for consistency
            self.widget_parameters["image_width"] = image_width_fraction
            self.db_widget.widget_parameters = self.widget_parameters
            
        except Exception as e:
            # Log error but don't fail - fallback to parameter value
            print(f"Warning: Could not calculate image width from media: {e}")
    
    @feature(
        display_name="Play",
        description="Display image and play a sound with customizable position and size.",
        order=1.0,
        parameters=[
            {
                "name": "volume",
                "type": "slider",
                "label": "Sound Volume",
                "min": 1,
                "max": 100,
                "step": 1,
                "default": 70,
                "optional": False
            },
            {
                "name": "duration",
                "type": "slider",
                "label": "Image Duration (ms)",
                "min": 0,
                "max": 10000,
                "step": 100,
                "default": 2500,
                "optional": True,
            },
            {
                "name": "image_x",
                "type": "slider",
                "label": "Image X Position (0-1)",
                "min": 0,
                "max": 1,
                "step": 0.05,
                "default": 0.5,
                "optional": True,
            },
            {
                "name": "image_y",
                "type": "slider",
                "label": "Image Y Position (0-1)",
                "min": 0,
                "max": 1,
                "step": 0.05,
                "default": 0.5,
                "optional": True,
            },
            {
                "name": "image_width",
                "type": "slider",
                "label": "Image Width (0-1)",
                "min": 0.05,
                "max": 1.0,
                "step": 0.05,
                "default": 0.2,
                "optional": True,
            }
        ]
    )
    async def play(
        self,
        volume: float,
        duration: float | None = None,
        image_x: float | None = None,
        image_y: float | None = None,
        image_width: float | None = None
    ):
        """
        Trigger image display with sound.
        
        Resets both elements to stopped state first, then sets playing=True
        to ensure the animation sequence restarts from the beginning.
        
        Auto-calculates image width from actual image dimensions if not overridden.
        
        Args:
            volume: Sound volume level (0-100)
            duration: Duration in milliseconds (optional, uses default if None)
            image_x: Image X position as fraction of overlay width (0-1, optional)
            image_y: Image Y position as fraction of overlay height (0-1, optional)
            image_width: Image width as fraction of overlay width (0-1, optional)
                        If not provided, auto-calculated from actual image dimensions
        """
        image_element = self.get_element(_IMAGE, validate_asset=False)
        sound = self.get_element(_AUDIO, validate_asset=False)
        
        # Step 1: Reset both elements to stopped state
        # This ensures the overlay stops any existing animations
        image_element.playing = False
        sound.playing = False
        
        await self.db.commit()
        
        # Broadcast reset to overlay
        await self.broadcast_element_update(image_element, action="hide")
        await self.broadcast_element_update(sound, action="hide")
        
        # Step 2: Calculate image width
        # If width_override provided, use it; otherwise calculate from media dimensions
        calculated_width = image_width
        
        if calculated_width is None:
            # Try to calculate from actual image dimensions
            try:
                image_media = image_element.get_media("image")
                if image_media:
                    media_path = Path(settings.upload_directory) / image_media.filename
                    if media_path.exists():
                        width_px, _ = get_image_dimensions(media_path)
                        calculated_width = calculate_width_fraction(width_px, overlay_width_px=1920)
            except Exception:
                # If we can't read image, fall back to parameter value
                pass
            
            # Final fallback to parameter
            if calculated_width is None:
                calculated_width = self.widget_parameters.get("image_width", 0.2)
        
        # Get position coordinates
        x = image_x if image_x is not None else self.widget_parameters.get("image_x", 0.5)
        y = image_y if image_y is not None else self.widget_parameters.get("image_y", 0.5)
        
        # Update position and size with validation
        await self.update_element_properties(_IMAGE, {
            "position": {
                "x": x,
                "y": y,
                "anchor": "center",
                "z_index": 100
            },
            "size": {
                "width": calculated_width,
                "height": "auto"  # Height auto-calculated from aspect ratio
            }
        })
        
        # Step 3: Start the animation sequence from scratch
        # Update behavior with the specified duration (or use default from widget parameters)
        wait_duration = duration if duration is not None else self.widget_parameters.get("duration", 2500)
        
        image_element.behavior = [
            {"type": "appear", "animation": "explosion", "duration": 500},
            {"type": "wait", "duration": wait_duration},
            {"type": "disappear", "animation": "fade-out", "duration": 500}
        ]
        image_element.playing = True
        
        # Play sound if configured and asset exists
        # Convert volume from 0-100 to 0.0-1.0 for audio element
        sound.properties["volume"] = max(0.0, min(volume, 100.0)) / 100.0
        sound.properties["autoplay"] = True
        sound.playing = True
        
        await self.db.commit()
        
        # Broadcast updates to start animation
        await self.broadcast_element_update(image_element, action="show")
        await self.broadcast_element_update(sound, action="show")
    
    @feature(
        display_name="Stop",
        description="Immediately stop sound and hide image_element",
        order=2.0,
        parameters=[]
    )
    async def stop(self):
        image_element = self.get_element(_IMAGE)
        sound = self.get_element(_AUDIO)
        
        # Hide elements and stop audio
        image_element.playing = False
        sound.playing = False
        sound.properties["autoplay"] = False  # Prevent auto-replay
        
        # Commit changes FIRST
        await self.db.commit()
        
        # Broadcast updates after commit (hide action will stop audio in overlay)
        await self.broadcast_element_update(image_element, action="hide")
        await self.broadcast_element_update(sound, action="hide")
