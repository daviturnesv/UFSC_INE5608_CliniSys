from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
import secrets
import hashlib

from ..models.refresh_token import RefreshToken
from ..models.usuario import UsuarioSistema


def _hash_token(token: str) -> str:
    """Gera hash SHA-256 do token"""
    return hashlib.sha256(token.encode()).hexdigest()


def _generate_token() -> str:
    """Gera um token aleatório seguro"""
    return secrets.token_urlsafe(32)


async def create_refresh_token(
    session: AsyncSession,
    usuario_id: int,
    expires_in_days: int = 30
) -> tuple[str, RefreshToken]:
    """
    Cria um novo refresh token para o usuário
    
    Returns:
        tuple: (token_plain, refresh_token_obj)
    """
    token_plain = _generate_token()
    token_hash = _hash_token(token_plain)
    
    expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
    
    refresh_token = RefreshToken(
        usuario_id=usuario_id,
        token_hash=token_hash,
        expira_em=expires_at,
        criado_em=datetime.now(timezone.utc),
        revogado=False
    )
    
    session.add(refresh_token)
    await session.commit()
    await session.refresh(refresh_token)
    
    return token_plain, refresh_token


async def get_refresh_token_by_token(
    session: AsyncSession,
    token: str
) -> Optional[RefreshToken]:
    """Busca refresh token pelo token (não hash)"""
    token_hash = _hash_token(token)
    
    stmt = select(RefreshToken).where(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revogado == False,
        RefreshToken.expira_em > datetime.now(timezone.utc)
    )
    
    result = await session.execute(stmt)
    return result.scalars().first()


async def revoke_refresh_token(
    session: AsyncSession,
    token: str
) -> bool:
    """Revoga um refresh token"""
    refresh_token = await get_refresh_token_by_token(session, token)
    
    if refresh_token:
        refresh_token.revogado = True
        await session.commit()
        return True
    
    return False


async def revoke_all_user_tokens(
    session: AsyncSession,
    usuario_id: int
) -> int:
    """Revoga todos os tokens de um usuário. Retorna quantidade revogada"""
    stmt = select(RefreshToken).where(
        RefreshToken.usuario_id == usuario_id,
        RefreshToken.revogado == False
    )
    
    result = await session.execute(stmt)
    tokens = result.scalars().all()
    
    count = 0
    for token in tokens:
        token.revogado = True
        count += 1
    
    if count > 0:
        await session.commit()
    
    return count


async def cleanup_expired_tokens(session: AsyncSession) -> int:
    """Remove tokens expirados do banco. Retorna quantidade removida"""
    stmt = delete(RefreshToken).where(
        RefreshToken.expira_em < datetime.now(timezone.utc)
    )
    
    result = await session.execute(stmt)
    await session.commit()
    
    return result.rowcount or 0
