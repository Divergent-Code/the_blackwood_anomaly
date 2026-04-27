from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google import genai # Using the modern GenAI client for isolated requests
from sqlalchemy.orm import Session
from database import get_db, GameSession
import re
from rag import rag_engine

# --- Constants & Prompts ---
SYSTEM_PROMPT_START = "You are a horror Game Master. The game has just started..."
SYSTEM_PROMPT_ACTION = "You are a horror AI Game Master. Strict rule: YOU MUST end your response exactly with [Health: X% | Stress: Y%]."

app = FastAPI(title="The Blackwood Anomaly API")

# Mount static files for the frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_frontend():
    """Serves the frontend application."""
    return FileResponse("static/index.html")

# Security schema to extract the Bearer token (The User's API Key)
security = HTTPBearer()

def get_gemini_client(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Dependency function: Extracts the user's API key from the Authorization header
    and returns a fresh, isolated Gemini client for this specific request.
    """
    user_api_key = credentials.credentials
    if not user_api_key:
        raise HTTPException(status_code=401, detail="Missing Google API Key")
    
    # Instantiate an isolated client. No global state!
    try:
        return genai.Client(api_key=user_api_key)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

def format_chat_history(session_history: list, new_prompt: str) -> list:
    """Formats the DB JSON history into the structure expected by the Gemini SDK."""
    formatted_history = []
    for msg in session_history:
        text_content = msg.get("content", msg.get("text", ""))
        formatted_history.append({"role": msg["role"], "parts": [{"text": text_content}]})
    
    formatted_history.append({"role": "user", "parts": [{"text": new_prompt}]})
    return formatted_history

# --- Request/Response Models ---
class ActionRequest(BaseModel):
    action: str

class GameResponse(BaseModel):
    session_id: str
    health: int
    stress: int
    narrative: str

# --- API Endpoints ---
@app.post("/api/v1/sessions", response_model=GameResponse)
async def create_session(
    client: genai.Client = Depends(get_gemini_client),
    db: Session = Depends(get_db)
):
    """Initializes a new game using the player's provided API key."""
    
    try:
        # We pass the prompt directly using the user's isolated client
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents="Describe the terrifying room the player wakes up in.",
            config={"system_instruction": SYSTEM_PROMPT_START}
        )
        
        # Save new session to database
        new_session = GameSession(
            health=100,
            stress=0,
            history=[{"role": "model", "content": response.text}]
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        return GameResponse(
            session_id=new_session.id,
            health=new_session.health,
            stress=new_session.stress,
            narrative=response.text
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Engine Error: {str(e)}")

@app.post("/api/v1/sessions/{session_id}/actions", response_model=GameResponse)
async def submit_action(
    session_id: str, 
    request: ActionRequest, 
    client: genai.Client = Depends(get_gemini_client),
    db: Session = Depends(get_db)
):
    """Processes a player's action, utilizing RAG and saving state to the DB."""
    
    # 1. Fetch Session
    session = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Formulate state-aware query and fetch RAG Context
    retrieval_query = f"Player State: {session.health}% Health, {session.stress}% Stress. Action: {request.action}"
    retrieved_chunks = rag_engine.retrieve(client, retrieval_query, top_k=2)
    
    rag_context_str = "\n\n".join([chunk['content'] for chunk in retrieved_chunks])
    
    # 3. Build the prompt
    augmented_prompt = f"""
=== RETRIEVED GAME MECHANICS ===
{rag_context_str}

=== PLAYER ACTION ===
(Current State - Health: {session.health}%, Stress: {session.stress}%)
Player: {request.action}
"""

    # 4. Call the LLM (Passing the JSON history for memory)
    try:
        formatted_history = format_chat_history(session.history, augmented_prompt)
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=formatted_history,
            config={"system_instruction": SYSTEM_PROMPT_ACTION}
        )
        ai_text = response.text
        
        # 5. Extract State via Regex
        match = re.search(r"\[Health: (\d+)% \| Stress: (\d+)%\]", ai_text)
        if match:
            session.health = int(match.group(1))
            session.stress = int(match.group(2))
            
        # 6. Update DB History & Commit
        new_history = list(session.history)
        new_history.append({"role": "user", "content": request.action}) # Store clean action for history
        new_history.append({"role": "model", "content": ai_text})
        session.history = new_history
        
        db.commit()
        db.refresh(session)
        
        return GameResponse(
            session_id=session.id,
            health=session.health,
            stress=session.stress,
            narrative=ai_text
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Engine Error: {str(e)}")
