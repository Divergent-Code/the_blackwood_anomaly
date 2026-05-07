# Agent Context: applied_ai-system_final

> **Last Updated**: 2026-05-06 23:22
> **Auto-generated**: by `prepare_context.py` to give AI Agents quick project context

---

## 🎯 1. Project Goal

* **Core Purpose**: An AI-powered, API-driven survival horror text adventure powered by FastAPI, PostgreSQL, and LLMs (supporting Gemini 2.5 Flash, OpenAI GPT-4o-mini, and OpenRouter).
* _For full details see [README.md](README.md)_

## 🛠️ 2. Tech Stack & Environment

* **Python Packages**: google-genai, python-dotenv, pytest, fastapi, uvicorn, pydantic, sqlalchemy, psycopg2-binary, pgvector, openai

### Raw Config Files

#### requirements.txt

```text
google-genai
python-dotenv
pytest
fastapi
uvicorn
pydantic
sqlalchemy
psycopg2-binary
pgvector
openai
```

## 📂 3. Core Structure

#### 💡 AI Reading Rule: Look for files according to this structure, do not blindly guess paths

```text
applied_ai-system_final/
├── AGENT_CONTEXT.md
├── CHANGELOG.md
├── README.md
├── app
│   ├── __init__.py
│   ├── api.py
│   ├── database.py
│   ├── llm_provider.py
│   └── rag.py
├── blackwood.db
├── data
│   ├── combat_mechanics.md
│   ├── escape_route.md
│   ├── institute_map.md
│   ├── lore_fragments.md
│   ├── storyteller_guide.md
│   ├── threats.md
│   └── world_lore.md
├── diary
│   └── 2026
│       └── 05
├── docker-compose.yml
├── docs
│   ├── api_reference.md
│   ├── architecture.md
│   ├── code_reference.md
│   ├── design
│   │   ├── blackwood_asylum.diagram.mmd
│   │   ├── blackwood_asylum_diagram.svg
│   │   └── system_architecture_design.mmd
│   ├── getting_started.md
│   └── wiki
│       ├── Home.md
│       └── Onboarding.md
├── model_card.md
├── project_outline.md
├── requirements.txt
├── scratch
│   ├── test_openrouter.py
│   └── test_tool.py
├── static
│   └── index.html
├── test_blackwood.db
└── tests
    └── test_api.py
```

## 🏛️ 4. Architecture & Conventions

* _(No `.auto-skill-local.md` yet, project pitfalls will automatically accumulate during development)_

## 🚦 5. Current Status & TODO

#### Auto-extracted from latest diary 2026-05-06

### 🚧 TODOs

* [ ] Implement full Mastery Tracking System (Project Neith integration) into the web frontend
* [ ] Add `tester_feedback_form.md` linting fixes (trailing spaces, column styling)
* [ ] Wire up the Neith `NeithRouter` to the FastAPI endpoints for in-game tutoring mode
* [ ] Add session export / save-to-file feature for players
* [ ] Validate Docker Compose PostgreSQL deployment end-to-end
* [ ] Review `model_card.md` for accuracy after v1.0.0 stabilization
* [ ] Consider adding OpenTelemetry tracing to `api.py` for production observability
