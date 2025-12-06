"""Confetti Alert Widget - Example widget implementation"""

from typing import Dict, Any
from app.widgets.base import BaseWidget, feature
from app.widgets import register_widget
from app.models.element import Element, ElementType


@register_widget
class ConfettiAlertWidget(BaseWidget):
    """
    Confetti Alert Widget
    
    Displays a celebratory confetti explosion with customizable intensity and color.
    Perfect for celebrating milestones, new followers, donations, or special events.
    
    Elements:
    - confetti_particle: Image element for confetti particles
    - pop_sound: Audio element for the pop sound effect
    
    Features:
    - trigger_blast: Launch confetti particles with intensity and color options
    - stop_confetti: Immediately stop and hide all confetti
    """
    
    widget_class = "ConfettiAlertWidget"
    display_name = "Confetti Alert"
    description = "Celebratory particle explosion with sound"
    
    @classmethod
    def get_default_parameters(cls) -> Dict[str, Any]:
        """
        Default widget parameters.
        
        Returns:
            - blast_duration: How long the confetti animation lasts (seconds)
            - particle_count: Number of confetti particles to spawn
            - default_color: Default color for confetti if not specified
        """
        return {
            "blast_duration": 2.5,
            "particle_count": 100,
            "default_color": "#FF5733"
        }
    
    async def create_default_elements(self):
        """
        Create default elements for confetti widget.
        
        Creates:
        1. confetti_particle - Image element (user will upload custom image)
        2. pop_sound - Audio element (user will select from media library)
        """
        # Confetti particle image
        confetti_particle = Element(
            widget_id=self.db_widget.id,
            element_type=ElementType.IMAGE,
            name="confetti_particle",
            asset_path=None,  # User will configure
            properties={
                "position": {
                    "x": 960,  # Center of 1920px screen
                    "y": 540,  # Center of 1080px screen
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
                    "duration": self.widget_parameters.get("blast_duration", 2.5)
                },
                "exit": {
                    "type": "fade",
                    "duration": 0.5
                }
            },
            visible=False
        )
        
        # Pop sound effect
        pop_sound = Element(
            widget_id=self.db_widget.id,
            element_type=ElementType.AUDIO,
            name="pop_sound",
            asset_path=None,  # User will configure
            properties={
                "volume": 0.7,
                "autoplay": False  # Will be set to True when feature is triggered
            },
            behavior={},
            visible=False
        )
        
        self.db.add(confetti_particle)
        self.db.add(pop_sound)
        
        # Store in memory (no commit - parent handles it)
        self.elements["confetti_particle"] = confetti_particle
        self.elements["pop_sound"] = pop_sound
    
    @feature(
        display_name="Trigger Confetti Blast",
        description="Launch confetti particles with customizable volume and color",
        parameters=[
            {
                "name": "volume",
                "type": "slider",
                "label": "Sound Volume",
                "min": 0,
                "max": 100,
                "step": 1,
                "default": 70,
                "optional": False
            },
            {
                "name": "color",
                "type": "color-picker",
                "label": "Confetti Color",
                "optional": True,
                "default": "#FF5733",
                "placeholder": "Leave empty for default color"
            }
        ]
    )
    async def trigger_blast(self, volume: int, color: str | None = None):
        """
        Trigger a confetti blast with sound.
        
        Args:
            volume: Sound volume level (0-100)
            color: Optional hex color code for confetti
        """
        # Use default color if not provided
        if not color:
            color = self.widget_parameters.get("default_color", "#FF5733")
        
        # Get elements with validation (confetti requires asset, sound is optional)
        confetti = self.get_element("confetti_particle", validate_asset=True)
        sound = self.get_element("pop_sound", validate_asset=False)
        
        # Update confetti element properties
        confetti.properties["color"] = color
        confetti.properties["particle_count"] = self.widget_parameters.get("particle_count", 100)
        confetti.visible = True
        
        # Play sound if configured and asset exists
        # Convert volume from 0-100 to 0.0-1.0 for audio element
        if sound.asset_path and self._validate_asset_path(sound.asset_path):
            sound.properties["volume"] = volume / 100.0
            sound.properties["autoplay"] = True
            sound.visible = True
        
        # Commit changes FIRST to ensure database consistency
        await self.db.commit()
        
        # Broadcast updates after commit
        await self.broadcast_element_update(confetti, action="show")
        
        if sound and sound.visible:
            await self.broadcast_element_update(sound, action="show")
    
    @feature(
        display_name="Stop Confetti",
        description="Immediately stop and hide all confetti",
        parameters=[]
    )
    async def stop_confetti(self):
        """
        Stop the confetti animation and audio immediately.
        
        This will hide all confetti elements and stop sound playback.
        """
        # Get elements (no asset validation needed for hiding)
        confetti = self.get_element("confetti_particle")
        sound = self.get_element("pop_sound")
        
        # Hide elements and stop audio
        confetti.visible = False
        sound.visible = False
        sound.properties["autoplay"] = False  # Prevent auto-replay
        
        # Commit changes FIRST
        await self.db.commit()
        
        # Broadcast updates after commit (hide action will stop audio in overlay)
        await self.broadcast_element_update(confetti, action="hide")
        await self.broadcast_element_update(sound, action="hide")
