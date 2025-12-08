"""Media repository for data access operations."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.media import Media


class MediaRepository:
    """Repository for Media data access."""
    
    @staticmethod
    async def get_by_id(
        media_id: int,
        db: AsyncSession
    ) -> Optional[Media]:
        """Get media by ID.
        
        Args:
            media_id: Media ID
            db: Database session
            
        Returns:
            Media or None if not found
        """
        result = await db.execute(
            select(Media).where(Media.id == media_id)
        )
        return result.scalar_one_or_none()
