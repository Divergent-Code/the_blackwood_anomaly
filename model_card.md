# Model Card: The Blackwood Anomaly (Game Master AI)

## Model Details

* **Developer:** The Blackwood Anomaly project team.
* **Model Version:** V1.0
* **Base Models:** Gemini 2.5 Flash, OpenAI GPT-4o-mini, & OpenRouter model routing
* **Task:** Text-based survival horror Game Master orchestration, state extraction, and Agentic Tool Calling.
* **Architecture:** Large Language Model (LLM) utilizing a stateless Retrieval-Augmented Generation (RAG) pipeline via FastAPI and an abstract `LLMProvider`.

## Intended Use

* **Primary Use Case:** To dynamically generate atmospheric, engaging, and terrifying horror narratives in response to player text inputs within a controlled, persistent game session.
* **Secondary Use Case:** To parse player intent and apply strict game mechanics by utilizing a suite of Python tools (like `roll_d20`, `apply_vitals`, `add_item`) autonomously to deterministically mutate game state, with Regex parsing reserved as a fallback mechanism.
* **Out-of-Scope:** This model is strictly bounded to the game's universe and mechanics. It is not intended to provide real-world advice, hold casual conversations, or generate non-horror related creative writing.

## Training Data & Retrieval Context

* **System Instruction:** Loaded dynamically per request from `data/storyteller_guide.md`. Includes:
  * Persona and aesthetic constraints ("Medical Brutalism").
  * **Core Premise block** — hard-coded lore (Subject 814, The Blackwood Institute, The Anomaly, the escape goal) injected on every single LLM call to eliminate context drift and generic outputs.
  * Narrative loop (Resolve → Advance → Prompt) and the `[Health: X% | Stress: Y%]` output guardrail.
  * **Session Modes** — MODE 1 (`"Start the game."`) for cinematic new-game openings; MODE 2 (`"Recap the session."`) for clinical session summaries with vitals tag explicitly suppressed to prevent regex misfire.
* **Session Opening:** The `POST /api/v1/sessions` call uses a directive prompt specifying the exact scene (wake-up moment), props (staples, gown, concrete room), and mandatory action-prompt ending to guarantee a consistent, grounded first impression for every player.
* **Session Recap:** The `POST /api/v1/sessions/{id}/recap` call compresses session history into a labelled transcript and triggers MODE 2, returning a 2–3 sentence clinical incident-report summary rendered as a distinct UI block in the frontend.
* **Retrieval-Augmented Generation (RAG):** The AI has no inherent persistent memory of the game's mechanics. Instead, it relies on strict context injected at runtime from two verified sources:
    1. `world_lore.md`: The atmospheric constraints, setting details, and narrative boundaries.
    2. `combat_mechanics.md`: Hard-coded rules dictating when the player should take damage or accrue stress based on their actions.
* The embedding layer (using `text-embedding-004`) fetches the most relevant context and injects it into the system prompt prior to generation.

## Evaluation & Testing

* **Reliability:** The system uses automated Pytest suites with FastAPI's `TestClient` and `unittest.mock` to ensure the agentic tool-interception loop accurately captures game state mutations and successfully updates the PostgreSQL database on every turn.
* **Performance:** Deployed as a stateless, dependency-injected endpoint where the RAG embeddings are lazy-loaded via a thread-safe, asynchronous Singleton pattern to prevent excessive API quota consumption and manage concurrent authentication safely.

## Ethical Considerations & Safety

* **Content Warning:** The game generates descriptions of mild to severe psychological and physical horror. It is strictly meant for mature audiences.
* **Safety Boundaries:** The system prompt and RAG context are designed to keep the AI focused on the narrative without generating excessively graphic, non-consensual, or real-world harmful content. The user maintains control over the LLM via their provided API key (BYOK architecture).
* **Data Privacy:** Because the architecture requires the user to supply their own API key via Bearer Auth, no centralized logging or telemetry of the generated stories is tracked or retained by the platform itself. The conversation history is persisted strictly within the user's isolated local database instance.
