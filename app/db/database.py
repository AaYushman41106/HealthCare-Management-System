from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.core.config import settings

# SQLite connection requires check_same_thread=False for multithreaded FastAPI requests
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

if settings.DATABASE_URL.startswith("sqlite"):
    import os
    raw_path = settings.DATABASE_URL.split("sqlite:///")[-1]
    dir_path = os.path.dirname(raw_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency yielding a database session per request and ensuring cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables according to defined ORM models."""
    import app.models  # noqa: F401 - ensures all models are registered
    Base.metadata.create_all(bind=engine)

    # Lightweight schema migration for SQLite development files
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            # Check users table columns
            res = conn.execute(text("PRAGMA table_info(users)"))
            user_cols = [row[1] for row in res.fetchall()]
            if user_cols:
                if "failed_login_attempts" not in user_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0 NOT NULL"))
                if "locked_until" not in user_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN locked_until DATETIME"))

            # Check doctors table columns
            res_doc = conn.execute(text("PRAGMA table_info(doctors)"))
            doc_cols = [row[1] for row in res_doc.fetchall()]
            if doc_cols:
                if "is_active" not in doc_cols:
                    conn.execute(text("ALTER TABLE doctors ADD COLUMN is_active BOOLEAN DEFAULT 1 NOT NULL"))

            conn.commit()
    except Exception:
        pass
