"""Charts data generation endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text as sa_text, Date
from typing import Optional

from app.database import get_db
from app.models import Entity, EntityType, Rating, EntityMetadata, EntityLink
from app.schemas import ChartConfig, ChartDataset, EntityCharts, TypeCharts

router = APIRouter(prefix="/api/charts", tags=["Charts"])


@router.get("/entity/{entity_id}", response_model=EntityCharts)
async def get_entity_charts(
    entity_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all chart data for an entity page"""
    entity = await db.get(Entity, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # Rating distribution
    dist_result = await db.execute(
        select(Rating.score, func.count(Rating.id))
        .where(Rating.entity_id == entity_id)
        .group_by(Rating.score)
        .order_by(Rating.score)
    )
    distribution = dict(dist_result.all())

    # Build distribution chart with bins 0-10
    labels = [str(i) for i in range(11)]
    dist_data = [distribution.get(float(i), 0) for i in range(11)]

    rating_distribution = ChartConfig(
        chart_type="bar",
        title="Distribution des notes",
        labels=labels,
        datasets=[
            ChartDataset(
                label="Nombre de notes",
                data=[float(d) for d in dist_data],
                backgroundColor="rgba(99, 102, 241, 0.7)",
                borderColor="rgba(99, 102, 241, 1)",
            )
        ],
    )

    # Rating over time (last 30 days)
    time_result = await db.execute(
        select(
            func.date_trunc(sa_text("'day'"), Rating.created_at).label("day"),
            func.avg(Rating.score).label("avg_score"),
            func.count(Rating.id).label("count"),
        )
        .where(
            Rating.entity_id == entity_id,
            Rating.created_at >= sa_text("NOW() - INTERVAL '30 days'"),
        )
        .group_by(func.date_trunc(sa_text("'day'"), Rating.created_at))
        .order_by(func.date_trunc(sa_text("'day'"), Rating.created_at))
    )
    time_rows = time_result.all()
    time_labels = [str(row.day)[:10] for row in time_rows] if time_rows else []
    time_data = [float(row.avg_score) for row in time_rows] if time_rows else []

    rating_over_time = ChartConfig(
        chart_type="line",
        title="Évolution de la note moyenne (30 jours)",
        labels=time_labels,
        datasets=[
            ChartDataset(
                label="Note moyenne",
                data=time_data,
                borderColor="rgba(34, 197, 94, 1)",
                backgroundColor="rgba(34, 197, 94, 0.1)",
            )
        ],
    )

    # Metadata breakdown charts
    metadata_breakdown = {}
    if entity.entity_metadata:
        for key, val in entity.entity_metadata.items():
            if isinstance(val, (str, int, float)):
                metadata_breakdown[key] = ChartConfig(
                    chart_type="bar",
                    title=key.replace("_", " ").title(),
                    labels=[str(val)],
                    datasets=[
                        ChartDataset(
                            label=key,
                            data=[1],
                        )
                    ],
                )

    return EntityCharts(
        rating_distribution=rating_distribution,
        rating_over_time=rating_over_time if time_labels else None,
        metadata_breakdown=metadata_breakdown if metadata_breakdown else None,
    )


@router.get("/type/{type_id}", response_model=TypeCharts)
async def get_type_charts(
    type_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get chart data for a type page"""
    entity_type = await db.get(EntityType, type_id)
    if not entity_type:
        raise HTTPException(status_code=404, detail="Type not found")

    # Top entities
    top_result = await db.execute(
        select(
            Entity.id,
            Entity.name,
            func.avg(Rating.score).label("avg_score"),
            func.count(Rating.id).label("count"),
        )
        .join(Rating, Entity.id == Rating.entity_id)
        .where(Entity.entity_type_id == type_id)
        .group_by(Entity.id, Entity.name)
        .having(func.count(Rating.id) >= 1)
        .order_by(func.avg(Rating.score).desc())
        .limit(10)
    )
    top_rows = top_result.all()

    top_entities = ChartConfig(
        chart_type="bar",
        title=f"Top 10 {entity_type.name}",
        labels=[row.name[:30] for row in top_rows],
        datasets=[
            ChartDataset(
                label="Note moyenne",
                data=[float(row.avg_score) for row in top_rows],
                backgroundColor="rgba(251, 191, 36, 0.7)",
                borderColor="rgba(251, 191, 36, 1)",
            )
        ],
    )

    # Timeline (entities created over time)
    timeline_result = await db.execute(
        select(
            func.date_trunc(sa_text("'week'"), Entity.created_at).label("week"),
            func.count(Entity.id).label("count"),
        )
        .where(Entity.entity_type_id == type_id)
        .group_by(func.date_trunc(sa_text("'week'"), Entity.created_at))
        .order_by(func.date_trunc(sa_text("'week'"), Entity.created_at))
        .limit(52)
    )
    timeline_rows = timeline_result.all()
    timeline_labels = [str(row.week)[:10] for row in timeline_rows]
    timeline_data = [float(row.count) for row in timeline_rows]

    timeline = ChartConfig(
        chart_type="line",
        title="Création d'entités par semaine",
        labels=timeline_labels,
        datasets=[
            ChartDataset(
                label="Nouvelles entités",
                data=timeline_data,
                borderColor="rgba(139, 92, 246, 1)",
                backgroundColor="rgba(139, 92, 246, 0.1)",
            )
        ],
    )

    # Metadata breakdown
    metadata_breakdown = {}
    meta_result = await db.execute(
        select(
            EntityMetadata.property_name,
            EntityMetadata.value,
            func.count(EntityMetadata.id).label("count"),
        )
        .join(Entity, EntityMetadata.entity_id == Entity.id)
        .where(Entity.entity_type_id == type_id)
        .group_by(EntityMetadata.property_name, EntityMetadata.value)
        .order_by(EntityMetadata.property_name, func.count(EntityMetadata.id).desc())
        .limit(50)
    )
    meta_rows = meta_result.all()

    # Group by property name
    meta_groups: dict[str, dict[str, int]] = {}
    for row in meta_rows:
        if row.property_name not in meta_groups:
            meta_groups[row.property_name] = {}
        meta_groups[row.property_name][row.value or "N/A"] = row.count

    for prop_name, values in meta_groups.items():
        items = sorted(values.items(), key=lambda x: x[1], reverse=True)[:10]
        metadata_breakdown[prop_name] = ChartConfig(
            chart_type="pie",
            title=prop_name.replace("_", " ").title(),
            labels=[v[0] for v in items],
            datasets=[
                ChartDataset(
                    label=prop_name,
                    data=[float(v[1]) for v in items],
                )
            ],
        )

    return TypeCharts(
        top_entities=top_entities,
        timeline=timeline if timeline_labels else None,
        metadata_breakdown=metadata_breakdown if metadata_breakdown else None,
    )


@router.get("/dashboard")
async def get_dashboard_charts(db: AsyncSession = Depends(get_db)):
    """Get charts for the main dashboard"""
    # Most active types
    type_activity = await db.execute(
        select(
            EntityType.id,
            EntityType.name,
            EntityType.emoji,
            func.count(Rating.id).label("rating_count"),
        )
        .join(Entity, EntityType.id == Entity.entity_type_id)
        .join(Rating, Entity.id == Rating.entity_id)
        .group_by(EntityType.id, EntityType.name, EntityType.emoji)
        .order_by(func.count(Rating.id).desc())
        .limit(10)
    )
    active_types = type_activity.all()

    return {
        "most_active_types": [
            {
                "id": t.id,
                "name": t.name,
                "emoji": t.emoji,
                "rating_count": t.rating_count,
            }
            for t in active_types
        ],
        "quick_stats": await _get_quick_stats(db),
    }


async def _get_quick_stats(db: AsyncSession) -> dict:
    """Get quick statistics for the dashboard"""
    entity_count = await db.execute(select(func.count(Entity.id)))
    type_count = await db.execute(select(func.count(EntityType.id)))
    rating_count = await db.execute(select(func.count(Rating.id)))

    return {
        "total_entities": entity_count.scalar() or 0,
        "total_types": type_count.scalar() or 0,
        "total_ratings": rating_count.scalar() or 0,
    }
