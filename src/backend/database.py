from __future__ import annotations

from typing import AsyncGenerator
import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy import event
from datetime import datetime, timezone


class Base(DeclarativeBase):
    pass


def get_database_url() -> str:
    """Build DB URL from environment variables.

    Expected env vars:
      - DB_USER
      - DB_PASSWORD
      - DB_HOST (default: localhost)
      - DB_PORT (default: 5432)
      - DB_NAME
    Falls back to a local dev PostgreSQL URL if not all provided.
    """
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "clinisysschool")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"


DATABASE_URL = get_database_url()

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


@event.listens_for(Session, "before_flush")
def _update_timestamp(session, flush_context, instances):  # type: ignore[unused-argument]
    """Garante updated_at em objetos alterados sem depender de trigger DB.

    Apenas se atributo existir.
    """
    agora = datetime.now(timezone.utc)
    for obj in session.dirty:
        if hasattr(obj, "updated_at") and session.is_modified(obj, include_collections=False):
            try:
                setattr(obj, "updated_at", agora)
            except Exception:
                pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session."""
    async with SessionLocal() as session:  # type: ignore[call-arg]
        try:
            yield session
        finally:
            # session is closed automatically by context manager
            pass
