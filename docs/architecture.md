# Architecture: The Blackwood Anomaly

The Blackwood Anomaly is designed as a stateless, API-first application that orchestrates complex LLM interactions while enforcing persistent game mechanics via a Retrieval-Augmented Generation (RAG) pipeline.

## System Diagram

The following diagram illustrates the flow of data between the player, the FastAPI backend, the local database, and the external Google Gemini API.

```mermaid
flowchart TD
    Player([Player]) -->|HTTP + Bearer Auth| UI[Web Interface]
    UI -->|REST/JSON| API[FastAPI Application]
    
    subgraph "Core System Architecture"
        API -->|Read/Write Session| DB[(PostgreSQL / SQLite)]
        API -->|Retrieve Context| RAG[RAG Engine Singleton]
        
        RAG -.->|Loads on Boot| Lore[world_lore.md]
        RAG -.->|Loads on Boot| Mechanics[combat_mechanics.md]
    end
    
    RAG -->|Embed Content| Gemini(Google Gemini API)
    API -->|Generate Content| Gemini
    
    classDef external fill:#f9f,stroke:#333,stroke-width:2px;
    classDef database fill:#bbf,stroke:#333,stroke-width:2px;
    class Gemini external;
    class DB database;
```

## Core Components

### 1. FastAPI Application (`api.py`)
The central orchestrator of the game. It handles routing, dependency injection, and security. 
- **Stateless BYOK:** The server does not store a global API key. Instead, it uses FastAPI's `Security` and `HTTPBearer` dependencies to extract the user's API key from the incoming request and instantiate an isolated `genai.Client`.
- **Regex State Extraction:** After the LLM generates a narrative response, the API parses the required `[Health: X% | Stress: Y%]` suffix using Regular Expressions, decoupling the narrative generation from hard state management.

### 2. RAG Engine Singleton (`rag.py`)
A custom-built, dependency-free Vector Search engine optimized for low-resource environments.
- **Lazy-Loaded Embeddings:** To prevent unnecessary API costs and accommodate the BYOK architecture, the engine parses local Markdown files on boot but *waits* to generate vector embeddings until the first user request provides an API key.
- **State-Aware Retrieval:** The engine constructs a query combining the player's proposed action with their current numerical vitals, ensuring that the fetched context is highly relevant to their immediate situation.

### 3. Database Layer (`database.py`)
Manages the persistence of the game loop across individual REST calls.
- **SQLAlchemy ORM:** Provides an abstraction layer over the database, allowing the system to seamlessly switch between a local SQLite file (for rapid testing) and a production-grade PostgreSQL container.
- **JSON History:** The player's entire conversation history is persisted in a JSON column, allowing the FastAPI route to rebuild the LLM's conversational memory on every stateless request.

### 4. Knowledge Base (`data/`)
The static, verified truth that anchors the LLM.
- `world_lore.md`: Defines the atmospheric boundaries, aesthetic (Medical Brutalism), and narrative constraints.
- `combat_mechanics.md`: Hard-coded rules that the LLM must follow to deduct health or apply stress based on player actions.

## Security & Privacy
Because of the **Bring-Your-Own-Key (BYOK)** architecture, no API traffic is routed through centralized proxy servers, and no usage is billed to the host. The local database ensures that session transcripts remain strictly within the user's deployed instance.
