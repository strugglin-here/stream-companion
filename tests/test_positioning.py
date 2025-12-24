"""Tests for positioning system and property validation."""

import pytest
from app.widgets.position_helper import calculate_element_grid_positions, calculate_centered_grid_positions
from app.services.element_service import validate_element_properties
from app.models.element import ElementType


class TestGridPositionCalculation:
    """Test grid position calculations."""
    
    def test_calculate_grid_10_cards_2_columns(self):
        """Test calculating positions for 10 cards in 2 columns."""
        positions = calculate_element_grid_positions(
            num_cards=10,
            total_width=0.8,
            total_height=0.85,
            vertical_spacing=0.03,
            horizontal_spacing=0.05,
            columns=2
        )
        
        assert len(positions) == 10
        
        # First card should be at origin (0, 0)
        assert positions[0]["x"] == pytest.approx(0.0)
        assert positions[0]["y"] == pytest.approx(0.0)
        
        # Second card in same row (col 1)
        assert positions[1]["x"] > positions[0]["x"]
        assert positions[1]["y"] == positions[0]["y"]
        
        # Third card in second row (col 0)
        assert positions[2]["x"] == positions[0]["x"]
        assert positions[2]["y"] > positions[1]["y"]
        
        # Fourth card in second row (col 1)
        assert positions[3]["x"] == positions[1]["x"]
        assert positions[3]["y"] == positions[2]["y"]
    
    def test_grid_calculation_spacing(self):
        """Test that spacing is correctly applied."""
        positions = calculate_element_grid_positions(
            num_cards=4,
            total_width=1.0,
            total_height=1.0,
            vertical_spacing=0.1,
            horizontal_spacing=0.1,
            columns=2
        )
        
        # With 2 columns, 1 spacing between them
        # Available width = 1.0 - 1*0.1 = 0.9
        # Card width = 0.9 / 2 = 0.45
        # Card positions: 0, 0.45+0.1=0.55
        
        assert positions[0]["x"] == pytest.approx(0.0)
        assert positions[1]["x"] == pytest.approx(0.55)
        
        # Same for height
        assert positions[0]["y"] == pytest.approx(0.0)
        assert positions[2]["y"] == pytest.approx(0.55)
    
    def test_grid_empty(self):
        """Test with 0 cards."""
        positions = calculate_element_grid_positions(
            num_cards=0,
            total_width=0.8,
            total_height=0.85,
            vertical_spacing=0.03,
            horizontal_spacing=0.05,
            columns=2
        )
        
        assert len(positions) == 0
    
    def test_grid_single_card(self):
        """Test with single card."""
        positions = calculate_element_grid_positions(
            num_cards=1,
            total_width=0.8,
            total_height=0.85,
            vertical_spacing=0.03,
            horizontal_spacing=0.05,
            columns=2
        )
        
        assert len(positions) == 1
        assert positions[0]["x"] == pytest.approx(0.0)
        assert positions[0]["y"] == pytest.approx(0.0)
    
    def test_grid_invalid_negative_cards(self):
        """Test that negative card count raises error."""
        with pytest.raises(ValueError):
            calculate_element_grid_positions(
                num_cards=-1,
                total_width=0.8,
                total_height=0.85,
                vertical_spacing=0.03,
                horizontal_spacing=0.05,
                columns=2
            )
    
    def test_grid_invalid_columns(self):
        """Test that invalid column count raises error."""
        with pytest.raises(ValueError):
            calculate_element_grid_positions(
                num_cards=10,
                total_width=0.8,
                total_height=0.85,
                vertical_spacing=0.03,
                horizontal_spacing=0.05,
                columns=0
            )
    
    def test_centered_grid_positions(self):
        """Test centered grid calculation."""
        positions = calculate_centered_grid_positions(
            num_cards=4,
            card_width=0.2,
            card_height=0.25,
            vertical_spacing=0.05,
            horizontal_spacing=0.05,
            columns=2
        )
        
        # 2 columns, 1 gap: total_width = 2*0.2 + 1*0.05 = 0.45
        # 2 rows, 1 gap: total_height = 2*0.25 + 1*0.05 = 0.55
        # Centered: start at (0.275, 0.225)
        # But function returns positions relative to (0, 0), not centered
        # So positions should still start at (0, 0)
        
        assert len(positions) == 4


