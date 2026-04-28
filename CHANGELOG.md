# Changelog

All notable changes to **The Blackwood Anomaly** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-27

### Added

- **FastAPI REST API (`api.py`)**: Migrated the core game loop from a local terminal script to a fully functional, stateless REST API.
- **System Prompt Decoupling**: Abstracted the AI Game Master persona into `data/storyteller_guide.md`, loaded dynamically via `api.py` dependency injection to easily tune the narrative style and formatting constraints.
- **Core Premise Context (`data/storyteller_guide.md`)**: Added a `## THE CORE PREMISE` section anchoring every generation to named lore: The Blackwood Institute (WHERE), Subject 814 (WHO), The Anomaly (WHY), and the escape goal (WHAT). Eliminates generic "dark room" outputs entirely.
- **Session Modes (`data/storyteller_guide.md`)**: Added a `## SESSION MODES` section defining two explicit behavioral modes: MODE 1 (New Game) triggered by `"Start the game."` and MODE 2 (Session Recap) triggered by `"Recap the session."` — preventing the LLM from conflating session-opening and recap generation logic.
- **Recap Endpoint (`api.py`)**: Added `POST /api/v1/sessions/{id}/recap` that compresses full session history into a labelled transcript (`SUBJECT 814` / `INSTITUTE LOG`), feeds it to the LLM in MODE 2, and returns a clinical 2–3 sentence atmospheric summary. Vitals tag is explicitly suppressed in this mode to prevent regex misfires.
- **Directive Session Opening (`api.py`)**: Replaced the vague session-start prompt with a specific directive instructing the LLM to write the exact wake-up moment—surgical staples, hospital gown, concrete room—ending on a clear action prompt.
- **Frontend Session Resume (`static/index.html`)**: Updated `resumeSession()` to call the `/recap` endpoint instead of dumping raw history. The recap renders as a visually distinct **INCIDENT REPORT — PRIOR OBSERVATION** block with a dashed border and muted styling. Graceful fallback to a static message if the recap call fails.
- **Multi-LLM Abstraction (`llm_provider.py`)**: Abstracted the AI engine to support Gemini, OpenAI, and OpenRouter models via the `X-LLM-Provider` header (including automatic model mapping for OpenRouter endpoints).
- **Agentic Tool Calling**: The Game Master can now autonomously decide to invoke the `roll_d20` Python function for dice rolls.
- **Agent Action Tracing**: Added the `agent_actions` array to `GameResponse` to log intermediate agent planning steps to the client.
- **Medical Brutalism UI (`static/index.html`)**: Added a browser-based frontend for interacting with the AI Game Master.
- **Database Persistence (`database.py`)**: Implemented SQLAlchemy ORM to track game sessions, health, stress, and conversation histories. Includes support for both local SQLite and containerized PostgreSQL.
- **BYOK Authentication**: Integrated `HTTPBearer` security to require users to supply their own Gemini, OpenAI, or OpenRouter API key, ensuring zero host billing.
- **Automated Testing (`tests/`)**: Added a comprehensive `pytest` harness using `FastAPI.TestClient` and `unittest.mock` to validate regex state extraction and RAG behavior without consuming API quota.
- **Comprehensive Documentation Suite**: Added API reference, architecture diagrams, setup guides, and a contributor Wiki.
- **Docker Compose Setup**: Added `docker-compose.yml` for rapid, consistent database deployments.

### Changed

- **RAG Engine Refactor (`rag.py`)**: Upgraded the local Markdown chunking and cosine similarity system. Embeddings are now lazy-loaded on the first authenticated request rather than at boot time.
- **Asynchronous RAG Retrieval**: Refactored `rag.py` to use `asyncio.Lock()` and async methods (`retrieve`, `_ensure_document_embeddings`) to prevent race conditions when multiple players authenticate simultaneously.
- **Model Migration**: Explicitly pinned the AI model to `gemini-2.5-flash` for high-speed, text-based narrative generation.
- **State Management**: Player vitals (Health, Stress) are now persistently tracked in the database and explicitly injected into the LLM's system prompt on every stateless turn.

### Deprecated

- **Terminal Loop (`legacy/main.py`)**: The original terminal-based interaction script was moved to `legacy/main.py` and is retained for archival purposes but is no longer the primary entry point for the engine.

## [0.1.0] - Initial Prototype

### Initial Release

- Created the initial terminal-based `main.py` game loop.
- Drafted `world_lore.md` and `combat_mechanics.md` to serve as the narrative boundaries.
- Implemented a basic pure-Python cosine similarity function for retrieving text chunks.
