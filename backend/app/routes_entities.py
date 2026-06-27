"""Entities API routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional

from app.database import get_db
from app.models import Entity, EntityType, EntityTag, EntityMetadata, Rating
from app.schemas import EntityCreate, EntityUpdate, EntityOut
from app.llm_client import get_llm_client
from app.llm_prompts import process_entity_prompt

router = APIRouter(prefix="/api/entities", tags=["Entities"])


@router.get("", response_model=list[EntityOut])
async def list_entities(
    type_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None, max_length=100),
    sort: str = Query("newest", pattern="^(newest|oldest|top|trending)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List entities with optional filters"""
    query = select(Entity)

    if type_id:
        query = query.where(Entity.entity_type_id == type_id)
    if search:
        query = query.where(Entity.name.ilike(f"%{search}%"))

    # Sorting
    if sort == "newest":
        query = query.order_by(Entity.created_at.desc())
    elif sort == "oldest":
        query = query.order_by(Entity.created_at)
    elif sort == "top":
        # Subquery for avg rating
        avg_subq = (
            select(Rating.entity_id, func.avg(Rating.score).label("avg_score"))
            .group_by(Rating.entity_id)
            .subquery()
        )
        query = query.outerjoin(avg_subq, Entity.id == avg_subq.c.entity_id)
        query = query.order_by(avg_subq.c.avg_score.desc().nullslast())
    elif sort == "trending":
        query = query.order_by(Entity.updated_at.desc())

    query = query.options(selectinload(Entity.entity_type)).offset(offset).limit(limit)
    result = await db.execute(query)
    entities = result.scalars().all()

    # Enrich with rating stats
    enriched = []
    for entity in entities:
        rating_stats = await _get_rating_stats(db, entity.id)
        enriched.append(EntityOut(
            id=entity.id,
            name=entity.name,
            entity_type_id=entity.entity_type_id,
            entity_type=entity.entity_type,
            description=entity.description,
            image_url=entity.image_url,
            metadata=entity.entity_metadata,
            avg_rating=rating_stats["avg"],
            rating_count=rating_stats["count"],
            created_at=entity.created_at,
        ))
    return enriched


