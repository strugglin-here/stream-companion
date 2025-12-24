"""Alert Widget - Example widget implementation"""

from typing import Dict, Any
from app.widgets.base import BaseWidget, feature
from app.widgets import register_widget
from app.models.element import Element, ElementType

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
        """
        return {
            "duration": 2.5,
            "volume": 70,
        }
    
    async def create_default_elements(self):
        """
        Create default elements for widget.
        
        Creates:
        1. image_element - Image element (user will upload custom image)
        2. audio_element - Audio element (user will select from media library)
        """
        # image_element particle image
        image_element = Element(
            widget_id=self.db_widget.id,
            element_type=ElementType.IMAGE,
            name=_IMAGE,
            properties={
                "media_roles": ["image"],  # Define required media roles
                "position": {
                    "x": 0,  # Center of 1920px screen
                    "y": 0,  # Center of 1080px screen
                    "z_index": 100
                },
                "size": {
                    "width": 50,
                    "height": 50
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
    
    @feature(
        display_name="Play",
        description="Display image and play a sound.",
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
            }
        ]
    )
    async def play(self, volume: float, duration: float | None = None):
        """
        Trigger image display with sound.
        
        Resets both elements to stopped state first, then sets playing=True
        to ensure the animation sequence restarts from the beginning.
        
        Args:
            volume: Sound volume level (0-100)
            duration: Duration in milliseconds (optional)
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
        
        # Step 2: Start the animation sequence from scratch
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
