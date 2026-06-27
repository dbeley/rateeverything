"""Tests for RateEverything API - Async with aiosqlite"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, event

from app.main import app
from app.database import Base, get_db
from app.models import EntityType, Entity, RelationType, Rating, EntityLink

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Enable WAL mode and foreign keys for SQLite
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    """Create test client with overridden DB dependency"""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_entity_type(client):
    response = await client.post(
        "/api/types",
        json={"name": "Album", "description": "A musical album", "emoji": "💿"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Album"
    assert data["emoji"] == "💿"

    response = await client.get("/api/types")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_create_entity(client):
    response = await client.post("/api/types", json={"name": "Morceau", "emoji": "🎵"})
    type_id = response.json()["id"]

    response = await client.post(
        "/api/entities",
        json={
            "name": "Not Like Us",
            "entity_type_id": type_id,
            "description": "Kendrick Lamar diss track",
            "tags": ["kendrick", "rap", "2024"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Not Like Us"
    assert data["entity_type_id"] == type_id


@pytest.mark.asyncio
async def test_create_rating(client):
    await client.post("/api/types", json={"name": "Film", "emoji": "🎬"})
    type_resp = await client.post("/api/types", json={"name": "Morceau", "emoji": "🎵"})
    type_id = type_resp.json()["id"]

    entity_resp = await client.post(
        "/api/entities", json={"name": "Humble", "entity_type_id": type_id}
    )
    entity_id = entity_resp.json()["id"]

    response = await client.post(
        "/api/ratings",
        json={"entity_id": entity_id, "score": 8.5, "review": "Excellent track"},
        params={"user_id": 1},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["score"] == 8.5
    assert data["entity_id"] == entity_id

    response = await client.get(f"/api/ratings/stats/{entity_id}")
    assert response.status_code == 200
    stats = response.json()
    assert stats["count"] == 1
    assert stats["avg"] == 8.5


@pytest.mark.asyncio
async def test_create_relation(client):
    await client.post("/api/types", json={"name": "Artiste", "emoji": "🎤"})
    type_resp = await client.post("/api/types", json={"name": "Coiffure", "emoji": "💇"})
    type_id = type_resp.json()["id"]

    artist_resp = await client.post(
        "/api/entities", json={"name": "Kendrick Lamar", "entity_type_id": type_id}
    )
    artist_id = artist_resp.json()["id"]

    haircut_resp = await client.post(
        "/api/entities",
        json={"name": "La coupe de Kendrick dans Not Like Us", "entity_type_id": type_id},
    )
    haircut_id = haircut_resp.json()["id"]

    rel_resp = await client.post(
        "/api/relations/types",
        json={"name": "a_pour_coiffure", "reverse_name": "est_la_coiffure_de", "category": "apparence"},
    )
    rel_type_id = rel_resp.json()["id"]

    response = await client.post(
        "/api/relations/links",
        json={
            "source_entity_id": artist_id,
            "target_entity_id": haircut_id,
            "relation_type_id": rel_type_id,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["source_entity_id"] == artist_id
    assert data["target_entity_id"] == haircut_id


@pytest.mark.asyncio
async def test_search_entities(client):
    await client.post("/api/types", json={"name": "Jeu vidéo", "emoji": "🎮"})
    type_resp = await client.post("/api/types", json={"name": "Morceau", "emoji": "🎵"})
    type_id = type_resp.json()["id"]

    await client.post("/api/entities", json={"name": "DNA", "entity_type_id": type_id})
    await client.post("/api/entities", json={"name": "LOYALTY", "entity_type_id": type_id})

    response = await client.get("/api/entities/search?q=DNA")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(e["name"] == "DNA" for e in data)


@pytest.mark.asyncio
async def test_type_tree(client):
    parent_resp = await client.post("/api/types", json={"name": "Musique", "emoji": "🎵"})
    parent_id = parent_resp.json()["id"]

    await client.post(
        "/api/types",
        json={"name": "Morceau de rap", "emoji": "🎤", "parent_type_id": parent_id},
    )

    response = await client.get("/api/types/tree")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_entity_charts(client):
    await client.post("/api/types", json={"name": "Livre", "emoji": "📚"})
    type_resp = await client.post("/api/types", json={"name": "Album", "emoji": "💿"})
    type_id = type_resp.json()["id"]

    entity_resp = await client.post(
        "/api/entities", json={"name": "DAMN.", "entity_type_id": type_id}
    )
    entity_id = entity_resp.json()["id"]

    await client.post(
        "/api/ratings", json={"entity_id": entity_id, "score": 9.0}, params={"user_id": 1}
    )

    response = await client.get(f"/api/charts/entity/{entity_id}")
    assert response.status_code == 200
    data = response.json()
    assert "rating_distribution" in data
    assert data["rating_distribution"]["chart_type"] == "bar"


@pytest.mark.asyncio
async def test_dashboard_charts(client):
    response = await client.get("/api/charts/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "quick_stats" in data
    assert "most_active_types" in data


@pytest.mark.asyncio
async def test_large_score_range(client):
    type_resp = await client.post("/api/types", json={"name": "Morceau", "emoji": "🎵"})
    type_id = type_resp.json()["id"]

    entity_resp = await client.post(
        "/api/entities", json={"name": "Test Track", "entity_type_id": type_id}
    )
    entity_id = entity_resp.json()["id"]

    response = await client.post(
        "/api/ratings", json={"entity_id": entity_id, "score": 11.0}, params={"user_id": 1}
    )
    assert response.status_code == 422

    response = await client.post(
        "/api/ratings", json={"entity_id": entity_id, "score": -1.0}, params={"user_id": 1}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_random_entity(client):
    # First create an entity so random works
    type_resp = await client.post("/api/types", json={"name": "Test", "emoji": "🧪"})
    type_id = type_resp.json()["id"]
    await client.post("/api/entities", json={"name": "Test Entity", "entity_type_id": type_id})

    response = await client.get("/api/entities/random")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data


@pytest.mark.asyncio
async def test_entity_graph(client):
    type_resp = await client.post("/api/types", json={"name": "Objet", "emoji": "📦"})
    type_id = type_resp.json()["id"]

    e1 = await client.post("/api/entities", json={"name": "Test A", "entity_type_id": type_id})
    e2 = await client.post("/api/entities", json={"name": "Test B", "entity_type_id": type_id})
    e1_id = e1.json()["id"]

    rel_resp = await client.post("/api/relations/types", json={"name": "est_lie_a"})
    rel_type_id = rel_resp.json()["id"]

    await client.post("/api/relations/links", json={
        "source_entity_id": e1_id,
        "target_entity_id": e2.json()["id"],
        "relation_type_id": rel_type_id,
    })

    response = await client.get(f"/api/relations/graph/{e1_id}")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) >= 2
