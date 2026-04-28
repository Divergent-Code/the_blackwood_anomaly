# Code Reference: The Blackwood Anomaly

This document provides a technical overview of the primary classes and utility functions that power the game engine.

## 1. Retrieval-Augmented Generation (`rag.py`)

The `rag.py` module contains the custom, dependency-free embedding and retrieval logic.

### `class RAGEngine`

A Singleton class that manages the loading, embedding, and retrieval of game mechanics and lore.

#### `__init__(self)`

Initializes the engine, sets the model to `text-embedding-004`, and triggers the local parsing of `world_lore.md` and `combat_mechanics.md`. Note that embeddings are *not* generated upon initialization to support the BYOK architecture.

#### `_parse_markdown(self, filename: str, prefix: str)`

Reads a local Markdown file and splits it into discrete chunks based on `##` headers. Appends the chunks to the internal `self.chunks` list.

* **Parameters:**
  * `filename`: The path to the markdown file.
  * `prefix`: A tag (e.g., `LORE`, `MECHANICS`) prepended to the title of the chunk to help the LLM identify the source of the rule.

#### `async _ensure_document_embeddings(self, client: genai.Client)`

A lazy-loading mechanism utilizing `asyncio.Lock()` for thread safety. When the first API request comes in containing a valid Gemini API key, this function embeds the knowledge base chunks using that user's key and caches them for the lifetime of the server instance. The async lock prevents race conditions during concurrent authentication requests.

#### `async retrieve(self, client: genai.Client, query: str, top_k: int = 2) -> list`

Embeds the incoming player query and performs a pure-Python cosine similarity search against the cached knowledge base.

* **Parameters:**
  * `client`: An authenticated `genai.Client`.
  * `query`: The state-aware search string (e.g., `"Player State: 100% Health. Action: I run away."`).
  * `top_k`: The number of relevant chunks to return (default is 2).
* **Returns:** A list of the `top_k` most relevant dictionary chunks.

---

## 2. Database Models (`database.py`)

The application uses SQLAlchemy to manage game states.

### `class GameSession(Base)`

Represents a single instance of a player's playthrough.

* **`id`** (`String`): A UUID primary key.
* **`health`** (`Integer`): The player's current health (0-100).
* **`stress`** (`Integer`): The player's current psychological stress (0-100).
* **`history`** (`JSON`): An array of message dictionaries (e.g., `{"role": "user", "content": "..."}`) maintaining the conversational context for the LLM.
* **Extended State Columns**:
  * **`inventory`** (`JSON`): List of items currently held (max 4).
  * **`current_location`** (`String`): The canonical zone name the player is in.
  * **`visited_locations`** (`JSON`): List of zones the player has discovered.
  * **`discovered_lore`** (`JSON`): List of fragment IDs the player has read.
  * **`escape_stage`** (`Integer`): The current progress of the escape route (0-4).
  * **`turn_count`** (`Integer`): Total number of actions taken.

### `get_db()`

A FastAPI dependency generator that creates a localized SQLAlchemy `SessionLocal`, yields it to the route, and ensures it safely closes after the request completes.

---

## 3. API Utilities (`api.py`)

### `get_llm_provider(credentials: HTTPAuthorizationCredentials, x_llm_provider: str)`

A FastAPI security dependency. Extracts the Bearer token from the `Authorization` HTTP header and instantiates an isolated `LLMProvider` (`GeminiProvider`, `OpenAIProvider`, or `OpenRouterProvider`) based on the `X-LLM-Provider` header.

### `get_storyteller_guide()`

A FastAPI dependency that dynamically loads `data/storyteller_guide.md` as the foundational system prompt on every LLM call. The guide is structured in five sections:

1. **Persona** — aesthetic and writing voice constraints.
2. **Core Premise** — the WHO/WHAT/WHERE/WHY lore block grounding all generation in established canon (Subject 814, The Blackwood Institute, The Anomaly).
3. **Game Loop** — the Resolve → Advance → Prompt narrative structure the LLM must follow on every turn.
4. **Output Guardrail** — instructs the LLM to call `apply_vitals` instead of manually writing out vitals, but enforces the `[Health: X% | Stress: Y%]` format as a fallback.
5. **Session Modes** — two explicit behavioral modes keyed to the opening of the user prompt:
   * **MODE 1 (New Game):** triggered by `"Start the game."` — cinematic scene-setting with vitals tag at 100/0.
   * **MODE 2 (Session Recap):** triggered by `"Recap the session."` — clinical 2–3 sentence incident-report summary, **vitals tag suppressed**.

Because the file is read per-request (not at boot), narrative tuning changes take effect immediately on the next API call without a server restart.

### `create_session()` — Opening Prompt

The session-initialization LLM call uses a **directive prompt** rather than a vague creative instruction. It explicitly tells the AI which moment to write (Subject 814's wake-up), which physical props to use (surgical staples, hospital gown, concrete room), and mandates ending on a clear player action prompt. This eliminates generic opening outputs.

### `get_session_recap()` — `POST /api/v1/sessions/{id}/recap`

Generates an atmospheric session summary for returning players. The backend:

1. Loads the full message history from the database.
2. Compresses it into a labelled transcript with `SUBJECT 814:` and `INSTITUTE LOG:` prefixes.
3. Sends it to the LLM with the `"Recap the session."` sentinel prefix, triggering MODE 2.
4. Returns the 2–3 sentence clinical summary as a `RecapResponse`.

The frontend renders this as a visually distinct **INCIDENT REPORT — PRIOR OBSERVATION** block with dashed border styling. If the call fails, it falls back silently to a static `"— Session resumed. Observation log continues. —"` message so play can continue.

## 4. LLM Providers (`llm_provider.py`)

Abstracts the underlying LLM SDKs to provide a unified `generate_content` and `generate_with_tool_result` interface, handling message formatting, tool definitions, and tool result passing across different models. Includes `OpenRouterProvider` for automatic endpoint routing and model name translation.

### Agentic Tools

The LLM is registered with a suite of Python functions that allow it to manipulate the deterministic game state:

* **`roll_d20(difficulty_class)`**: Rolls a 20-sided die to determine the success/failure of an action.
* **`apply_vitals(health_delta, stress_delta)`**: Safely updates Subject 814's health and stress without regex parsing.
* **`add_item(item_name)` / `remove_item(item_name)`**: Modifies the player's 4-slot inventory.
* **`move_to_location(location_name)`**: Updates the current canonical zone.
* **`discover_lore(fragment_id)`**: Marks a specific document as found.
* **`advance_escape_stage()`**: Increments the primary win-condition track (0-4).

### `_execute_tool_call(tool_call, session)`

The internal dispatch loop in `api.py`. When the LLM requests a tool call, this function intercepts it, updates the live `GameSession` attributes accordingly, records a human-readable log in the `agent_actions` array, and passes the updated state back to the LLM to narrate the outcome.
