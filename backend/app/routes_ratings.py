"""Ratings API routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional

from app.database import get_db
from app.models import Rating, Entity
from app.schemas import RatingCreate, RatingUpdate, RatingOut

router = APIRouter(prefix="/api/ratings", tags=["Ratings"])


@router.get("", response_model=list[RatingOut])
async def list_ratings(
    entity_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    sort: str = Query("newest", pattern="^(newest|oldest|highest|lowest)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List ratings with filters"""
    query = select(Rating).options(selectinload(Rating.entity).selectinload(Entity.entity_type))

    if entity_id:
        query = query.where(Rating.entity_id == entity_id)
    if user_id:
        query = query.where(Rating.user_id == user_id)

    if sort == "newest":
        query = query.order_by(Rating.created_at.desc())
    elif sort == "oldest":
        query = query.order_by(Rating.created_at)
    elif sort == "highest":
        query = query.order_by(Rating.score.desc())
    elif sort == "lowest":
        query = query.order_by(Rating.score)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats/{entity_id}")
async def get_rating_stats(entity_id: int, db: AsyncSession = Depends(get_db)):
    """Get detailed rating stats for an entity"""
    result = await db.execute(
        select(
            func.avg(Rating.score).label("avg"),
            func.count(Rating.id).label("count"),
            func.min(Rating.score).label("min"),
            func.max(Rating.score).label("max"),
        ).where(Rating.entity_id == entity_id)
    )
    stats = result.one()

    return {
        "avg": round(float(stats.avg), 2) if stats.avg else None,
        "count": stats.count or 0,
        "min": float(stats.min) if stats.min else None,
        "max": float(stats.max) if stats.max else None,
    }


@router.post("", response_model=RatingOut, status_code=201)
async def create_rating(
    data: RatingCreate,
    user_id: int = Query(1),  # TODO: real auth
    db: AsyncSession = Depends(get_db),
):
    """Create a rating"""
    # Check entity exists
    entity = await db.get(Entity, data.entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # Check existing rating
    existing = await db.execute(
        select(Rating).where(
            Rating.user_id == user_id,
            Rating.entity_id == data.entity_id,
        )
    )
    existing_rating = existing.scalar_one_or_none()
    if existing_rating:
        # Re-rating: mark old one as re-rate
        existing_rating.is_re_rate = True

    rating = Rating(
        user_id=user_id,
        entity_id=data.entity_id,
        score=data.score,
        review=data.review,
        tags=data.tags or [],
        has_spoiler=data.has_spoiler,
    )
    db.add(rating)
    await db.flush()
    await db.refresh(rating)

    # Load entity for response
    rating.entity = entity
    return rating


@router.put("/{rating_id}", response_model=RatingOut)
async def update_rating(
    rating_id: int,
    data: RatingUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a rating"""
    rating = await db.get(Rating, rating_id)
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rating, key, value)

    await db.flush()
    await db.refresh(rating)
    return rating


@router.delete("/{rating_id}", status_code=204)
async def delete_rating(rating_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a rating"""
    rating = await db.get(Rating, rating_id)
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    await db.delete(rating)
