"""
SQLAlchemy engine, session factory, and database dependency for PostgreSQL persistence (Phase 11).
"""
import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# Base class for all ORM models
Base = declarative_base()

# Configure SQLAlchemy engine with connection pooling and pre-ping
def _get_engine():
    """
    Creates the SQLAlchemy engine with PostgreSQL connection pooling.
    If PostgreSQL is unreachable (e.g. during local tests or environments where Postgres service is not running),
    falls back gracefully to SQLite file database with schema auto-generation.
    """
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql"):
        try:
            pg_engine = create_engine(
                db_url,
                pool_pre_ping=True,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                echo=settings.DB_ECHO,
                connect_args={"connect_timeout": 1},
            )
            with pg_engine.connect():
                pass
            return pg_engine
        except Exception as e:
            logger.warning(
                "PostgreSQL connection failed (%s); falling back to SQLite for persistence.",
                e,
            )
            sqlite_engine = create_engine(
                "sqlite:////tmp/ai_resume_parser.db",
                connect_args={"check_same_thread": False},
            )
            try:
                import backend.app.models.resume_models  # noqa: F401
                import backend.app.models.embedding_models  # noqa: F401
                Base.metadata.create_all(sqlite_engine)
            except Exception as meta_err:
                logger.warning("Failed to auto-create SQLite tables: %s", meta_err)
            return sqlite_engine
    elif db_url.startswith("sqlite"):
        sqlite_engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
        )
        try:
            import backend.app.models.resume_models  # noqa: F401
            import backend.app.models.embedding_models  # noqa: F401
            Base.metadata.create_all(sqlite_engine)
        except Exception:
            pass
        return sqlite_engine
    return create_engine(
        db_url,
        pool_pre_ping=True,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        echo=settings.DB_ECHO,
    )


engine = _get_engine()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a SQLAlchemy session per request.
    Ensures safe session commit/rollback and automatic cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
