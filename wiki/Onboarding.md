# Onboarding: Contributing to The Blackwood Anomaly

Welcome to the development team for **The Blackwood Anomaly**! This document is designed to get you up to speed quickly on how our engine operates, our design philosophy, and how to start making contributions.

## 1. The Core Philosophy

We are building a **stateless, AI-driven narrative engine**. 
Instead of hard-coding dialogue trees, we use an LLM. Instead of relying on the LLM's inherently flawed memory, we use **Retrieval-Augmented Generation (RAG)** to constantly remind the AI of the rules.

**Key constraints to keep in mind:**
- **Zero-Dependency RAG:** We do not use LangChain or LlamaIndex. We use pure Python cosine similarity to keep the deployment lightweight.
- **BYOK (Bring Your Own Key):** The server does not handle billing. Every request uses the user's provided API key. **Never** hardcode your API key or commit it to the repository.

## 2. Project Structure

Familiarize yourself with the core directories:
- `api.py`: The FastAPI application. All routing and dependency injection happens here.
- `rag.py`: The `RAGEngine` Singleton. If you want to improve how the AI searches for rules, look here.
- `database.py`: SQLAlchemy models. Modifying the player's saved state structure? You'll need to update `GameSession` here.
- `data/`: The heart of the game. `world_lore.md` and `combat_mechanics.md` dictate the actual gameplay. To change the game, change these files.
- `tests/`: Our automated testing suite. 

## 3. Your First Pull Request

### Step 1: Run the Tests First
Before touching any code, ensure you have the environment running and tests passing locally:
```bash
pytest tests/
```
We use `unittest.mock` to simulate the Gemini API responses. You do not need a real API key to run the test suite.

### Step 2: Make Your Changes
Pick an area to focus on. For example:
- **Game Design:** Add a new room to `world_lore.md`.
- **Backend:** Add an inventory system to `database.py` and extract it via regex in `api.py`.
- **Frontend:** Enhance the `static/index.html` interface.

### Step 3: Test Your Changes
If you modified the core logic, you **must** update the `tests/test_api.py` suite to reflect the new expected states. 

### Step 4: Submit a PR
Ensure your code is clean, well-commented, and your commit messages are descriptive. 

## 4. Need Help?
Check out the [Architecture Documentation](../docs/architecture.md) and [Code Reference](../docs/code_reference.md) for deeper technical details. If you're still stuck, reach out to the project maintainers!
