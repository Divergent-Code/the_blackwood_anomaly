# Changelog

All notable changes to **The Blackwood Anomaly** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-27

### Added

- **FastAPI REST API (`api.py`)**: Migrated the core game loop from a local terminal script to a fully functional, stateless REST API.
- **Medical Brutalism UI (`static/index.html`)**: Added a browser-based frontend for interacting with the AI Game Master.
- **Database Persistence (`database.py`)**: Implemented SQLAlchemy ORM to track game sessions, health, stress, and conversation histories. Includes support for both local SQLite and containerized PostgreSQL.
- **BYOK Authentication**: Integrated `HTTPBearer` security to require users to supply their own Google Gemini API key, ensuring zero host billing.
- **Automated Testing (`tests/`)**: Added a comprehensive `pytest` harness using `FastAPI.TestClient` and `unittest.mock` to validate regex state extraction and RAG behavior without consuming API quota.
- **Comprehensive Documentation Suite**: Added API reference, architecture diagrams, setup guides, and a contributor Wiki.
- **Docker Compose Setup**: Added `docker-compose.yml` for rapid, consistent database deployments.

### Changed

- **RAG Engine Refactor (`rag.py`)**: Upgraded the local Markdown chunking and cosine similarity system. Embeddings are now lazy-loaded on the first authenticated request rather than at boot time.
- **Model Migration**: Explicitly pinned the AI model to `gemini-2.5-flash` for high-speed, text-based narrative generation.
- **State Management**: Player vitals (Health, Stress) are now persistently tracked in the database and explicitly injected into the LLM's system prompt on every stateless turn.

### Deprecated

- **Terminal Loop (`main.py`)**: The original terminal-based interaction script is retained for archival purposes but is no longer the primary entry point for the engine.

## [0.1.0] - Initial Prototype

### Initial Release

- Created the initial terminal-based `main.py` game loop.
- Drafted `world_lore.md` and `combat_mechanics.md` to serve as the narrative boundaries.
- Implemented a basic pure-Python cosine similarity function for retrieving text chunks.