class TestPropertyValidation:
    """Test property validation."""
    
    def test_valid_image_properties(self):
        """Test valid image element properties."""
        props = {
            "position": {"x": 0.5, "y": 0.5, "anchor": "center"},
            "size": {"width": 0.25, "height": 0.3},
            "opacity": 0.8,
            "z_index": 10
        }
        
        is_valid, errors = validate_element_properties(ElementType.IMAGE, props)
        assert is_valid
        assert len(errors) == 0
    
    def test_invalid_position_out_of_range(self):
        """Test position with values out of 0-1 range."""
        props = {
            "position": {"x": 1.5, "y": 0.5}
        }
        
        is_valid, errors = validate_element_properties(ElementType.IMAGE, props)
        assert not is_valid
        assert any("between 0 and 1" in e for e in errors)
    
    def test_invalid_position_missing_x(self):
        """Test position missing x coordinate."""
        props = {
            "position": {"y": 0.5}
        }
        
        is_valid, errors = validate_element_properties(ElementType.IMAGE, props)
        assert not is_valid
        assert any("x is required" in e for e in errors)
    
    def test_invalid_position_missing_y(self):
        """Test position missing y coordinate."""
        props = {
            "position": {"x": 0.5}
        }
        
        is_valid, errors = validate_element_properties(ElementType.IMAGE, props)
        assert not is_valid
        assert any("y is required" in e for e in errors)
    
    def test_invalid_anchor(self):
        """Test invalid anchor value."""
        props = {
            "position": {"x": 0.5, "y": 0.5, "anchor": "invalid"}
        }
        
        is_valid, errors = validate_element_properties(ElementType.IMAGE, props)
        assert not is_valid
        assert any("anchor must be one of" in e for e in errors)
    
    def test_valid_anchors(self):
        """Test all valid anchor values."""
        anchors = [
            "top-left", "top-center", "top-right",
            "center-left", "center", "center-right",
            "bottom-left", "bottom-center", "bottom-right"
        ]
        
        for anchor in anchors:
            props = {
                "position": {"x": 0.5, "y": 0.5, "anchor": anchor}
            }
            is_valid, errors = validate_element_properties(ElementType.IMAGE, props)
            assert is_valid, f"Anchor {anchor} should be valid"
    
    def test_invalid_opacity(self):
        """Test opacity outside 0-1 range."""
        props = {
            "opacity": 1.5
        }
        
        is_valid, errors = validate_element_properties(ElementType.IMAGE, props)
        assert not is_valid
        assert any("opacity" in e for e in errors)
    
    def test_invalid_size(self):
        """Test size with invalid values."""
        props = {
            "size": {"width": 1.5, "height": 0.3}
        }
        
        is_valid, errors = validate_element_properties(ElementType.IMAGE, props)
        assert not is_valid
        assert any("width" in e for e in errors)
    
    def test_size_auto_height(self):
        """Test size with auto height."""
        props = {
            "size": {"width": 0.25, "height": "auto"},
            "aspect_ratio": 1.777
        }
        
        is_valid, errors = validate_element_properties(ElementType.IMAGE, props)
        assert is_valid
    
    def test_card_properties_valid(self):
        """Test valid CARD element properties."""
        props = {
            "position": {"x": 0.1, "y": 0.1},
            "size": {"width": 0.15, "height": 0.2},
            "revealed": False,
            "front_text": "?",
            "back_text": "ANSWER",
            "z_index": 10
        }
        
        is_valid, errors = validate_element_properties(ElementType.CARD, props)
        assert is_valid
    
    def test_card_revealed_invalid_type(self):
        """Test CARD with invalid revealed type."""
        props = {
            "revealed": "yes"  # Should be boolean
        }
        
        is_valid, errors = validate_element_properties(ElementType.CARD, props)
        assert not is_valid
        assert any("revealed must be boolean" in e for e in errors)
    
    def test_audio_no_position_required(self):
        """Test AUDIO element (no position required)."""
        props = {
            "volume": 0.7,
            "autoplay": False
        }
        
        is_valid, errors = validate_element_properties(ElementType.AUDIO, props)
        assert is_valid
    
    def test_audio_invalid_property(self):
        """Test AUDIO with invalid property."""
        props = {
            "volume": 0.7,
            "position": {"x": 0.5, "y": 0.5}  # Not allowed for AUDIO
        }
        
        is_valid, errors = validate_element_properties(ElementType.AUDIO, props)
        assert not is_valid
        assert any("position" in e and "not allowed" in e for e in errors)
    
    def test_unknown_property_rejected(self):
        """Test that unknown properties are rejected (strict validation)."""
        props = {
            "position": {"x": 0.5, "y": 0.5},
            "invalid_property": "value"
        }
        
        is_valid, errors = validate_element_properties(ElementType.IMAGE, props)
        assert not is_valid
        assert any("invalid_property" in e for e in errors)
    
    def test_scale_positive_required(self):
        """Test that scale must be positive."""
        props = {
            "scale_x": 0  # Must be > 0
        }
        
        is_valid, errors = validate_element_properties(ElementType.IMAGE, props)
        assert not is_valid
        assert any("scale_x" in e for e in errors)


