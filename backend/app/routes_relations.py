"""Relations API routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from typing import Optional

from app.database import get_db
from app.models import EntityLink, RelationType, Entity
from app.schemas import (
    EntityLinkCreate, EntityLinkOut,
    RelationTypeCreate, RelationTypeOut,
)

router = APIRouter(prefix="/api/relations", tags=["Relations"])


# ─── Relation Types ──────────────────────────────────────────

@router.get("/types", response_model=list[RelationTypeOut])
async def list_relation_types(db: AsyncSession = Depends(get_db)):
    """List all relation types"""
    result = await db.execute(select(RelationType).order_by(RelationType.name))
    return result.scalars().all()


@router.post("/types", response_model=RelationTypeOut, status_code=201)
async def create_relation_type(
    data: RelationTypeCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new relation type"""
    dup = await db.execute(select(RelationType).where(RelationType.name == data.name))
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Relation type already exists")

    rel_type = RelationType(**data.model_dump())
    db.add(rel_type)
    await db.flush()
    await db.refresh(rel_type)
    return rel_type


# ─── Entity Links ────────────────────────────────────────────

@router.get("", response_model=list[EntityLinkOut])
async def list_links(
    entity_id: Optional[int] = Query(None),
    relation_type_id: Optional[int] = Query(None),
    depth: int = Query(1, ge=1, le=2),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List entity links, optionally filtered by entity or relation type"""
    query = select(EntityLink).options(
        selectinload(EntityLink.relation_type),
        selectinload(EntityLink.source_entity).selectinload(Entity.entity_type),
        selectinload(EntityLink.target_entity).selectinload(Entity.entity_type),
    )

    if entity_id:
        if depth == 1:
            query = query.where(
                or_(
                    EntityLink.source_entity_id == entity_id,
                    EntityLink.target_entity_id == entity_id,
                )
            )
        # depth=2 handled separately
    if relation_type_id:
        query = query.where(EntityLink.relation_type_id == relation_type_id)

    query = query.order_by(EntityLink.created_at.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/graph/{entity_id}")
async def get_entity_graph(
    entity_id: int,
    depth: int = Query(1, ge=1, le=2),
    db: AsyncSession = Depends(get_db),
):
    """Get the full relation graph for an entity (for D3/vis-network visualization)"""
    links = await db.execute(
        select(EntityLink).options(
            selectinload(EntityLink.relation_type),
            selectinload(EntityLink.source_entity).selectinload(Entity.entity_type),
            selectinload(EntityLink.target_entity).selectinload(Entity.entity_type),
        ).where(
            or_(
                EntityLink.source_entity_id == entity_id,
                EntityLink.target_entity_id == entity_id,
            )
        ).limit(100)
    )
    entity_links = links.scalars().all()

    nodes = {}
    edges = []
    added_ids = {entity_id}

    # Add the main entity
    main_entity = await db.get(Entity, entity_id)
    if not main_entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    nodes[entity_id] = {
        "id": entity_id,
        "name": main_entity.name,
        "type": main_entity.entity_type.name if main_entity.entity_type else "Unknown",
        "is_center": True,
    }

    for link in entity_links:
        source_id = link.source_entity_id
        target_id = link.target_entity_id

        for eid, ent in [(source_id, link.source_entity), (target_id, link.target_entity)]:
            if eid not in added_ids:
                nodes[eid] = {
                    "id": eid,
                    "name": ent.name if ent else f"Entity {eid}",
                    "type": ent.entity_type.name if ent and ent.entity_type else "Unknown",
                    "is_center": False,
                }
                added_ids.add(eid)

        edges.append({
            "source": source_id,
            "target": target_id,
            "relation": link.relation_type.name if link.relation_type else "related",
            "reverse_relation": link.relation_type.reverse_name if link.relation_type else None,
            "confidence": link.confidence,
            "auto_generated": link.auto_generated,
        })

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
    }


@router.post("/links", response_model=EntityLinkOut, status_code=201)
async def create_link(
    data: EntityLinkCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a link between entities"""
    # Check entities exist
    source = await db.get(Entity, data.source_entity_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source entity not found")
    target = await db.get(Entity, data.target_entity_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target entity not found")

    # Check relation type exists
    rel_type = await db.get(RelationType, data.relation_type_id)
    if not rel_type:
        raise HTTPException(status_code=404, detail="Relation type not found")

    link = EntityLink(
        source_entity_id=data.source_entity_id,
        target_entity_id=data.target_entity_id,
        relation_type_id=data.relation_type_id,
        link_metadata=data.metadata or {},
    )
    db.add(link)
    await db.flush()
    await db.refresh(link)
    link.relation_type = rel_type
    return link


@router.delete("/links/{link_id}", status_code=204)
async def delete_link(link_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a link"""
    link = await db.get(EntityLink, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    await db.delete(link)
