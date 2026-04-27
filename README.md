# 🌲 The Blackwood Anomaly

An AI-powered, API-driven survival horror text adventure powered by FastAPI, PostgreSQL, and Google's Gemini 2.5 Flash model.

This project demonstrates how to build a stateful, RAG-augmented game engine where players interact with an AI Game Master that strictly adheres to retrieved game mechanics and lore.

## 🏛️ Architecture

* **Framework:** FastAPI
* **AI Integration:** `google-genai` (BYOK - Bring Your Own Key architecture via Bearer tokens)
* **State Management:** SQLAlchemy + PostgreSQL (via Docker) with a local SQLite fallback for rapid testing.
* **Retrieval-Augmented Generation (RAG):** A lazy-loaded Singleton engine that embeds `world_lore.md` and `combat_mechanics.md` dynamically on the first request, saving massive API overhead.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Database (Optional but Recommended)

To use actual PostgreSQL with vector capabilities, spin up the provided Docker container:

```bash
docker-compose up -d
```

*(If you skip this step, the app will automatically fall back to creating a local `blackwood.db` SQLite file).*

### 3. Boot the Server

```bash
uvicorn api:app --reload
```

### 4. Play the Game

Navigate to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to access the interactive Swagger UI.

1. Click **Authorize** and input your Google AI API key.
2. Use the `POST /api/v1/sessions` endpoint to start a new game and get your `session_id`.
3. Use the `POST /api/v1/sessions/{session_id}/actions` endpoint to submit your actions and try to survive!

## 🧪 Testing

This project features an automated, zero-dependency test suite utilizing FastAPI's `TestClient` and `unittest.mock`.

To run the tests without consuming real API quota or touching your local database:

```bash
pytest tests/test_api.py
```

## 📜 Project Phases Completed

* **Phase 1 & 2:** Core Mechanics & Architecture mapped out.
* **Phase 3:** RAG Singleton implemented using `google-genai`.
* **Phase 4:** Reliability & Testing achieved via `test_api.py` mocking.
* **Phase 5 & 6:** Reflection (`model_card.md`) and finalized documentation deployed!
