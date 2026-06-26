"""
Comprehensive test suite for the LLM Council backend.
Tests: health check, auth endpoints, mode switching, adapter logic, debate graph structure.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock
import json
import asyncio

# Import the FastAPI app and modules
from server import app
from adapter import HybridLLMAdapter
from database import Base, engine, SessionLocal, User
from auth import get_password_hash, verify_password, create_access_token

# ─── Fixtures ───────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client():
    """Create an async test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def clean_db():
    """Ensure clean database state for auth tests."""
    db = SessionLocal()
    try:
        db.query(User).filter(User.username == "testuser_unit").delete()
        db.commit()
    finally:
        db.close()
    yield
    db = SessionLocal()
    try:
        db.query(User).filter(User.username == "testuser_unit").delete()
        db.commit()
    finally:
        db.close()

# ─── 1. Health Check ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check(client):
    """Health endpoint returns status and current mode."""
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "online"
    assert data["mode"] in ["cloud", "local"]

# ─── 2. Mode Switching ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_set_mode_cloud(client):
    """Switch to cloud mode."""
    resp = await client.post("/api/mode", json={"mode": "cloud"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "cloud"

@pytest.mark.asyncio
async def test_set_mode_local(client):
    """Switch to local mode."""
    resp = await client.post("/api/mode", json={"mode": "local"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "local"

@pytest.mark.asyncio
async def test_set_mode_invalid(client):
    """Invalid mode returns 400."""
    resp = await client.post("/api/mode", json={"mode": "invalid"})
    assert resp.status_code == 400

# ─── 3. Auth: Registration ──────────────────────────────────────

@pytest.mark.asyncio
async def test_register_user(client, clean_db):
    """Register a new user."""
    resp = await client.post("/api/auth/register", json={
        "username": "testuser_unit",
        "password": "testpassword123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "User registered successfully"

@pytest.mark.asyncio
async def test_register_duplicate_user(client, clean_db):
    """Duplicate registration returns 400."""
    await client.post("/api/auth/register", json={
        "username": "testuser_unit",
        "password": "testpassword123"
    })
    resp = await client.post("/api/auth/register", json={
        "username": "testuser_unit",
        "password": "testpassword123"
    })
    assert resp.status_code == 400

# ─── 4. Auth: Login (Token) ─────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(client, clean_db):
    """Login with valid credentials returns a token."""
    await client.post("/api/auth/register", json={
        "username": "testuser_unit",
        "password": "testpassword123"
    })
    resp = await client.post("/api/auth/token", data={
        "username": "testuser_unit",
        "password": "testpassword123"
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_wrong_password(client, clean_db):
    """Login with wrong password returns 401."""
    await client.post("/api/auth/register", json={
        "username": "testuser_unit",
        "password": "testpassword123"
    })
    resp = await client.post("/api/auth/token", data={
        "username": "testuser_unit",
        "password": "wrongpassword"
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    """Login with nonexistent user returns 401."""
    resp = await client.post("/api/auth/token", data={
        "username": "nonexistent_user_xyz",
        "password": "anypassword"
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert resp.status_code == 401

# ─── 5. Password Hashing ────────────────────────────────────────

def test_password_hash_and_verify():
    """Password hashing and verification works correctly."""
    password = "my_secure_password"
    hashed = get_password_hash(password)
    assert hashed != password  # Not stored in plaintext
    assert verify_password(password, hashed)
    assert not verify_password("wrong_password", hashed)

def test_password_hash_uniqueness():
    """Each hash is unique due to random salt."""
    h1 = get_password_hash("same_password")
    h2 = get_password_hash("same_password")
    assert h1 != h2  # Different salts

# ─── 6. JWT Token ────────────────────────────────────────────────

def test_create_access_token():
    """JWT token creation returns a string."""
    token = create_access_token(data={"sub": "testuser"})
    assert isinstance(token, str)
    assert len(token) > 20

# ─── 7. Adapter Unit Tests ──────────────────────────────────────

def test_adapter_default_mode():
    """Adapter defaults to cloud mode when API key is set."""
    adapter = HybridLLMAdapter()
    # Mode depends on whether OPENROUTER_API_KEY is set in environment
    assert adapter.mode in ["cloud", "local"]

def test_adapter_set_mode():
    """Mode switching works."""
    adapter = HybridLLMAdapter()
    adapter.set_mode("local")
    assert adapter.mode == "local"
    adapter.set_mode("cloud")
    assert adapter.mode == "cloud"

def test_adapter_set_invalid_mode():
    """Invalid mode doesn't change the adapter."""
    adapter = HybridLLMAdapter()
    original = adapter.mode
    adapter.set_mode("bogus")
    assert adapter.mode == original

def test_adapter_cloud_models_all_agents():
    """All 5 agents have cloud model fallback chains."""
    adapter = HybridLLMAdapter()
    expected_agents = {"sage", "analyst", "strategist", "skeptic", "judge"}
    assert set(adapter.cloud_models.keys()) == expected_agents

def test_adapter_cloud_models_have_fallbacks():
    """Each agent has at least 2 models in the fallback chain."""
    adapter = HybridLLMAdapter()
    for agent, models in adapter.cloud_models.items():
        assert len(models) >= 2, f"{agent} has fewer than 2 fallback models"

def test_adapter_cloud_models_are_free():
    """All cloud model IDs end with :free suffix."""
    adapter = HybridLLMAdapter()
    for agent, models in adapter.cloud_models.items():
        for model_id in models:
            assert model_id.endswith(":free"), f"{model_id} for {agent} does not end with :free"

def test_adapter_local_model_files():
    """Local model file mapping covers all agents."""
    adapter = HybridLLMAdapter()
    expected_agents = {"sage", "analyst", "strategist", "skeptic", "judge"}
    assert set(adapter.local_model_files.keys()) == expected_agents
    for agent, filename in adapter.local_model_files.items():
        assert filename.endswith(".gguf"), f"{filename} for {agent} is not a .gguf file"

@pytest.mark.asyncio
async def test_adapter_mock_fallback():
    """When no local model is loaded, adapter returns mock text."""
    adapter = HybridLLMAdapter()
    adapter.set_mode("local")
    adapter.local_models = {}  # Ensure no models loaded
    result = await adapter.get_full_response("sage", "test prompt")
    assert "MOCK" in result.upper() or "not loaded" in result.lower()

# ─── 8. Debate Graph Structure ──────────────────────────────────

def test_debate_graph_nodes():
    """Graph has all required nodes."""
    from debate_graph import workflow
    node_names = set(workflow.nodes.keys())
    required = {"archivist", "sage", "analyst", "strategist", "skeptic", "judge", "crossfire"}
    assert required.issubset(node_names), f"Missing nodes: {required - node_names}"

def test_debate_graph_compiles():
    """Graph compiles into a runnable app."""
    from debate_graph import debate_app
    assert debate_app is not None

def test_should_continue_logic():
    """Routing logic sends to judge when rounds exceeded."""
    from debate_graph import should_continue
    state_continue = {"round_count": 0, "max_rounds": 2}
    assert should_continue(state_continue) == "crossfire"
    
    state_done = {"round_count": 2, "max_rounds": 2}
    assert should_continue(state_done) == "judge"
    
    state_exact = {"round_count": 3, "max_rounds": 2}
    assert should_continue(state_exact) == "judge"

# ─── 9. Database Model Tests ────────────────────────────────────

def test_database_tables_exist():
    """Verify tables are created in the database."""
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "users" in tables
    assert "chat_histories" in tables

def test_user_model_fields():
    """User model has required fields."""
    from database import User
    columns = [c.name for c in User.__table__.columns]
    assert "id" in columns
    assert "username" in columns
    assert "hashed_password" in columns

def test_chat_history_model_fields():
    """ChatHistory model has required fields."""
    from database import ChatHistory
    columns = [c.name for c in ChatHistory.__table__.columns]
    assert "id" in columns
    assert "user_id" in columns
    assert "title" in columns
    assert "transcript" in columns
    assert "created_at" in columns
