"""Entity types API routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from typing import Optional

from app.database import get_db
from app.models import EntityType, Entity
from app.schemas import (
    EntityTypeCreate, EntityTypeOut, EntityTypeTree,
)

router = APIRouter(prefix="/api/types", tags=["Entity Types"])


@router.get("", response_model=list[EntityTypeOut])
async def list_types(
    search: Optional[str] = Query(None, max_length=100),
    parent_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all entity types"""
    query = select(EntityType)

    if search:
        query = query.where(EntityType.name.ilike(f"%{search}%"))
    if parent_id is not None:
        if parent_id == 0:
            query = query.where(EntityType.parent_type_id.is_(None))
        else:
            query = query.where(EntityType.parent_type_id == parent_id)

    query = query.order_by(EntityType.name).offset(offset).limit(limit)
    result = await db.execute(query)
    types = result.scalars().all()
    return types


@router.get("/tree", response_model=list[EntityTypeTree])
async def get_type_tree(db: AsyncSession = Depends(get_db)):
    """Get the full entity type tree"""
    # Get all types
    result = await db.execute(select(EntityType).order_by(EntityType.name))
    all_types = result.scalars().all()

    # Count entities per type
    count_query = select(Entity.entity_type_id, func.count(Entity.id)).group_by(Entity.entity_type_id)
    count_result = await db.execute(count_query)
    counts = dict(count_result.all())

    # Build tree
    type_map: dict[int, EntityTypeTree] = {}
    root_types: list[EntityTypeTree] = []

    for t in all_types:
        tree_item = EntityTypeTree(
            id=t.id,
            name=t.name,
            description=t.description,
            emoji=t.emoji,
            parent_type_id=t.parent_type_id,
            is_verified=t.is_verified,
            absurdity_level=t.absurdity_level,
            created_at=t.created_at,
            entity_count=counts.get(t.id, 0),
            children=[],
        )
        type_map[t.id] = tree_item

    for t in all_types:
        item = type_map[t.id]
        if t.parent_type_id and t.parent_type_id in type_map:
            type_map[t.parent_type_id].children.append(item)
        else:
            root_types.append(item)

    return root_types


@router.get("/{type_id}", response_model=EntityTypeOut)
async def get_type(type_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific entity type"""
    result = await db.execute(select(EntityType).where(EntityType.id == type_id))
    entity_type = result.scalar_one_or_none()
    if not entity_type:
        raise HTTPException(status_code=404, detail="Entity type not found")
    return entity_type


@router.post("", response_model=EntityTypeOut, status_code=201)
async def create_type(
    data: EntityTypeCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new entity type"""
    # Check for duplicate
    result = await db.execute(select(EntityType).where(EntityType.name == data.name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Entity type already exists")

    # Check parent exists
    if data.parent_type_id:
        parent = await db.get(EntityType, data.parent_type_id)
        if not parent:
            raise HTTPException(status_code=404, detail="Parent type not found")

    entity_type = EntityType(**data.model_dump())
    db.add(entity_type)
    await db.flush()
    await db.refresh(entity_type)
    return entity_type


@router.put("/{type_id}", response_model=EntityTypeOut)
async def update_type(
    type_id: int,
    data: EntityTypeCreate,
    db: AsyncSession = Depends(get_db),
):
    """Update an entity type"""
    entity_type = await db.get(EntityType, type_id)
    if not entity_type:
        raise HTTPException(status_code=404, detail="Entity type not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(entity_type, key, value)

    await db.flush()
    await db.refresh(entity_type)
    return entity_type


@router.delete("/{type_id}", status_code=204)
async def delete_type(type_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an entity type"""
    entity_type = await db.get(EntityType, type_id)
    if not entity_type:
        raise HTTPException(status_code=404, detail="Entity type not found")
    await db.delete(entity_type)
