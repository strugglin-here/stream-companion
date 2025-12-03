"""API routes for Element CRUD operations"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.models.element import Element, ElementType
from app.schemas.element import (
    ElementCreate,
    ElementUpdate,
    ElementResponse,
    ElementList
)

router = APIRouter(prefix="/elements", tags=["elements"])


@router.post("/", response_model=ElementResponse, status_code=201)
async def create_element(
    element_data: ElementCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new element.
    
    - **name**: Unique element name
    - **element_type**: Type of element (image, video, text, etc.)
    - **description**: Optional description
    - **asset_path**: Optional path to media asset
    - **enabled**: Whether element is enabled (default: true)
    - **visible**: Whether element is visible (default: false)
    - **properties**: Display properties as JSON dict
    - **behavior**: Animation/interaction behavior as JSON dict
    """
    # Check if name already exists
    result = await db.execute(
        select(Element).where(Element.name == element_data.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Element with name '{element_data.name}' already exists")
    
    # Create new element
    element = Element(**element_data.model_dump())
    db.add(element)
    await db.commit()
    await db.refresh(element)
    
    return element


@router.get("/", response_model=ElementList)
async def list_elements(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    element_type: Optional[ElementType] = Query(None, description="Filter by element type"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    visible: Optional[bool] = Query(None, description="Filter by visible status"),
    db: AsyncSession = Depends(get_db)
):
    """
    List elements with pagination and optional filters.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 50, max: 100)
    - **element_type**: Filter by type
    - **enabled**: Filter by enabled status
    - **visible**: Filter by visible status
    """
    # Build query with filters
    query = select(Element)
    
    if element_type:
        query = query.where(Element.element_type == element_type)
    if enabled is not None:
        query = query.where(Element.enabled == enabled)
    if visible is not None:
        query = query.where(Element.visible == visible)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Element.created_at.desc())
    
    # Execute query
    result = await db.execute(query)
    elements = result.scalars().all()
    
    return ElementList(
        items=[ElementResponse.model_validate(element) for element in elements],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{element_id}", response_model=ElementResponse)
async def get_element(
    element_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a single element by ID."""
    result = await db.execute(
        select(Element).where(Element.id == element_id)
    )
    element = result.scalar_one_or_none()
    
    if not element:
        raise HTTPException(status_code=404, detail=f"Element with id {element_id} not found")
    
    return element


@router.patch("/{element_id}", response_model=ElementResponse)
async def update_element(
    element_id: int,
    element_data: ElementUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an element (partial update).
    
    Only provided fields will be updated. Omitted fields remain unchanged.
    """
    # Get existing element
    result = await db.execute(
        select(Element).where(Element.id == element_id)
    )
    element = result.scalar_one_or_none()
    
    if not element:
        raise HTTPException(status_code=404, detail=f"Element with id {element_id} not found")
    
    # Check if new name conflicts with existing element
    update_data = element_data.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] != element.name:
        result = await db.execute(
            select(Element).where(Element.name == update_data["name"])
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Element with name '{update_data['name']}' already exists")
    
    # Update fields
    for field, value in update_data.items():
        setattr(element, field, value)
    
    await db.commit()
    await db.refresh(element)
    
    return element


@router.delete("/{element_id}", status_code=204)
async def delete_element(
    element_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an element by ID."""
    result = await db.execute(
        select(Element).where(Element.id == element_id)
    )
    element = result.scalar_one_or_none()
    
    if not element:
        raise HTTPException(status_code=404, detail=f"Element with id {element_id} not found")
    
    await db.delete(element)
    await db.commit()
    
    return  # 204 No Content