@router.get("/search", response_model=list[EntityOut])
async def search_entities(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Full-text search entities"""
    query = (
        select(Entity)
        .where(Entity.name.ilike(f"%{q}%"))
        .options(selectinload(Entity.entity_type))
        .order_by(Entity.name)
        .limit(limit)
    )
    result = await db.execute(query)
    entities = result.scalars().all()

    enriched = []
    for entity in entities:
        rating_stats = await _get_rating_stats(db, entity.id)
        enriched.append(EntityOut(
            id=entity.id,
            name=entity.name,
            entity_type_id=entity.entity_type_id,
            entity_type=entity.entity_type,
            description=entity.description,
            image_url=entity.image_url,
            metadata=entity.entity_metadata,
            avg_rating=rating_stats["avg"],
            rating_count=rating_stats["count"],
            created_at=entity.created_at,
        ))
    return enriched


@router.get("/trending", response_model=list[EntityOut])
async def trending_entities(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get trending entities (most rated recently)"""
    # Entities with most ratings in last 7 days
    seven_days_ago = func.datetime("now", "-7 days")

    recent_ratings = (
        select(Rating.entity_id, func.count(Rating.id).label("recent_count"))
        .where(Rating.created_at >= seven_days_ago)
        .group_by(Rating.entity_id)
        .order_by(func.count(Rating.id).desc())
        .limit(limit)
        .subquery()
    )

    query = (
        select(Entity)
        .join(recent_ratings, Entity.id == recent_ratings.c.entity_id)
        .options(selectinload(Entity.entity_type))
        .order_by(recent_ratings.c.recent_count.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    entities = result.scalars().all()

    enriched = []
    for entity in entities:
        rating_stats = await _get_rating_stats(db, entity.id)
        enriched.append(EntityOut(
            id=entity.id,
            name=entity.name,
            entity_type_id=entity.entity_type_id,
            entity_type=entity.entity_type,
            description=entity.description,
            image_url=entity.image_url,
            metadata=entity.entity_metadata,
            avg_rating=rating_stats["avg"],
            rating_count=rating_stats["count"],
            created_at=entity.created_at,
        ))
    return enriched


@router.get("/random", response_model=EntityOut)
async def random_entity(db: AsyncSession = Depends(get_db)):
    """Get a random entity"""
    result = await db.execute(
        select(Entity)
        .options(selectinload(Entity.entity_type))
        .order_by(func.random())
        .limit(1)
    )
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail="No entities found")

    rating_stats = await _get_rating_stats(db, entity.id)
    return EntityOut(
        id=entity.id,
        name=entity.name,
        entity_type_id=entity.entity_type_id,
        entity_type=entity.entity_type,
        description=entity.description,
        image_url=entity.image_url,
        metadata=entity.entity_metadata,
        avg_rating=rating_stats["avg"],
        rating_count=rating_stats["count"],
        created_at=entity.created_at,
    )


@router.get("/{entity_id}", response_model=EntityOut)
async def get_entity(entity_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific entity"""
    result = await db.execute(
        select(Entity)
        .options(selectinload(Entity.entity_type))
        .where(Entity.id == entity_id)
    )
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    rating_stats = await _get_rating_stats(db, entity.id)
    return EntityOut(
        id=entity.id,
        name=entity.name,
        entity_type_id=entity.entity_type_id,
        entity_type=entity.entity_type,
        description=entity.description,
        image_url=entity.image_url,
        metadata=entity.entity_metadata,
        avg_rating=rating_stats["avg"],
        rating_count=rating_stats["count"],
        created_at=entity.created_at,
    )


@router.post("", response_model=EntityOut, status_code=201)
async def create_entity(
    data: EntityCreate,
    user_id: int = Query(1),  # TODO: real auth
    db: AsyncSession = Depends(get_db),
):
    """Create a new entity"""
    # Check type exists
    entity_type = await db.get(EntityType, data.entity_type_id)
    if not entity_type:
        raise HTTPException(status_code=404, detail="Entity type not found")

    entity = Entity(
        name=data.name,
        entity_type_id=data.entity_type_id,
        description=data.description,
        entity_metadata=data.metadata or {},
        created_by=user_id,
    )
    db.add(entity)
    await db.flush()

    # Add tags
    if data.tags:
        for tag_name in data.tags:
            db.add(EntityTag(entity_id=entity.id, tag=tag_name.lower().strip()))

    # Try LLM enrichment (async, non-blocking)
    try:
        llm = get_llm_client()
        existing_types_raw = await db.execute(
            select(EntityType).order_by(EntityType.name).limit(100)
        )
        existing_types = [
            {"id": t.id, "name": t.name, "emoji": t.emoji}
            for t in existing_types_raw.scalars().all()
        ]
        existing_entities_raw = await db.execute(
            select(Entity).order_by(Entity.created_at.desc()).limit(50)
        )
        existing_entities = [
            {"id": e.id, "name": e.name, "type_name": e.entity_type.name if e.entity_type else ""}
            for e in existing_entities_raw.scalars().all()
        ]

        messages = process_entity_prompt(
            name=data.name,
            type_name=entity_type.name,
            description=data.description,
            existing_types=existing_types,
            existing_entities=existing_entities,
        )
        llm_result = await llm.chat_json(messages)

        # Apply LLM suggestions
        if llm_result.get("entity_name_normalized") and llm_result["confidence_name"] > 0.8:
            entity.name = llm_result["entity_name_normalized"]

        if llm_result.get("metadata"):
            existing_meta = entity.entity_metadata or {}
            for key, val in llm_result["metadata"].items():
                if isinstance(val, dict) and "value" in val:
                    existing_meta[key] = val["value"]
            entity.entity_metadata = existing_meta

        if llm_result.get("tags"):
            for tag_name in llm_result["tags"]:
                # Check duplicate
                dup_check = await db.execute(
                    select(EntityTag).where(
                        EntityTag.entity_id == entity.id,
                        EntityTag.tag == tag_name.lower().strip(),
                    )
                )
                if not dup_check.scalar_one_or_none():
                    db.add(EntityTag(entity_id=entity.id, tag=tag_name.lower().strip()))

    except Exception as e:
        # LLM error shouldn't break entity creation
        import logging
        logging.getLogger(__name__).warning(f"LLM enrichment failed for entity {entity.id}: {e}")

    await db.flush()
    await db.refresh(entity)

    rating_stats = await _get_rating_stats(db, entity.id)
    return EntityOut(
        id=entity.id,
        name=entity.name,
        entity_type_id=entity.entity_type_id,
        entity_type=entity_type,
        description=entity.description,
        image_url=entity.image_url,
        metadata=entity.entity_metadata,
        avg_rating=rating_stats["avg"],
        rating_count=rating_stats["count"],
        created_at=entity.created_at,
    )


@router.put("/{entity_id}", response_model=EntityOut)
async def update_entity(
    entity_id: int,
    data: EntityUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an entity"""
    entity = await db.get(Entity, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    if data.name is not None:
        entity.name = data.name
    if data.description is not None:
        entity.description = data.description
    if data.metadata is not None:
        entity.entity_metadata = {**(entity.metadata or {}), **data.metadata}

    await db.flush()
    await db.refresh(entity)

    rating_stats = await _get_rating_stats(db, entity.id)
    return EntityOut(
        id=entity.id,
        name=entity.name,
        entity_type_id=entity.entity_type_id,
        entity_type=entity.entity_type,
        description=entity.description,
        image_url=entity.image_url,
        metadata=entity.entity_metadata,
        avg_rating=rating_stats["avg"],
        rating_count=rating_stats["count"],
        created_at=entity.created_at,
    )


@router.delete("/{entity_id}", status_code=204)
async def delete_entity(entity_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an entity"""
    entity = await db.get(Entity, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    await db.delete(entity)


async def _get_rating_stats(db: AsyncSession, entity_id: int) -> dict:
    """Get rating statistics for an entity"""
    result = await db.execute(
        select(
            func.avg(Rating.score).label("avg"),
            func.count(Rating.id).label("count"),
        ).where(Rating.entity_id == entity_id)
    )
    row = result.one()
    return {
        "avg": round(float(row.avg), 2) if row.avg else None,
        "count": row.count if row.count else 0,
    }
