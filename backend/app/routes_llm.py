"""LLM-powered endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.database import get_db
from app.models import EntityType, Entity, EntityTag
from app.schemas import LLMEntityAnalysis, LLMResponse
from app.llm_client import get_llm_client
from app.llm_prompts import (
    process_entity_prompt,
    suggest_type_prompt,
    summarize_entity_prompt,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/llm", tags=["LLM"])


@router.post("/analyze-entity", response_model=LLMResponse)
async def analyze_entity(
    data: LLMEntityAnalysis,
    db: AsyncSession = Depends(get_db),
):
    """Analyze a new entity name/description using LLM"""
    try:
        # Get context
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
            {
                "id": e.id,
                "name": e.name,
                "type_name": e.entity_type.name if e.entity_type else "Unknown",
            }
            for e in existing_entities_raw.scalars().all()
        ]

        messages = process_entity_prompt(
            name=data.user_input_raw,
            type_name=data.type_name,
            description=data.description,
            existing_types=existing_types,
            existing_entities=existing_entities,
        )

        llm = get_llm_client()
        result = await llm.chat_json(messages)
        return LLMResponse(**result)
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"LLM analysis failed: {str(e)}")


@router.post("/suggest-type")
async def suggest_type(
    name: str,
    description: str = "",
    db: AsyncSession = Depends(get_db),
):
    """Get LLM suggestions for a new entity type"""
    try:
        existing_types_raw = await db.execute(
            select(EntityType).order_by(EntityType.name).limit(100)
        )
        existing_types = [
            {"id": t.id, "name": t.name, "emoji": t.emoji, "description": t.description}
            for t in existing_types_raw.scalars().all()
        ]

        messages = suggest_type_prompt(
            raw_type_name=name,
            description=description or None,
            existing_types=existing_types,
        )

        llm = get_llm_client()
        result = await llm.chat_json(messages)
        return result
    except Exception as e:
        logger.error(f"LLM type suggestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"LLM suggestion failed: {str(e)}")


@router.post("/summarize-entity/{entity_id}")
async def summarize_entity(
    entity_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Generate an AI summary for an entity"""
    try:
        entity = await db.get(Entity, entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")

        # Get ratings
        from app.models import Rating
        ratings_raw = await db.execute(
            select(Rating).where(Rating.entity_id == entity_id).limit(50)
        )
        ratings = ratings_raw.scalars().all()

        entity_data = {
            "name": entity.name,
            "entity_type_name": entity.entity_type.name if entity.entity_type else "Unknown",
            "description": entity.description or "",
            "metadata": entity.entity_metadata or {},
        }
        rating_data = [{"score": r.score, "review": r.review or ""} for r in ratings]

        messages = summarize_entity_prompt(entity_data, rating_data)
        llm = get_llm_client()
        summary = await llm.chat(messages, temperature=0.7)
        return {"summary": summary.strip()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LLM summarization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")
