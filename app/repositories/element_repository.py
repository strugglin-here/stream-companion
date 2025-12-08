"""Element repository for data access operations.

Provides CRUD operations with automatic eager loading of media relationships.
Validates entity constraints (role validation) but does not contain business logic.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.element import Element
from app.models.element_asset import ElementAsset
from app.models.media import Media


class ElementRepository:
    """Repository for Element data access with automatic eager loading."""
    
    @staticmethod
    def _with_eager_loading(query):
        """Apply standard eager loading for elements.
        
        Always loads media_assets and their nested media objects to prevent
        greenlet_spawn errors and ensure snappy performance.
        """
        return query.options(
            selectinload(Element.media_assets).selectinload(ElementAsset.media)
        )
    
    @staticmethod
    async def get_by_id(
        element_id: int,
        db: AsyncSession
    ) -> Optional[Element]:
        """Get element by ID with all relationships loaded.
        
        Args:
            element_id: Element ID
            db: Database session
            
        Returns:
            Element with media_assets and media loaded, or None if not found
        """
        query = select(Element).where(Element.id == element_id)
        query = ElementRepository._with_eager_loading(query)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_by_widget(
        widget_id: int,
        db: AsyncSession
    ) -> List[Element]:
        """Get all elements for a widget with relationships loaded.
        
        Args:
            widget_id: Widget ID
            db: Database session
            
        Returns:
            List of elements with media_assets and media loaded
        """
        query = select(Element).where(Element.widget_id == widget_id)
        query = ElementRepository._with_eager_loading(query)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def validate_media_role(
        element: Element,
        role: str
    ) -> None:
        """Validate that a role is allowed for an element.
        
        Entity-level validation - checks if role exists in element's schema.
        
        Args:
            element: Element to validate against
            role: Role to validate
            
        Raises:
            ValueError: If role is not in element's media_roles
        """
        allowed_roles = element.properties.get('media_roles', []) if element.properties else []
        
        if allowed_roles and role not in allowed_roles:
            raise ValueError(
                f"Invalid role '{role}' for element '{element.name}'. "
                f"Allowed roles: {', '.join(allowed_roles)}"
            )
    
    @staticmethod
    async def create_element_asset(
        element_id: int,
        media_id: int,
        role: str,
        db: AsyncSession
    ) -> ElementAsset:
        """Create a new ElementAsset (media assignment).
        
        Does NOT commit - caller controls transaction.
        Does NOT validate role - call validate_media_role first.
        
        Args:
            element_id: Element ID
            media_id: Media ID
            role: Asset role
            db: Database session
            
        Returns:
            Created ElementAsset (not yet committed)
        """
        asset = ElementAsset(
            element_id=element_id,
            media_id=media_id,
            role=role
        )
        db.add(asset)
        return asset
    
    @staticmethod
    async def clear_element_role(
        element: Element,
        role: str
    ) -> None:
        """Remove all media assets for a specific role.
        
        Modifies element.media_assets in place.
        Does NOT commit - caller controls transaction.
        
        Args:
            element: Element to modify
            role: Role to clear
        """
        element.media_assets = [
            asset for asset in element.media_assets
            if asset.role != role
        ]
