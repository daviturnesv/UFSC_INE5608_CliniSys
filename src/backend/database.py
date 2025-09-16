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
    """Resolve a URL de banco de dados.

    Ordem de precedência:
    1) DATABASE_URL (env padrão)
    2) APP_DATABASE_URL (env com prefixo do projeto)
    3) Monta a partir de Settings (.env via pydantic): APP_DB_*
    """
    # 1) Override direto via env
    direct = os.getenv("DATABASE_URL") or os.getenv("APP_DATABASE_URL")
    if direct:
        return direct

    # 2) Monta a partir das variáveis carregadas por Settings
    from .core.config import get_settings  # lazy import para evitar ciclos

    s = get_settings()
    user = str(getattr(s, "db_user", "postgres"))
    password = str(getattr(s, "db_password", "postgres"))
    host = str(getattr(s, "db_host", "localhost"))
    port = str(getattr(s, "db_port", 5432))
    name = str(getattr(s, "db_name", "clinisysschool"))
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
