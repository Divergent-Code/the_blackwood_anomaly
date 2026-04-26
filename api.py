from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from google import genai # Using the modern GenAI client for isolated requests

app = FastAPI(title="The Blackwood Anomaly API")

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
        raise HTTPException(status_code=401, detail="Invalid API Key format")

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
async def create_session(client: genai.Client = Depends(get_gemini_client)):
    """Initializes a new game using the player's provided API key."""
    
    system_prompt = "You are a horror Game Master. The game has just started..."
    
    try:
        # We pass the prompt directly using the user's isolated client
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents="Describe the terrifying room the player wakes up in.",
            config={"system_instruction": system_prompt}
        )
        
        # TODO: Save new session to PostgreSQL here
        
        return GameResponse(
            session_id="new-uuid-1234",
            health=100,
            stress=0,
            narrative=response.text
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Engine Error: {str(e)}")

@app.post("/api/v1/sessions/{session_id}/actions", response_model=GameResponse)
async def submit_action(session_id: str, request: ActionRequest, client: genai.Client = Depends(get_gemini_client)):
    """Processes a player's action using their API key and updates the database."""
    
    # TODO: 1. Fetch current health/stress from PostgreSQL using session_id
    # TODO: 2. Run RAG Retrieval
    # TODO: 3. Call AI with the client.models.generate_content()
    # TODO: 4. Extract new stats via Regex
    # TODO: 5. Update PostgreSQL
    
    return GameResponse(
        session_id=session_id,
        health=80, # Mocked for now
        stress=15, # Mocked for now
        narrative=f"You tried to '{request.action}'. It didn't go well."
    )
