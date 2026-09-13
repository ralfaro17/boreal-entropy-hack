import os
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Load environment variables from .env if present
load_dotenv()


def get_database_url() -> str | URL:
    """Build or retrieve the database connection URL."""
    custom_url = os.getenv("DATABASE_URL")
    if custom_url:
        # Normalize postgres / postgresql prefix to postgresql+psycopg driver
        if custom_url.startswith("postgres://"):
            return custom_url.replace("postgres://", "postgresql+psycopg://", 1)
        if custom_url.startswith("postgresql://") and "+psycopg" not in custom_url:
            return custom_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return custom_url

    user = os.getenv("DB_USER", "boreal")
    password = os.getenv("DB_PASSWORD", "porfavor1,")
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", "5432"))
    dbname = os.getenv("DB_NAME", "entropy")

    return URL.create(
        drivername="postgresql+psycopg",
        username=user,
        password=password,
        host=host,
        port=port,
        database=dbname,
    )


DATABASE_URL = get_database_url()

# Create the SQLAlchemy engine with connection pool pre-ping
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

# Factory for creating database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy ORM models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy database session and ensures it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all database tables defined in the metadata."""
    import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def check_db_connection() -> bool:
    """Test database connectivity with a lightweight query."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

