import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker

# Deterministic base directory to prevent relative path ambiguity
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SQLITE_PATH = os.path.join(BASE_DIR, "leadflow.db")

def normalize_database_url(url: str) -> str:
    """
    Normalizes database connection URLs:
    - Strips whitespace and surrounding quotes
    - Converts postgres:// and generic postgresql:// to explicit postgresql+psycopg2://
      dialect to ensure SQLAlchemy loads the installed psycopg2 driver rather than psycopg 3
    - Falls back to local SQLite if URL is empty
    """
    cleaned = (url or "").strip().strip("'\"")
    if not cleaned:
        return f"sqlite:///{DEFAULT_SQLITE_PATH}"

    # Explicitly map PostgreSQL schemes to postgresql+psycopg2 dialect
    if cleaned.startswith("postgres://"):
        return cleaned.replace("postgres://", "postgresql+psycopg2://", 1)
    elif cleaned.startswith("postgresql://"):
        return cleaned.replace("postgresql://", "postgresql+psycopg2://", 1)
    elif cleaned.startswith("postgresql+psycopg://"):
        return cleaned.replace("postgresql+psycopg://", "postgresql+psycopg2://", 1)

    return cleaned

# Support environment-configured DATABASE_URL (for deployment on Render, Railway, Fly.io, etc.)
raw_db_url = os.environ.get("DATABASE_URL", "")
SQLALCHEMY_DATABASE_URL = normalize_database_url(raw_db_url)

# Configure engine appropriately for SQLite vs PostgreSQL / MySQL
is_sqlite = SQLALCHEMY_DATABASE_URL.startswith("sqlite")

if is_sqlite:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

    # Enable WAL mode for high-performance concurrent SQLite operations
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
        except Exception:
            pass
else:
    # Production connection pool for PostgreSQL
    connect_args = {}
    # Ensure SSL is requested for Render PostgreSQL if not already in URL
    if "sslmode" not in SQLALCHEMY_DATABASE_URL:
        if os.environ.get("RENDER") == "true" or "render.com" in SQLALCHEMY_DATABASE_URL or "dpg-" in SQLALCHEMY_DATABASE_URL:
            connect_args["sslmode"] = "require"

    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        connect_args=connect_args
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base
Base = declarative_base()

# Dependency to get DB session in FastAPI endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
