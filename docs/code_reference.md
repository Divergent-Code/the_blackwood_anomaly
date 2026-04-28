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

### `get_db()`

A FastAPI dependency generator that creates a localized SQLAlchemy `SessionLocal`, yields it to the route, and ensures it safely closes after the request completes.

---

## 3. API Utilities (`api.py`)

### `get_llm_provider(credentials: HTTPAuthorizationCredentials, x_llm_provider: str)`

A FastAPI security dependency. Extracts the Bearer token from the `Authorization` HTTP header and instantiates an isolated `LLMProvider` (`GeminiProvider`, `OpenAIProvider`, or `OpenRouterProvider`) based on the `X-LLM-Provider` header.

### `get_storyteller_guide()`

A FastAPI dependency that dynamically loads `data/storyteller_guide.md` as the foundational system prompt for the LLM. This defines the core Game Master persona, narrative style, and regex state-extraction rules for each session request.

## 4. LLM Providers (`llm_provider.py`)

Abstracts the underlying LLM SDKs to provide a unified `generate_content` and `generate_with_tool_result` interface, handling message formatting, tool definitions, and tool result passing across different models. Includes `OpenRouterProvider` for automatic endpoint routing and model name translation.

### `roll_d20(difficulty_class: int) -> str`

A Python tool registered with the Gemini model to act as a "Dice Roller" agent. Instead of arbitrarily deciding player success, the AI can invoke this function with a target difficulty class. The FastAPI backend intercepts the `function_call`, executes the dice roll mathematically, records the action in the `agent_actions` array, and returns the result to Gemini to dictate the final narrative outcome.
