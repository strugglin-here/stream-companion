"""Element service for business operations.

Unified service layer used by both API endpoints and widget methods.
Orchestrates repository operations but does NOT commit transactions.
"""

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.repositories.element_repository import ElementRepository
from app.repositories.media_repository import MediaRepository
from app.models.element import Element


class ElementService:
    """Service for element business operations."""
    
    @staticmethod
    async def assign_media(
        element_id: int,
        media_id: int,
        role: str,
        db: AsyncSession,
        replace_existing: bool = True
    ) -> Element:
        """Assign media to an element with role validation.
        
        Unified media assignment operation used by both API and widgets.
        
        Process:
        1. Load element and media (with eager loading)
        2. Validate role against element schema
        3. Clear existing role assignment (if replace_existing)
        4. Create new ElementAsset
        5. Return updated element
        
        Does NOT commit - caller controls transaction.
        
        Args:
            element_id: Element ID
            media_id: Media ID to assign
            role: Role for the media (e.g., "image", "sound")
            db: Database session
            replace_existing: If True, clear existing media for this role
            
        Returns:
            Updated element (not yet committed)
            
        Raises:
            HTTPException: If element or media not found
            ValueError: If role is invalid for element
        """
        # Load element with media relationships
        element = await ElementRepository.get_by_id(element_id, db)
        if not element:
            raise HTTPException(status_code=404, detail=f"Element {element_id} not found")
        
        # Validate media exists
        media = await MediaRepository.get_by_id(media_id, db)
        if not media:
            raise HTTPException(status_code=404, detail=f"Media {media_id} not found")
        
        # Validate role against element schema
        await ElementRepository.validate_media_role(element, role)
        
        # Clear existing role assignment if requested
        if replace_existing:
            await ElementRepository.clear_element_role(element, role)
        
        # Create new assignment
        new_asset = await ElementRepository.create_element_asset(
            element_id=element_id,
            media_id=media_id,
            role=role,
            db=db
        )
        
        # Add to element's relationships
        element.media_assets.append(new_asset)
        
        return element
    
    @staticmethod
    async def assign_multiple_media(
        element_id: int,
        media_assignments: List[Dict[str, Any]],
        db: AsyncSession
    ) -> Element:
        """Assign multiple media to an element at once.
        
        Used by API endpoints that update multiple roles simultaneously.
        
        Args:
            element_id: Element ID
            media_assignments: List of {"media_id": int, "role": str} dicts
            db: Database session
            
        Returns:
            Updated element (not yet committed)
            
        Raises:
            HTTPException: If element or any media not found
            ValueError: If any role is invalid
        """
        # Load element once
        element = await ElementRepository.get_by_id(element_id, db)
        if not element:
            raise HTTPException(status_code=404, detail=f"Element {element_id} not found")
        
        # Validate all roles first (fail fast)
        for assignment in media_assignments:
            role = assignment.get('role', 'default')
            await ElementRepository.validate_media_role(element, role)
        
        # Collect roles being updated
        updated_roles = {assignment.get('role', 'default') for assignment in media_assignments}
        
        # Clear all roles being updated
        element.media_assets = [
            asset for asset in element.media_assets
            if asset.role not in updated_roles
        ]
        
        # Add new assignments
        for assignment in media_assignments:
            media_id = assignment['media_id']
            role = assignment.get('role', 'default')
            
            # Validate media exists
            media = await MediaRepository.get_by_id(media_id, db)
            if not media:
                raise HTTPException(status_code=404, detail=f"Media {media_id} not found")
            
            # Create new asset
            new_asset = await ElementRepository.create_element_asset(
                element_id=element_id,
                media_id=media_id,
                role=role,
                db=db
            )
            element.media_assets.append(new_asset)
        
        return element
