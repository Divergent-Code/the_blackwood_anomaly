import os
import uuid
from sqlalchemy import create_engine, Column, String, Integer, JSON
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# We default to a local SQLite database so you can test immediately without Docker,
# but you can easily switch to PostgreSQL by setting DATABASE_URL in your .env
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./blackwood.db")

# SQLite specific arguments (PostgreSQL will ignore this if we check the dialect)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class GameSession(Base):
    """
    SQLAlchemy Model for persisting a player's game state.
    """
    __tablename__ = "game_sessions"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    health = Column(Integer, default=100)
    stress = Column(Integer, default=0)
    # Storing history as JSON allows us to keep the full prompt context
    # for when we implement the LLM call in the submit_action endpoint
    history = Column(JSON, default=list)

# FastAPI Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables automatically for now.
# (In a production environment, we'd use Alembic for migrations)
Base.metadata.create_all(bind=engine)
