from app.database import Base
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, UniqueConstraint, Index, JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class EntityType(Base):
    __tablename__ = "entity_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    emoji = Column(String(10), nullable=True)
    parent_type_id = Column(Integer, ForeignKey("entity_types.id"), nullable=True)
    is_verified = Column(Boolean, default=False)
    absurdity_level = Column(Float, default=0.0)  # 0.0 = sérieux, 1.0 = délire
    icon_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    parent = relationship("EntityType", remote_side=[id], backref="children", lazy="selectin")

    def __repr__(self):
        return f"<EntityType {self.emoji or ''} {self.name}>"


class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(500), nullable=False, index=True)
    entity_type_id = Column(Integer, ForeignKey("entity_types.id"), nullable=False, index=True)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    created_by = Column(Integer, nullable=True)  # user_id
    entity_metadata = Column("entity_metadata", JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    entity_type = relationship("EntityType", lazy="selectin")
    ratings = relationship("Rating", back_populates="entity", lazy="selectin",
                           cascade="all, delete-orphan")

    # Relations source/target
    source_links = relationship("EntityLink", foreign_keys="EntityLink.source_entity_id",
                                back_populates="source_entity", lazy="selectin",
                                cascade="all, delete-orphan")
    target_links = relationship("EntityLink", foreign_keys="EntityLink.target_entity_id",
                                back_populates="target_entity", lazy="selectin",
                                cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Entity {self.name}>"


class RelationType(Base):
    __tablename__ = "relation_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)  # "a_pour_coiffure"
    reverse_name = Column(String(100), nullable=True)  # "est_la_coiffure_de"
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # "apparence", "musique", "lieu"...
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<RelationType {self.name}>"


class EntityLink(Base):
    __tablename__ = "entity_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    target_entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    relation_type_id = Column(Integer, ForeignKey("relation_types.id"), nullable=False)
    link_metadata = Column("link_metadata", JSON, nullable=True, default=dict)
    confidence = Column(Float, default=1.0)  # 0.0 to 1.0
    auto_generated = Column(Boolean, default=False)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    source_entity = relationship("Entity", foreign_keys=[source_entity_id],
                                 back_populates="source_links", lazy="selectin")
    target_entity = relationship("Entity", foreign_keys=[target_entity_id],
                                 back_populates="target_links", lazy="selectin")
    relation_type = relationship("RelationType", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("source_entity_id", "target_entity_id", "relation_type_id",
                         name="uq_entity_link"),
    )

    def __repr__(self):
        return f"<EntityLink {self.source_entity_id} -{self.relation_type.name}→ {self.target_entity_id}>"


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    score = Column(Float, nullable=False)  # 0.0 to 10.0
    review = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True, default=list)
    has_spoiler = Column(Boolean, default=False)
    is_re_rate = Column(Boolean, default=False)  # True if re-rating
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    entity = relationship("Entity", back_populates="ratings", lazy="selectin")

    __table_args__ = (
        Index("idx_rating_user_entity", "user_id", "entity_id"),
    )

    def __repr__(self):
        return f"<Rating user={self.user_id} entity={self.entity_id} score={self.score}>"


class EntityMetadataSchema(Base):
    """Defines available metadata properties for each entity type"""
    __tablename__ = "entity_metadata_schemas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type_id = Column(Integer, ForeignKey("entity_types.id"), nullable=False, index=True)
    property_name = Column(String(100), nullable=False)
    property_type = Column(String(50), nullable=False)  # "date", "text", "number", "location", "nationality", "url", "image", "entity_link"
    is_required = Column(Boolean, default=False)
    is_searchable = Column(Boolean, default=True)
    is_facet = Column(Boolean, default=False)
    ui_hint = Column(String(255), nullable=True)
    allowed_values = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("entity_type_id", "property_name", name="uq_metadata_schema"),
    )


class EntityMetadata(Base):
    """Actual metadata values for entities"""
    __tablename__ = "entity_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    property_name = Column(String(100), nullable=False)
    property_type = Column(String(50), nullable=False)
    value = Column(Text, nullable=False)
    value_normalized = Column(String(500), nullable=True)
    confidence = Column(Float, default=1.0)
    source = Column(String(50), default="user_input")
    validated_by_user = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_entity_metadata_lookup", "entity_id", "property_name"),
    )


class EntityTag(Base):
    """Free tags on entities for search/filter"""
    __tablename__ = "entity_tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    tag = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("entity_id", "tag", name="uq_entity_tag"),
    )


class User(Base):
    """User with authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    display_name = Column(String(200), nullable=True)
    password_hash = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

