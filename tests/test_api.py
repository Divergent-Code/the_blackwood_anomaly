import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock, AsyncMock

import os
import sys

# Add the parent directory to the path so we can import api and database
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.api import app, get_db, get_llm_provider
from app.database import Base, GameSession, run_migrations

# ==========================================
# 1. Setup Isolated Test Database
# ==========================================
# We use a separate SQLite file so we don't overwrite real game saves during testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_blackwood.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the tables in the test database
Base.metadata.create_all(bind=engine)
run_migrations(engine)

@pytest.fixture(autouse=True)
def clear_db():
    db = TestingSessionLocal()
    db.query(GameSession).delete()
    db.commit()
    db.close()

def override_get_db():
    """Yields the testing database session instead of the production one."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the FastAPI dependency
app.dependency_overrides[get_db] = override_get_db

# Initialize the TestClient
client = TestClient(app)

# ==========================================
# 2. Test Cases
# ==========================================

def test_create_session():
    """Tests if a new game session is created and saved to the DB correctly."""
    
    # Mock the LLM Response
    mock_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "You wake up in a freezing dark room. [Health: 100% | Stress: 0%]"
    mock_instance.generate_content = AsyncMock(return_value=mock_response)
    
    # Inject the mocked client
    app.dependency_overrides[get_llm_provider] = lambda: mock_instance

    # Make the Request
    response = client.post(
        "/api/v1/sessions",
        headers={"Authorization": "Bearer FAKE_TEST_KEY"}
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["health"] == 100
    assert data["stress"] == 0
    assert "freezing dark room" in data["narrative"]
    assert "agent_actions" in data

@patch("app.api.rag_engine.retrieve")
def test_submit_action_and_state_update(mock_rag_retrieve):
    """Tests if a player action properly retrieves RAG context, calls AI, and updates DB state."""
    
    # 1. Seed the test database with a mock session
    db = TestingSessionLocal()
    new_session = GameSession(id="test-uuid-123", health=100, stress=0, history=[])
    db.add(new_session)
    db.commit()
    db.close()

    # 2. Mock RAG Engine Output
    mock_rag_retrieve.return_value = [
        {"title": "Test Lore", "content": "Rule: Monsters deal 20% damage on failed stealth."}
    ]
    
    # 3. Mock LLM Response (Simulating taking damage)
    mock_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.function_calls = None
    mock_response.text = "The monster hears you and attacks! [Health: 80% | Stress: 35%]"
    mock_instance.generate_content = AsyncMock(return_value=mock_response)
    
    app.dependency_overrides[get_llm_provider] = lambda: mock_instance

    # 4. Make the Request
    response = client.post(
        "/api/v1/sessions/test-uuid-123/actions",
        headers={"Authorization": "Bearer FAKE_TEST_KEY"},
        json={"action": "I try to sneak past."}
    )

    # 5. Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["health"] == 80  # Proves Regex extracted the new state
    assert data["stress"] == 35  # Proves Regex extracted the new state
    assert "monster hears you" in data["narrative"]
    assert "agent_actions" in data
