# Welcome to The Blackwood Anomaly Wiki

The Blackwood Anomaly is a text-based survival horror engine powered by a custom Retrieval-Augmented Generation (RAG) implementation and Google's Gemini LLM.

This wiki serves as the central knowledge base for understanding the architecture, deploying the project, and contributing to the codebase.

## 📖 Table of Contents

### 🚀 Getting Started

* [Getting Started Guide](../docs/getting_started.md) - Full local setup, Docker configuration, and troubleshooting.
* [Onboarding for Contributors](Onboarding.md) - A guide for new developers looking to understand the project structure and contribute.

### 🏛️ Architecture & API

* [System Architecture](../docs/architecture.md) - Overview of the BYOK architecture, RAG Singleton, and database.
* [API Reference](../docs/api_reference.md) - Documentation for the FastAPI routes, endpoints, and authentication schema.
* [Code Reference](../docs/code_reference.md) - Deep dive into `RAGEngine`, `GameSession`, and core utility methods.

### 🎭 Game Design & Lore

* **World Lore:** (`data/world_lore.md`) - The atmospheric boundaries and the Medical Brutalism aesthetic.
* **Combat Mechanics:** (`data/combat_mechanics.md`) - The hard-coded logic defining Health and Stress impacts.
* [Model Card](../model_card.md) - Safety, usage, and ethical considerations for the AI Game Master.

---

## 🛠️ Tech Stack Quick Links

* **Backend:** [FastAPI](https://fastapi.tiangolo.com/)
* **AI Model:** [Google GenAI](https://ai.google.dev/)
* **Database:** [SQLAlchemy](https://www.sqlalchemy.org/) + PostgreSQL (Local SQLite fallback)
* **Frontend:** Vanilla HTML/JS with CSS Glassmorphism
