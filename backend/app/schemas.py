from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any
from datetime import datetime


# ─── Entity Types ─────────────────────────────────────────────

class EntityTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    emoji: Optional[str] = None
    parent_type_id: Optional[int] = None
    absurdity_level: float = 0.0


class EntityTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    emoji: Optional[str] = None
    parent_type_id: Optional[int] = None
    is_verified: bool = False
    absurdity_level: float = 0.0
    created_at: datetime | None = None


class EntityTypeTree(EntityTypeOut):
    children: list["EntityTypeTree"] = []
    entity_count: int = 0


# ─── Entities ─────────────────────────────────────────────────

class EntityCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    entity_type_id: int
    description: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    tags: Optional[list[str]] = None


class EntityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class EntityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    name: str
    entity_type_id: int
    entity_type: Optional[EntityTypeOut] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    metadata: Optional[dict[str, Any]] = Field(None, alias="entity_metadata")
    avg_rating: Optional[float] = None
    rating_count: int = 0
    created_at: datetime | None = None


# ─── Relations ────────────────────────────────────────────────

class RelationTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    reverse_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None


class RelationTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    reverse_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None


class EntityLinkCreate(BaseModel):
    source_entity_id: int
    target_entity_id: int
    relation_type_id: int
    metadata: Optional[dict[str, Any]] = None


class EntityLinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    source_entity_id: int
    target_entity_id: int
    relation_type_id: int
    relation_type: Optional[RelationTypeOut] = None
    source_entity: Optional[EntityOut] = None
    target_entity: Optional[EntityOut] = None
    metadata: Optional[dict[str, Any]] = Field(None, alias="link_metadata")
    confidence: float = 1.0
    auto_generated: bool = False


# ─── Ratings ──────────────────────────────────────────────────

class RatingCreate(BaseModel):
    entity_id: int
    score: float = Field(..., ge=0, le=10)
    review: Optional[str] = None
    tags: Optional[list[str]] = None
    has_spoiler: bool = False


class RatingUpdate(BaseModel):
    score: Optional[float] = Field(None, ge=0, le=10)
    review: Optional[str] = None
    tags: Optional[list[str]] = None
    has_spoiler: Optional[bool] = None


class RatingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    entity_id: int
    entity: Optional[EntityOut] = None
    score: float
    review: Optional[str] = None
    tags: Optional[list] = None
    has_spoiler: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ─── Metadata ─────────────────────────────────────────────────

class MetadataSchemaCreate(BaseModel):
    entity_type_id: int
    property_name: str
    property_type: str = "text"
    is_required: bool = False
    is_searchable: bool = True
    is_facet: bool = False
    ui_hint: Optional[str] = None
    allowed_values: Optional[list[str]] = None
    description: Optional[str] = None


class MetadataSchemaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_type_id: int
    property_name: str
    property_type: str
    is_required: bool = False
    is_searchable: bool = True
    is_facet: bool = False
    ui_hint: Optional[str] = None
    allowed_values: Optional[list] = None


# ─── LLM ──────────────────────────────────────────────────────

class LLMEntityAnalysis(BaseModel):
    entity_name: str
    type_name: Optional[str] = None
    description: Optional[str] = None
    user_input_raw: str


class LLMRelationSuggestion(BaseModel):
    target_entity_name: str
    target_type_name: Optional[str] = None
    relation_type_name: str
    confidence: float
    reason: str


class LLMResponse(BaseModel):
    entity_name_normalized: str = ""
    confidence_name: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)
    relations: list[LLMRelationSuggestion] = Field(default_factory=list)
    suggested_new_entities: list[dict] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    type_suggestions: Optional[dict[str, Any]] = None


# ─── Charts ───────────────────────────────────────────────────

class ChartDataPoint(BaseModel):
    label: str = ""
    value: float = 0.0
    extra: Optional[dict[str, Any]] = None


class ChartDataset(BaseModel):
    label: str = ""
    data: list[float] = Field(default_factory=list)
    borderColor: Optional[str] = None
    backgroundColor: Optional[str] = None


class ChartConfig(BaseModel):
    chart_type: str = "bar"
    title: str = ""
    labels: list[str] = Field(default_factory=list)
    datasets: list[ChartDataset] = Field(default_factory=list)
    data: Optional[list[dict]] = None


class EntityCharts(BaseModel):
    rating_distribution: Optional[ChartConfig] = None
    rating_over_time: Optional[ChartConfig] = None
    comparative_radar: Optional[ChartConfig] = None
    metadata_breakdown: Optional[dict[str, ChartConfig]] = None


class TypeCharts(BaseModel):
    top_entities: Optional[ChartConfig] = None
    metadata_breakdown: Optional[dict[str, ChartConfig]] = None
    timeline: Optional[ChartConfig] = None
    correlation: Optional[ChartConfig] = None


# ─── Search & Trending ────────────────────────────────────────

class TrendingResult(BaseModel):
    entity_id: int
    entity_name: str
    entity_type_name: str
    avg_rating: float = 0.0
    rating_count: int = 0
    trend_score: float = 0.0
