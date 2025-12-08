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
            behavior={
                "entrance": {
                    "type": "explosion",
                    "duration": self.widget_parameters.get("duration", 2.5)
                },
                "exit": {
                    "type": "fade",
                    "duration": 0.5
                }
            },
            visible=False
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
            behavior={},
            visible=False
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
                "label": "Image Duration (seconds)",
                "min": 0,
                "max": 10,
                "step": 0.1,
                "default": 2.5,
                "optional": True,
            }
        ]
    )
    async def play(self, volume: float, duration: float | None = None):
        """
        Trigger image display with sound.
        
        Args:
            volume: Sound volume level (0-100)
        """
        image_element = self.get_element(_IMAGE, validate_asset=False)
        sound = self.get_element(_AUDIO, validate_asset=False)
        
        # Update image_element properties
        image_element.properties["duration"] = duration
        image_element.properties["particle_count"] = self.widget_parameters.get("particle_count", 100)
        image_element.visible = True
        
        # Play sound if configured and asset exists
        # Convert volume from 0-100 to 0.0-1.0 for audio element
        sound.properties["volume"] = max(0.0, min(volume, 100.0)) / 100.0
        sound.properties["autoplay"] = True
        sound.visible = True
        
        await self.db.commit()
        
        # Broadcast updates after commit
        await self.broadcast_element_update(image_element, action="show")
        if sound and sound.visible:
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
        image_element.visible = False
        sound.visible = False
        sound.properties["autoplay"] = False  # Prevent auto-replay
        
        # Commit changes FIRST
        await self.db.commit()
        
        # Broadcast updates after commit (hide action will stop audio in overlay)
        await self.broadcast_element_update(image_element, action="hide")
        await self.broadcast_element_update(sound, action="hide")
