# Model Card: The Blackwood Anomaly (Game Master AI)

## Model Details

* **Developer:** The Blackwood Anomaly project team.
* **Model Version:** V1.0
* **Base Model:** Gemini 2.5 Flash
* **Task:** Text-based survival horror Game Master orchestration and state extraction.
* **Architecture:** Large Language Model (LLM) utilizing a stateless Retrieval-Augmented Generation (RAG) pipeline via `google-genai` and FastAPI.

## Intended Use

* **Primary Use Case:** To dynamically generate atmospheric, engaging, and terrifying horror narratives in response to player text inputs within a controlled, persistent game session.
* **Secondary Use Case:** To parse player intent and apply strict game mechanics (Health and Stress modifications) by outputting a predictable Regex-parsable state format at the end of each response.
* **Out-of-Scope:** This model is strictly bounded to the game's universe and mechanics. It is not intended to provide real-world advice, hold casual conversations, or generate non-horror related creative writing.

## Training Data & Retrieval Context

* **Retrieval-Augmented Generation (RAG):** The AI has no inherent persistent memory of the game's mechanics. Instead, it relies on strict context injected at runtime from two verified sources:
    1. `world_lore.md`: The atmospheric constraints, setting details, and narrative boundaries.
    2. `combat_mechanics.md`: Hard-coded rules dictating when the player should take damage or accrue stress based on their actions.
* The embedding layer (using `text-embedding-004`) fetches the most relevant context and injects it into the system prompt prior to generation.

## Evaluation & Testing

* **Reliability:** The system uses automated Pytest suites with FastAPI's `TestClient` and `unittest.mock` to ensure the regex state-extractor (`[Health: X% | Stress: Y%]`) successfully fires and updates the PostgreSQL database on every turn.
* **Performance:** Deployed as a stateless, dependency-injected endpoint where the RAG embeddings are lazy-loaded via a Singleton pattern to prevent excessive API quota consumption.

## Ethical Considerations & Safety

* **Content Warning:** The game generates descriptions of mild to severe psychological and physical horror. It is strictly meant for mature audiences.
* **Safety Boundaries:** The system prompt and RAG context are designed to keep the AI focused on the narrative without generating excessively graphic, non-consensual, or real-world harmful content. The user maintains control over the LLM via their provided API key (BYOK architecture).
* **Data Privacy:** Because the architecture requires the user to supply their own API key via Bearer Auth, no centralized logging or telemetry of the generated stories is tracked or retained by the platform itself. The conversation history is persisted strictly within the user's isolated local database instance.
