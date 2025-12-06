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
            enabled=True,
            visible=False
        )
        
        # Pop sound effect
        pop_sound = Element(
            widget_id=self.db_widget.id,
            element_type=ElementType.AUDIO,
            name="pop_sound",
            asset_path=None,  # User will configure
            properties={
                "volume": 0.7
            },
            behavior={},
            enabled=True,
            visible=False
        )
        
        self.db.add(confetti_particle)
        self.db.add(pop_sound)
        await self.db.commit()
    
    @feature(
        display_name="Trigger Confetti Blast",
        description="Launch confetti particles with customizable intensity and color",
        parameters=[
            {
                "name": "intensity",
                "type": "dropdown",
                "label": "Intensity Level",
                "options": ["Low", "Medium", "High"],
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
    async def trigger_blast(self, intensity: str, color: str | None = None):
        """
        Trigger a confetti blast.
        
        Args:
            intensity: Intensity level (Low, Medium, High)
            color: Optional hex color code for confetti
        """
        # Use default color if not provided
        if not color:
            color = self.widget_parameters.get("default_color", "#FF5733")
        
        # Get elements
        confetti = self.elements.get("confetti_particle")
        sound = self.elements.get("pop_sound")
        
        if not confetti:
            raise ValueError("Confetti particle element not found")
        
        # Adjust particle properties based on intensity
        particle_count = self.widget_parameters.get("particle_count", 100)
        
        if intensity == "Low":
            particle_count = int(particle_count * 0.5)
        elif intensity == "High":
            particle_count = int(particle_count * 1.5)
        
        # Update confetti element properties
        confetti.properties["color"] = color
        confetti.properties["particle_count"] = particle_count
        confetti.visible = True
        
        # Broadcast confetti update
        await self.broadcast_element_update(confetti, action="show")
        
        # Play sound if configured
        if sound and sound.asset_path:
            sound.visible = True
            await self.broadcast_element_update(sound, action="show")
        
        # Commit changes
        await self.db.commit()
        
        return {
            "intensity": intensity,
            "color": color,
            "particle_count": particle_count
        }
    
    @feature(
        display_name="Stop Confetti",
        description="Immediately stop and hide all confetti",
        parameters=[]
    )
    async def stop_confetti(self):
        """
        Stop the confetti animation immediately.
        
        This will hide all confetti elements.
        """
        # Get elements
        confetti = self.elements.get("confetti_particle")
        sound = self.elements.get("pop_sound")
        
        # Hide confetti
        if confetti:
            confetti.visible = False
            await self.broadcast_element_update(confetti, action="hide")
        
        # Stop sound
        if sound:
            sound.visible = False
            await self.broadcast_element_update(sound, action="hide")
        
        # Commit changes
        await self.db.commit()
        
        return {"status": "stopped"}
