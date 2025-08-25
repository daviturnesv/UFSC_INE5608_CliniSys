from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.refresh_token import RefreshToken
from ..models import UsuarioSistema
from ..core.security import hash_password, verify_password
from ..core.config import get_settings


def _agora() -> datetime:
    return datetime.now(timezone.utc)


async def criar_refresh_token(db: AsyncSession, usuario: UsuarioSistema) -> tuple[str, RefreshToken]:
    """Gera string aleatória (plaintext) e persiste hash + metadados.

    Retorna (plaintext, instancia persistida)
    """
    settings = get_settings()
    raw = secrets.token_urlsafe(48)
    expira = _agora() + timedelta(minutes=settings.refresh_token_expire_minutes)
    rt = RefreshToken(
        usuario_id=usuario.id,
        token_hash=hash_password(raw),
        expira_em=expira,
        criado_em=_agora(),
    )
    db.add(rt)
    await db.commit()
    await db.refresh(rt)
    return raw, rt


async def obter_refresh_token_valido(db: AsyncSession, usuario: UsuarioSistema, raw_token: str) -> RefreshToken | None:
    # Busca tokens não revogados e não expirados do usuário (poderia otimizar com filtro mais específico)
    stmt = select(RefreshToken).where(RefreshToken.usuario_id == usuario.id, RefreshToken.revogado.is_(False))
    res = await db.execute(stmt)
    tokens = res.scalars().all()
    agora = _agora()
    for t in tokens:
        if t.expira_em < agora:
            continue
        if verify_password(raw_token, t.token_hash):
            return t
    return None


async def revogar_refresh_token(db: AsyncSession, token: RefreshToken) -> None:
    token.revogado = True
    await db.commit()


async def rotacionar_refresh_token(db: AsyncSession, usuario: UsuarioSistema, antigo: RefreshToken | None) -> tuple[str, RefreshToken]:
    if antigo:
        antigo.revogado = True
    novo_raw, novo = await criar_refresh_token(db, usuario)
    return novo_raw, novo
