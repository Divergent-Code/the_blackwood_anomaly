# Getting Started: The Blackwood Anomaly

Welcome to The Blackwood Anomaly! This guide will walk you through setting up the API, configuring the environment, and playing the game locally.

## Prerequisites

Before you begin, ensure you have the following installed:
- **Python 3.10+**
- **Docker & Docker Compose** (Optional, but highly recommended for the PostgreSQL database)
- A valid **Google Gemini API Key**. You can obtain one from [Google AI Studio](https://aistudio.google.com/).

---

## 1. Local Environment Setup

First, clone the repository and set up your Python environment.

```bash
# Clone the repository
git clone <your-repo-url>
cd applied_ai-system_final

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install the required dependencies
pip install -r requirements.txt
```

---

## 2. Database Configuration

The Blackwood Anomaly uses SQLAlchemy and defaults to a local SQLite database (`blackwood.db`) for immediate testing out-of-the-box. However, for a production-like environment with concurrent sessions, we provide a PostgreSQL Docker container.

**To run with PostgreSQL (Recommended):**

1. Start the Docker container:
   ```bash
   docker-compose up -d
   ```
2. Create a `.env` file in the root directory and set the `DATABASE_URL`:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/blackwood
   ```

*(If you skip this step and do not create a `.env` file, the app will automatically fall back to creating a local `blackwood.db` SQLite file).*

---

## 3. Running the Server

Once your dependencies are installed and your database is ready, you can start the FastAPI server.

```bash
uvicorn api:app --reload
```

The server will boot up and be accessible at `http://127.0.0.1:8000`.

---

## 4. Playing the Game

1. Open your web browser and navigate to [http://127.0.0.1:8000/](http://127.0.0.1:8000/).
2. You will be greeted by the **Medical Brutalism** web interface.
3. When prompted, enter your **Google Gemini API Key**. The server uses a Bring-Your-Own-Key (BYOK) architecture, meaning your key is passed directly in the HTTP headers and is never stored on the server.
4. Begin typing your actions into the dossier to interact with the AI Game Master.

---

## 5. Running the Test Suite

The project features a comprehensive, zero-dependency test suite that utilizes FastAPI's `TestClient` and `unittest.mock` to ensure game mechanics function correctly without consuming your actual Gemini API quota.

To run the tests:

```bash
pytest tests/
```

You should see all tests pass, validating the RAG engine initialization, the API endpoints, and the regex state extraction logic.

---

## Troubleshooting

### "🚨 WARNING: RAG document missing."
**Cause:** The application cannot find `world_lore.md` or `combat_mechanics.md`.
**Fix:** Ensure you are running the `uvicorn` command from the root directory of the project, so the relative paths to the `data/` directory resolve correctly.

### "401 Unauthorized"
**Cause:** You did not provide a Gemini API Key, or the key provided is invalid.
**Fix:** Double-check your API key in Google AI Studio. Ensure you haven't hit your rate limits.

### "SQLite thread errors"
**Cause:** You are running concurrent requests against the SQLite fallback database.
**Fix:** SQLite is meant for single-user testing. For robust multi-session support, please use the provided Docker Compose file to spin up the PostgreSQL database.
