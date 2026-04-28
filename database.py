import os
import uuid
from sqlalchemy import create_engine, Column, String, Integer, JSON, DateTime, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

# Default to local SQLite; switch to PostgreSQL via DATABASE_URL in .env
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./blackwood.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class GameSession(Base):
    """
    SQLAlchemy Model for persisting a player's full game state.
    New columns are added gracefully via run_migrations() for existing databases.
    """
    __tablename__ = "game_sessions"

    id               = Column(String,  primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    health           = Column(Integer, default=100)
    stress           = Column(Integer, default=0)
    history          = Column(JSON,    default=list)
    # --- Extended state (Tier 1–3 additions) ---
    inventory        = Column(JSON,    default=list)          # max 4 items
    current_location = Column(String,  default="Intake Bay 4")
    visited_locations= Column(JSON,    default=list)
    discovered_lore  = Column(JSON,    default=list)          # list of fragment_ids
    escape_stage     = Column(Integer, default=0)             # 0–4; 4 = game won
    turn_count       = Column(Integer, default=0)
    player_name      = Column(String,  nullable=True)
    created_at       = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def run_migrations():
    """
    Adds new columns to existing game_sessions tables without dropping data.
    Safe to call on every startup — ignores errors for columns that already exist.
    """
    new_columns = [
        "ALTER TABLE game_sessions ADD COLUMN inventory TEXT DEFAULT '[]'",
        "ALTER TABLE game_sessions ADD COLUMN current_location TEXT DEFAULT 'Intake Bay 4'",
        "ALTER TABLE game_sessions ADD COLUMN visited_locations TEXT DEFAULT '[]'",
        "ALTER TABLE game_sessions ADD COLUMN discovered_lore TEXT DEFAULT '[]'",
        "ALTER TABLE game_sessions ADD COLUMN escape_stage INTEGER DEFAULT 0",
        "ALTER TABLE game_sessions ADD COLUMN turn_count INTEGER DEFAULT 0",
        "ALTER TABLE game_sessions ADD COLUMN player_name TEXT",
        "ALTER TABLE game_sessions ADD COLUMN created_at TEXT",
    ]
    with engine.connect() as conn:
        for sql in new_columns:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                conn.rollback()  # Column already exists — safe to skip


# FastAPI dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create tables then apply any pending column migrations
Base.metadata.create_all(bind=engine)
run_migrations()
