"""Position calculation helper for widget layouts.

Provides utilities for calculating element positions in grid layouts
using relative coordinates (0-1 fractions of overlay dimensions).
"""

from math import ceil
from typing import List, Dict


def calculate_element_grid_positions(
    num_cards: int,
    total_width: float,
    total_height: float,
    vertical_spacing: float,
    horizontal_spacing: float,
    columns: int = 2
) -> List[Dict[str, float]]:
    """
    Calculate element positions for a grid layout.
    
    All parameters are relative fractions (0-1) of overlay dimensions.
    Spacing is defined as the gap between cards.
    
    Args:
        num_cards: Total number of elements to position (e.g., 10 cards)
        total_width: Total grid width as fraction of overlay (e.g., 0.8 = 80%)
        total_height: Total grid height as fraction of overlay (e.g., 0.9 = 90%)
        vertical_spacing: Space between rows as fraction of overlay height (e.g., 0.02 = 2%)
        horizontal_spacing: Space between columns as fraction of overlay width (e.g., 0.05 = 5%)
        columns: Number of columns in grid (default: 2)
    
    Returns:
        List of position dicts with x, y coordinates for each element.
        Positions are in top-left anchor format.
        
        Example output for 4 cards in 2 columns:
        [
            {"x": 0.0, "y": 0.0},    # Card 1 (col 0, row 0)
            {"x": 0.525, "y": 0.0},  # Card 2 (col 1, row 0)
            {"x": 0.0, "y": 0.27},   # Card 3 (col 0, row 1)
            {"x": 0.525, "y": 0.27}  # Card 4 (col 1, row 1)
        ]
    
    Raises:
        ValueError: If num_cards is negative or columns is non-positive
    
    Example:
        positions = calculate_element_grid_positions(
            num_cards=10,
            total_width=0.8,
            total_height=0.85,
            vertical_spacing=0.03,
            horizontal_spacing=0.05,
            columns=2
        )
        
        # Apply to cards
        for i, pos in enumerate(positions):
            card = widget.get_element(f"card_{i+1}")
            card.properties["position"] = {
                "x": pos["x"],
                "y": pos["y"],
                "anchor": "top-left"
            }
    """
    if num_cards < 0:
        raise ValueError("num_cards must be non-negative")
    
    if num_cards == 0:
        return []
    
    if columns <= 0:
        raise ValueError("columns must be positive")
    
    # Calculate number of rows needed
    rows = ceil(num_cards / columns)
    
    # Calculate individual card dimensions
    # Total width/height is divided into cards and gaps
    # gaps between columns = (columns - 1) * horizontal_spacing
    # gaps between rows = (rows - 1) * vertical_spacing
    available_width = total_width - (columns - 1) * horizontal_spacing
    available_height = total_height - (rows - 1) * vertical_spacing
    
    card_width = available_width / columns
    card_height = available_height / rows
    
    positions = []
    for index in range(num_cards):
        col = index % columns
        row = index // columns
        
        # Calculate top-left position of card
        # Cards start at (0, 0) and spacing is between them
        x = col * (card_width + horizontal_spacing)
        y = row * (card_height + vertical_spacing)
        
        positions.append({"x": x, "y": y})
    
    return positions


def calculate_centered_grid_positions(
    num_cards: int,
    card_width: float,
    card_height: float,
    vertical_spacing: float,
    horizontal_spacing: float,
    columns: int = 2
) -> List[Dict[str, float]]:
    """
    Calculate grid positions centered on the overlay.
    
    Useful when you know the exact card size and want the grid centered.
    
    Args:
        num_cards: Total number of elements
        card_width: Width of each card as fraction (e.g., 0.15)
        card_height: Height of each card as fraction (e.g., 0.2)
        vertical_spacing: Space between rows
        horizontal_spacing: Space between columns
        columns: Number of columns
    
    Returns:
        Centered grid positions
    
    Example:
        positions = calculate_centered_grid_positions(
            num_cards=10,
            card_width=0.15,
            card_height=0.2,
            vertical_spacing=0.03,
            horizontal_spacing=0.05,
            columns=2
        )
    """
    rows = ceil(num_cards / columns)
    
    # Calculate total grid dimensions (including spacing)
    total_width = columns * card_width + (columns - 1) * horizontal_spacing
    total_height = rows * card_height + (rows - 1) * vertical_spacing
    
    # Calculate total dimensions already includes spacing, so pass directly
    # The calculation will account for the spacing between cards
    return calculate_element_grid_positions(
        num_cards=num_cards,
        total_width=total_width,
        total_height=total_height,
        vertical_spacing=vertical_spacing,
        horizontal_spacing=horizontal_spacing,
        columns=columns
    )