class TestBaseWidgetPropertyUpdates:
    """Test BaseWidget property update methods with validation."""
    
    @pytest.mark.asyncio
    async def test_update_element_properties_valid(self, mock_widget, mock_element):
        """Test updating element properties with valid data."""
        mock_element.element_type = ElementType.IMAGE
        mock_widget.elements = {"test_image": mock_element}
        
        # Update with valid properties (using correct position object structure)
        await mock_widget.update_element_properties("test_image", {
            "position": {"x": 0.5, "y": 0.3},
            "opacity": 0.8
        })
        
        # Verify properties updated
        assert mock_element.properties["position"]["x"] == 0.5
        assert mock_element.properties["position"]["y"] == 0.3
        assert mock_element.properties["opacity"] == 0.8
    
    @pytest.mark.asyncio
    async def test_update_element_properties_card_revealed(self, mock_widget, mock_element):
        """Test updating CARD element with revealed flag."""
        mock_element.element_type = ElementType.CARD
        mock_widget.elements = {"my_card": mock_element}
        
        # Update card properties
        await mock_widget.update_element_properties("my_card", {
            "revealed": True,
            "position": {"x": 0.4, "y": 0.5}
        })
        
        assert mock_element.properties["revealed"] is True
        assert mock_element.properties["position"]["x"] == 0.4
        assert mock_element.properties["position"]["y"] == 0.5
    
    @pytest.mark.asyncio
    async def test_update_element_properties_invalid_properties(self, mock_widget, mock_element):
        """Test that invalid properties raise ValueError."""
        mock_element.element_type = ElementType.IMAGE
        mock_widget.elements = {"test_image": mock_element}
        
        # Try to update with invalid opacity
        with pytest.raises(ValueError, match="Invalid properties"):
            await mock_widget.update_element_properties("test_image", {
                "opacity": 1.5  # Out of range
            })
    
    @pytest.mark.asyncio
    async def test_update_element_properties_unknown_property(self, mock_widget, mock_element):
        """Test that unknown properties are rejected."""
        mock_element.element_type = ElementType.IMAGE
        mock_widget.elements = {"test_image": mock_element}
        
        # Try to update with unknown property
        with pytest.raises(ValueError, match="Invalid properties"):
            await mock_widget.update_element_properties("test_image", {
                "position": {"x": 0.5, "y": 0.5},
                "invalid_prop": "value"
            })
    
    @pytest.mark.asyncio
    async def test_update_element_properties_element_not_found(self, mock_widget):
        """Test that updating non-existent element raises ValueError."""
        mock_widget.elements = {}
        
        with pytest.raises(ValueError, match="Element .* not found"):
            await mock_widget.update_element_properties("nonexistent", {
                "position": {"x": 0.5, "y": 0.5}
            })
    
    @pytest.mark.asyncio
    async def test_update_element_properties_multiple_fields(self, mock_widget, mock_element):
        """Test updating multiple properties at once."""
        mock_element.element_type = ElementType.CARD
        mock_widget.elements = {"card": mock_element}
        
        # Update multiple properties
        await mock_widget.update_element_properties("card", {
            "position": {"x": 0.1, "y": 0.2},
            "size": {"width": 0.15, "height": 0.2},
            "scale_x": 1.5,
            "scale_y": 1.5,
            "opacity": 0.9,
            "z_index": 50,
            "revealed": False
        })
        
        assert mock_element.properties["position"]["x"] == 0.1
        assert mock_element.properties["position"]["y"] == 0.2
        assert mock_element.properties["size"]["width"] == 0.15
        assert mock_element.properties["size"]["height"] == 0.2
        assert mock_element.properties["scale_x"] == 1.5
        assert mock_element.properties["scale_y"] == 1.5
        assert mock_element.properties["opacity"] == 0.9
        assert mock_element.properties["z_index"] == 50
        assert mock_element.properties["revealed"] is False


# Test fixtures for BaseWidget tests
@pytest.fixture
def mock_element():
    """Create a mock element for testing."""
    from app.models.element import Element
    
    element = Element(
        id=1,
        widget_id=1,
        name="test_element",
        element_type=ElementType.IMAGE,
        properties={},
        behavior=[],
        playing=False,
        media_assets=[]
    )
    return element


@pytest.fixture
def mock_widget(mock_element):
    """Create a mock widget for testing."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.widget import Widget
    from app.widgets.base import BaseWidget
    from unittest.mock import AsyncMock, MagicMock
    
    # Create a concrete subclass of BaseWidget for testing
    class TestWidget(BaseWidget):
        widget_class = "TestWidget"
        display_name = "Test Widget"
        description = "Widget for testing"
        
        @classmethod
        def get_default_parameters(cls):
            return {}
        
        async def create_default_elements(self):
            pass
    
    # Create mock session
    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.commit = AsyncMock()
    
    # Create mock widget record
    mock_widget_record = MagicMock(spec=Widget)
    mock_widget_record.id = 1
    mock_widget_record.name = "TestWidget"
    mock_widget_record.widget_parameters = {}
    
    # Create widget instance
    widget = TestWidget(mock_db, mock_widget_record)
    
    return widget

