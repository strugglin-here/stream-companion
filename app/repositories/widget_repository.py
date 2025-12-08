"""Widget repository for data access operations."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.widget import Widget


class WidgetRepository:
    """Repository for Widget data access."""
    
    @staticmethod
    async def get_by_id(
        widget_id: int,
        db: AsyncSession
    ) -> Optional[Widget]:
        """Get widget by ID.
        
        Args:
            widget_id: Widget ID
            db: Database session
            
        Returns:
            Widget or None if not found
        """
        result = await db.execute(
            select(Widget).where(Widget.id == widget_id)
        )
        return result.scalar_one_or_none()
