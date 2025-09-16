from __future__ import annotations

import os
import pathlib
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from src.backend.main import app
from src.backend.database import Base, get_db
from src.backend.core.security import hash_password
from src.backend.models import UsuarioSistema, PerfilUsuario

"""Configuração de fixtures de teste.

Por padrão usamos SQLite (arquivo) para tornar os testes independentes de um servidor
PostgreSQL local. Caso queira forçar uso de Postgres, defina a env TEST_DATABASE_URL.
Ex: TEST_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db_test
"""

DEFAULT_SQLITE_PATH = pathlib.Path("./test_app.db").absolute()
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL") or f"sqlite+aiosqlite:///{DEFAULT_SQLITE_PATH}"

# Engine isolado sem pool persistente para testes
is_sqlite = TEST_DATABASE_URL.startswith("sqlite+")

engine_test = create_async_engine(
    TEST_DATABASE_URL,
    future=True,
    echo=False,
    poolclass=NullPool,
)
SessaoTeste = async_sessionmaker(bind=engine_test, expire_on_commit=False, class_=AsyncSession)


async def override_get_db():
    async with SessaoTeste() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True, scope="session")
async def preparar_schema():
    """Cria e derruba o schema para a suite de testes.

    Em SQLite arquivo removido ao final; em Postgres drop das tabelas.
    """
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    # Limpar arquivo SQLite
    if is_sqlite and DEFAULT_SQLITE_PATH.exists():
        try:
            DEFAULT_SQLITE_PATH.unlink()
        except OSError:
            pass


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:  # type: ignore[override]
    async with SessaoTeste() as sessao:  # noqa: SIM117
        yield sessao


@pytest_asyncio.fixture
async def cliente() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture
async def usuario_admin(db_session: AsyncSession):
    from sqlalchemy import select

    stmt = select(UsuarioSistema).where(UsuarioSistema.email == "admin@exemplo.com")
    res = await db_session.execute(stmt)
    admin = res.scalar_one_or_none()
    if not admin:
        admin = UsuarioSistema(
            nome="Administrador",
            email="admin@exemplo.com",
            senha_hash=hash_password("admin123"),
            perfil=PerfilUsuario.admin,
            ativo=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def usuario_recepcionista(db_session: AsyncSession):
    from sqlalchemy import select

    stmt = select(UsuarioSistema).where(UsuarioSistema.email == "recep@exemplo.com")
    res = await db_session.execute(stmt)
    recep = res.scalar_one_or_none()
    if not recep:
        recep = UsuarioSistema(
            nome="Recepcionista",
            email="recep@exemplo.com",
            senha_hash=hash_password("recep123"),
            perfil=PerfilUsuario.recepcionista,
            ativo=True,
        )
        db_session.add(recep)
        await db_session.commit()
        await db_session.refresh(recep)
    return recep


@pytest_asyncio.fixture
async def usuario_aluno(db_session: AsyncSession):
    from sqlalchemy import select

    stmt = select(UsuarioSistema).where(UsuarioSistema.email == "aluno@exemplo.com")
    res = await db_session.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        user = UsuarioSistema(
            nome="Aluno",
            email="aluno@exemplo.com",
            senha_hash=hash_password("aluno123"),
            perfil=PerfilUsuario.aluno,
            ativo=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
    return user
