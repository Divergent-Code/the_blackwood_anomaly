from fastapi import FastAPI, Depends, HTTPException, Security, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db, GameSession
import re
import random
from app.rag import rag_engine
from app.llm_provider import LLMProvider, GeminiProvider, OpenAIProvider, OpenRouterProvider

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

def get_storyteller_guide() -> str:
    """Loads the Game Master persona and rules dynamically per request."""
    try:
        with open("data/storyteller_guide.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "You are a horror AI Game Master. Call apply_vitals() to update health/stress."


app = FastAPI(title="The Blackwood Anomaly API")
app.mount("/static", StaticFiles(directory="static"), name="static")

security = HTTPBearer()


@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")


def get_llm_provider(
    credentials: HTTPAuthorizationCredentials = Security(security),
    x_llm_provider: str = Header("gemini", alias="X-LLM-Provider"),
) -> LLMProvider:
    """Extracts API key and returns an isolated LLM provider for this request."""
    user_api_key = credentials.credentials
    if not user_api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")
    try:
        name = x_llm_provider.lower()
        if name == "openai":
            return OpenAIProvider(api_key=user_api_key)
        elif name == "openrouter":
            return OpenRouterProvider(api_key=user_api_key)
        else:
            return GeminiProvider(api_key=user_api_key)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class ActionRequest(BaseModel):
    action: str


class GameResponse(BaseModel):
    session_id: str
    health: int
    stress: int
    narrative: str
    agent_actions: list[str] = []
    inventory: list[str] = []
    current_location: str = "Intake Bay 4"
    discovered_lore: list[str] = []
    escape_stage: int = 0
    turn_count: int = 0
    game_over: bool = False
    game_won: bool = False
    panic_cascade: bool = False


class SessionState(BaseModel):
    session_id: str
    health: int
    stress: int
    history: list
    inventory: list = []
    current_location: str = "Intake Bay 4"
    discovered_lore: list = []
    escape_stage: int = 0
    turn_count: int = 0


class RecapResponse(BaseModel):
    recap: str


# ---------------------------------------------------------------------------
# Agentic Tool Definitions
# The function BODIES are fallbacks only — the agentic loop in submit_action
# intercepts each call and applies state changes directly on the session object.
# The docstrings are what the LLM reads to understand each tool's contract.
# ---------------------------------------------------------------------------

def roll_d20(difficulty_class: int) -> str:
    """Rolls a 20-sided die to determine the success or failure of a risky player
    action. Consult combat_mechanics.md Dice Protocol for when to call this.

    Args:
        difficulty_class: The DC target (8=Very Easy, 10=Easy, 12=Moderate,
            15=Hard, 18=Very Hard, 20=Nearly Impossible).
    """
    roll = random.randint(1, 20)
    success = roll >= difficulty_class
    return f"Roll: {roll} vs DC {difficulty_class}. Success: {success}"


def apply_vitals(health_delta: int, stress_delta: int) -> str:
    """Updates Subject 814's health and stress after any event that changes them
    (damage taken, stress from environment, healing, panic cascade, etc.).
    Call this INSTEAD of writing [Health: X% | Stress: Y%] in the narrative.

    Args:
        health_delta: Integer change to health (-100 to +100). Negative = damage.
        stress_delta: Integer change to stress (-100 to +100). Positive = more stress.
    """
    return f"Vitals delta queued: health={health_delta}, stress={stress_delta}"


def add_item(item_name: str) -> str:
    """Adds an item to Subject 814's inventory. Maximum 4 slots. If inventory is
    full, the player MUST be told to drop something first — do not call add_item
    until they confirm what to drop.

    Args:
        item_name: Descriptive name of the item (e.g. 'Dr. Voss's Badge',
            'Bone Saw Fragment', 'Hypodermic Needle').
    """
    return f"add_item queued: {item_name}"


def remove_item(item_name: str) -> str:
    """Removes an item from Subject 814's inventory (used, dropped, or destroyed).

    Args:
        item_name: Exact name of the item as it appears in inventory.
    """
    return f"remove_item queued: {item_name}"


def move_to_location(location_name: str) -> str:
    """Updates Subject 814's current location when they successfully move to a
    new zone. Use exact zone names from institute_map.md.

    Args:
        location_name: Canonical zone name (e.g. 'Surgery Wing', 'Morgue Corridor').
    """
    return f"move_to_location queued: {location_name}"


def discover_lore(fragment_id: str) -> str:
    """Marks a lore fragment as discovered. Call when the player finds a document,
    terminal entry, or audio log defined in lore_fragments.md.

    Args:
        fragment_id: The exact fragment ID (e.g. 'intake_file_814', 'voss_log_pre').
    """
    return f"discover_lore queued: {fragment_id}"


def advance_escape_stage() -> str:
    """Advances the player's escape progress by one stage (max 4). Call only when
    the player has genuinely completed a stage requirement from escape_route.md.
    Stage 4 triggers the game-won condition.
    """
    return "advance_escape_stage queued"


ALL_TOOLS = [
    roll_d20, apply_vitals, add_item, remove_item,
    move_to_location, discover_lore, advance_escape_stage,
]


# ---------------------------------------------------------------------------
# Agentic Loop Helper
# ---------------------------------------------------------------------------

def _execute_tool_call(tool_call, session: GameSession) -> tuple[str, str]:
    """
    Executes a single tool call against the live session object.
    Returns (tool_result_string, agent_action_log_string).
    """
    name = tool_call.name
    args = tool_call.arguments

    if name == "roll_d20":
        dc = max(1, min(20, int(args.get("difficulty_class", 10))))
        result = roll_d20(dc)
        log = f"⚙️ roll_d20(DC={dc}) → {result}"

    elif name == "apply_vitals":
        h = max(-100, min(100, int(args.get("health_delta", 0))))
        s = max(-100, min(100, int(args.get("stress_delta", 0))))
        session.health = max(0, min(100, session.health + h))
        session.stress = max(0, min(100, session.stress + s))
        result = f"Vitals updated — Health: {session.health}%, Stress: {session.stress}%"
        log = f"⚙️ apply_vitals(Δhealth={h}, Δstress={s}) → {result}"

    elif name == "add_item":
        item = args.get("item_name", "").strip()
        inventory = list(session.inventory or [])
        if len(inventory) >= 4:
            result = f"INVENTORY FULL (4/4). Cannot add '{item}' — player must drop an item first."
        elif item in inventory:
            result = f"'{item}' already in inventory."
        else:
            inventory.append(item)
            session.inventory = inventory
            result = f"Added '{item}'. Inventory ({len(inventory)}/4): {', '.join(inventory)}"
        log = f"⚙️ add_item('{item}') → {result}"

    elif name == "remove_item":
        item = args.get("item_name", "").strip()
        inventory = list(session.inventory or [])
        if item in inventory:
            inventory.remove(item)
            session.inventory = inventory
            result = f"Removed '{item}'. Inventory ({len(inventory)}/4): {', '.join(inventory) or 'empty'}"
        else:
            result = f"'{item}' not found in inventory."
        log = f"⚙️ remove_item('{item}') → {result}"

    elif name == "move_to_location":
        location = args.get("location_name", "").strip()
        session.current_location = location
        visited = list(session.visited_locations or [])
        if location not in visited:
            visited.append(location)
            session.visited_locations = visited
        result = f"Location set: {location}"
        log = f"⚙️ move_to_location('{location}') → {result}"

    elif name == "discover_lore":
        fid = args.get("fragment_id", "").strip()
        discovered = list(session.discovered_lore or [])
        if fid not in discovered:
            discovered.append(fid)
            session.discovered_lore = discovered
            result = f"Lore fragment '{fid}' added to dossier."
        else:
            result = f"Fragment '{fid}' already discovered."
        log = f"⚙️ discover_lore('{fid}') → {result}"

    elif name == "advance_escape_stage":
        stage = session.escape_stage or 0
        if stage < 4:
            session.escape_stage = stage + 1
            result = f"Escape stage advanced to {session.escape_stage}/4."
        else:
            result = "Escape stage already at maximum (4/4)."
        log = f"⚙️ advance_escape_stage() → {result}"

    else:
        result = f"Unknown tool: {name}"
        log = f"⚙️ {name}() → {result}"

    return result, log


# ---------------------------------------------------------------------------
# Session Management Endpoints (no LLM key required)
# ---------------------------------------------------------------------------

@app.get("/api/v1/sessions", response_model=list[SessionState])
async def list_sessions(db: Session = Depends(get_db)):
    """Lists all persisted sessions."""
    sessions = db.query(GameSession).all()
    return [
        SessionState(
            session_id=s.id,
            health=s.health,
            stress=s.stress,
            history=s.history or [],
            inventory=s.inventory or [],
            current_location=s.current_location or "Intake Bay 4",
            discovered_lore=s.discovered_lore or [],
            escape_stage=s.escape_stage or 0,
            turn_count=s.turn_count or 0,
        )
        for s in sessions
    ]


@app.get("/api/v1/sessions/{session_id}", response_model=SessionState)
async def get_session(session_id: str, db: Session = Depends(get_db)):
    """Loads a saved session by ID — used by the frontend to resume a game."""
    session = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionState(
        session_id=session.id,
        health=session.health,
        stress=session.stress,
        history=session.history or [],
        inventory=session.inventory or [],
        current_location=session.current_location or "Intake Bay 4",
        discovered_lore=session.discovered_lore or [],
        escape_stage=session.escape_stage or 0,
        turn_count=session.turn_count or 0,
    )


@app.post("/api/v1/sessions/{session_id}/recap", response_model=RecapResponse)
async def get_session_recap(
    session_id: str,
    llm: LLMProvider = Depends(get_llm_provider),
    db: Session = Depends(get_db),
    system_instruction: str = Depends(get_storyteller_guide),
):
    """Generates an AI atmospheric summary of a previous session."""
    session = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    history = session.history or []
    if not history:
        return RecapResponse(recap="No prior events recorded. Subject 814's file is blank.")

    transcript = "\n\n".join(
        f"{'SUBJECT 814' if m.get('role') == 'user' else 'INSTITUTE LOG'}: {m.get('content', '')}"
        for m in history
    )
    recap_prompt = (
        f"Recap the session.\n\n=== SESSION TRANSCRIPT ===\n{transcript}\n\n"
        f"Current vitals — Health: {session.health}%, Stress: {session.stress}%.\n"
        f"Location: {session.current_location or 'Intake Bay 4'}. "
        f"Escape stage: {session.escape_stage or 0}/4."
    )
    try:
        response = await llm.generate_content(
            model="gemini-2.5-flash",
            system_instruction=system_instruction,
            messages=[{"role": "user", "content": recap_prompt}],
        )
        return RecapResponse(recap=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recap generation failed: {str(e)}")


# ---------------------------------------------------------------------------
# Game Endpoints (LLM key required)
# ---------------------------------------------------------------------------

@app.post("/api/v1/sessions", response_model=GameResponse)
async def create_session(
    llm: LLMProvider = Depends(get_llm_provider),
    db: Session = Depends(get_db),
    system_instruction: str = Depends(get_storyteller_guide),
):
    """Initializes a new game session."""
    try:
        response = await llm.generate_content(
            model="gemini-2.5-flash",
            system_instruction=system_instruction,
            messages=[{
                "role": "user",
                "content": (
                    "Start the game. Describe the exact moment Subject 814 wakes up "
                    "in the Blackwood Institute. Establish the sensory details of the room, "
                    "the surgical staples on their neck, and give them their first prompt "
                    "to action. Be brief and punchy."
                ),
            }],
        )

        new_session = GameSession(
            health=100,
            stress=0,
            inventory=[],
            current_location="Intake Bay 4",
            visited_locations=["Intake Bay 4"],
            discovered_lore=[],
            escape_stage=0,
            turn_count=0,
            history=[{"role": "model", "content": response.text}],
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)

        return GameResponse(
            session_id=new_session.id,
            health=new_session.health,
            stress=new_session.stress,
            narrative=response.text,
            inventory=[],
            current_location="Intake Bay 4",
            discovered_lore=[],
            escape_stage=0,
            turn_count=0,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Engine Error: {str(e)}")


@app.post("/api/v1/sessions/{session_id}/actions", response_model=GameResponse)
async def submit_action(
    session_id: str,
    request: ActionRequest,
    llm: LLMProvider = Depends(get_llm_provider),
    db: Session = Depends(get_db),
    system_instruction: str = Depends(get_storyteller_guide),
):
    """Processes a player action through the full agentic loop."""

    # 1. Fetch session
    session = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Block dead/won sessions
    if (session.health or 100) <= 0:
        raise HTTPException(status_code=409, detail="Session ended — subject deceased.")
    if (session.escape_stage or 0) >= 4:
        raise HTTPException(status_code=409, detail="Session ended — subject escaped.")

    # 3. RAG retrieval
    retrieval_query = (
        f"Location: {session.current_location or 'Intake Bay 4'}. "
        f"Health: {session.health}%, Stress: {session.stress}%. "
        f"Escape stage: {session.escape_stage or 0}/4. "
        f"Action: {request.action}"
    )
    retrieved_chunks = await rag_engine.retrieve(llm, retrieval_query, top_k=3)
    rag_context_str = "\n\n".join(c["content"] for c in retrieved_chunks)

    # 4. Build augmented prompt
    inventory_str = ", ".join(session.inventory or []) or "empty"
    lore_str = ", ".join(session.discovered_lore or []) or "none"
    augmented_prompt = (
        f"=== RETRIEVED GAME MECHANICS ===\n{rag_context_str}\n\n"
        f"=== CURRENT GAME STATE ===\n"
        f"Location: {session.current_location or 'Intake Bay 4'}\n"
        f"Health: {session.health}% | Stress: {session.stress}%\n"
        f"Inventory ({len(session.inventory or [])}/4): {inventory_str}\n"
        f"Escape stage: {session.escape_stage or 0}/4\n"
        f"Lore discovered: {lore_str}\n\n"
        f"=== PLAYER ACTION ===\n{request.action}"
    )

    try:
        messages = list(session.history or [])
        messages.append({"role": "user", "content": augmented_prompt})
        agent_actions: list[str] = []
        vitals_updated_by_tool = False

        # 5. First LLM call
        response = await llm.generate_content(
            model="gemini-2.5-flash",
            system_instruction=system_instruction,
            messages=messages,
            tools=ALL_TOOLS,
        )

        # 6. Agentic loop
        if response.function_calls:
            tool_results = []
            for tool_call in response.function_calls:
                tool_result, log = _execute_tool_call(tool_call, session)
                agent_actions.append(log)
                tool_results.append({"name": tool_call.name, "result": tool_result})
                if tool_call.name == "apply_vitals":
                    vitals_updated_by_tool = True

            # Second LLM call with tool results
            response = await llm.generate_with_tool_result(
                model="gemini-2.5-flash",
                system_instruction=system_instruction,
                messages=messages,
                previous_response=response,
                tool_results=tool_results,
                tools=ALL_TOOLS,
            )
        else:
            agent_actions.append("⚙️ No tool required — narrating directly.")

        ai_text = response.text

        # 7. Regex fallback for vitals (only if apply_vitals was not called)
        if not vitals_updated_by_tool:
            match = re.search(r"\[Health: (\d+)% \| Stress: (\d+)%\]", ai_text)
            if match:
                session.health = int(match.group(1))
                session.stress = int(match.group(2))
                agent_actions.append("⚙️ Vitals extracted via regex fallback.")

        # 8. Derived game state flags
        game_over = (session.health or 0) <= 0
        game_won  = (session.escape_stage or 0) >= 4
        panic_cascade = (session.stress or 0) >= 80

        # 9. Increment turn and persist history
        session.turn_count = (session.turn_count or 0) + 1
        new_history = list(session.history or [])
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
            agent_actions=agent_actions,
            inventory=session.inventory or [],
            current_location=session.current_location or "Intake Bay 4",
            discovered_lore=session.discovered_lore or [],
            escape_stage=session.escape_stage or 0,
            turn_count=session.turn_count,
            game_over=game_over,
            game_won=game_won,
            panic_cascade=panic_cascade,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Engine Error: {str(e)}")
