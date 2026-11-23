import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker

# Deterministic base directory to prevent relative path ambiguity
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SQLITE_PATH = os.path.join(BASE_DIR, "leadflow.db")

# Support environment-configured DATABASE_URL (for deployment on Render, Railway, Fly.io, etc.)
raw_db_url = os.environ.get("DATABASE_URL", "").strip().strip("'\"")
if not raw_db_url:
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH}"
else:
    SQLALCHEMY_DATABASE_URL = raw_db_url

# Convert legacy Heroku/Render postgres:// to postgresql:// for SQLAlchemy 2.0+
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

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
