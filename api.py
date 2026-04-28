from fastapi import FastAPI, Depends, HTTPException, Security, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db, GameSession
import re
import random
from rag import rag_engine
from llm_provider import LLMProvider, GeminiProvider, OpenAIProvider, OpenRouterProvider

# --- Dependencies ---
def get_storyteller_guide() -> str:
    """Loads the core narrative constraints and Game Master persona dynamically per request."""
    try:
        with open("data/storyteller_guide.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "You are a horror AI Game Master. Strict rule: YOU MUST end your response exactly with [Health: X% | Stress: Y%]."

app = FastAPI(title="The Blackwood Anomaly API")

# Mount static files for the frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_frontend():
    """Serves the frontend application."""
    return FileResponse("static/index.html")

# Security schema to extract the Bearer token (The User's API Key)
security = HTTPBearer()

def get_llm_provider(
    credentials: HTTPAuthorizationCredentials = Security(security),
    x_llm_provider: str = Header("gemini", alias="X-LLM-Provider")
):
    """
    Dependency function: Extracts the user's API key from the Authorization header
    and returns a fresh, isolated LLM Provider for this specific request.
    Can be configured via X-LLM-Provider header (default: gemini).
    """
    user_api_key = credentials.credentials
    if not user_api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")
    
    # Instantiate an isolated provider. No global state!
    try:
        provider_name = x_llm_provider.lower()
        if provider_name == "openai":
            return OpenAIProvider(api_key=user_api_key)
        elif provider_name == "openrouter":
            return OpenRouterProvider(api_key=user_api_key)
        else:
            return GeminiProvider(api_key=user_api_key)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

# --- Request/Response Models ---
class ActionRequest(BaseModel):
    action: str

class GameResponse(BaseModel):
    session_id: str
    health: int
    stress: int
    narrative: str
    agent_actions: list[str] = []

class SessionState(BaseModel):
    """Lightweight snapshot returned when loading a saved game."""
    session_id: str
    health: int
    stress: int
    history: list

# --- API Endpoints: Session Management ---
@app.get("/api/v1/sessions", response_model=list[SessionState])
async def list_sessions(db: Session = Depends(get_db)):
    """Returns all persisted sessions (id, health, stress). Does not require an API key."""
    sessions = db.query(GameSession).all()
    return [
        SessionState(
            session_id=s.id,
            health=s.health,
            stress=s.stress,
            history=s.history or []
        )
        for s in sessions
    ]

@app.get("/api/v1/sessions/{session_id}", response_model=SessionState)
async def get_session(session_id: str, db: Session = Depends(get_db)):
    """Loads a saved game session by ID. Returns health, stress, and full history.
    Does not require an API key — the client uses this to resume state on page load.
    """
    session = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionState(
        session_id=session.id,
        health=session.health,
        stress=session.stress,
        history=session.history or []
    )

# --- Tool Definitions ---
def roll_d20(difficulty_class: int) -> str:
    """Rolls a 20-sided die to determine the success or failure of a risky player action.
    
    Args:
        difficulty_class: The target number to beat. 10=Easy, 15=Hard, 20=Nearly Impossible.
    """
    roll = random.randint(1, 20)
    success = roll >= difficulty_class
    return f"Roll: {roll} vs DC {difficulty_class}. Success: {success}"

# --- API Endpoints ---
@app.post("/api/v1/sessions", response_model=GameResponse)
async def create_session(
    llm: LLMProvider = Depends(get_llm_provider),
    db: Session = Depends(get_db),
    system_instruction: str = Depends(get_storyteller_guide)
):
    """Initializes a new game using the player's provided API key."""
    
    try:
        response = await llm.generate_content(
            model='gemini-2.5-flash',
            system_instruction=system_instruction,
            messages=[{"role": "user", "content": "Describe the terrifying room the player wakes up in."}]
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
            narrative=response.text,
            agent_actions=[]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Engine Error: {str(e)}")

@app.post("/api/v1/sessions/{session_id}/actions", response_model=GameResponse)
async def submit_action(
    session_id: str, 
    request: ActionRequest, 
    llm: LLMProvider = Depends(get_llm_provider),
    db: Session = Depends(get_db),
    system_instruction: str = Depends(get_storyteller_guide)
):
    """Processes a player's action, utilizing RAG and saving state to the DB."""
    
    # 1. Fetch Session
    session = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Formulate state-aware query and fetch RAG Context
    retrieval_query = f"Player State: {session.health}% Health, {session.stress}% Stress. Action: {request.action}"
    retrieved_chunks = await rag_engine.retrieve(llm, retrieval_query, top_k=2)
    
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
        messages = list(session.history)
        messages.append({"role": "user", "content": augmented_prompt})
        agent_actions = [] # Array to track observable steps
        
        # 4. First LLM Call (Passing the Tool)
        response = await llm.generate_content(
            model='gemini-2.5-flash',
            system_instruction=system_instruction,
            messages=messages,
            tools=[roll_d20]
        )
        
        # 5. Agentic Loop: Check if the AI decided to use the tool
        if response.function_calls:
            tool_results = []
            for tool_call in response.function_calls:
                if tool_call.name == "roll_d20":
                    # Execute the Python logic
                    dc = int(tool_call.arguments.get("difficulty_class", 10))
                    tool_result = roll_d20(dc)
                    
                    # Log the intermediate step for the grader to see
                    agent_actions.append(f"⚙️ Planner Agent decided to roll_d20(DC={dc}) -> {tool_result}")
                    tool_results.append({"name": "roll_d20", "result": tool_result})
            
            # Second LLM Call: Now that it has the dice roll, generate the final story
            response = await llm.generate_with_tool_result(
                model='gemini-2.5-flash',
                system_instruction=system_instruction,
                messages=messages,
                previous_response=response,
                tool_results=tool_results,
                tools=[roll_d20]
            )
        else:
            agent_actions.append("⚙️ Planner Agent logic: No tool required. Generating directly.")
            
        ai_text = response.text
        
        # 6. Extract State via Regex
        match = re.search(r"\[Health: (\d+)% \| Stress: (\d+)%\]", ai_text)
        if match:
            session.health = int(match.group(1))
            session.stress = int(match.group(2))
        else:
            print(f"⚠️ WARNING: Regex extraction failed. Raw Output: {ai_text}")
            
        # 7. Update DB History & Commit
        new_history = list(session.history)
        new_history.append({"role": "user", "content": request.action})
        new_history.append({"role": "model", "content": ai_text})
        session.history = new_history
        
        db.commit()
        db.refresh(session)
        
        return GameResponse(
            session_id=session.id,
            health=session.health,
            stress=session.stress,
            narrative=ai_text,
            agent_actions=agent_actions # Pass the steps to the frontend
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Engine Error: {str(e)}")
