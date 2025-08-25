from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import UsuarioSistema, PerfilUsuario
from ..core.security import hash_password, verify_password, pwd_context
import re


async def get_user_by_email(db: AsyncSession, email: str) -> UsuarioSistema | None:
    stmt = select(UsuarioSistema).where(UsuarioSistema.email == email)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def create_user(db: AsyncSession, *, nome: str, email: str, senha: str, perfil: PerfilUsuario) -> UsuarioSistema:
    # Política simples de senha: mínimo 8 chars, pelo menos uma letra e um dígito
    if not re.fullmatch(r"(?=.*[A-Za-z])(?=.*\d).{8,}", senha):
        raise ValueError("Senha não atende aos requisitos mínimos (>=8, letra e dígito)")
    user = UsuarioSistema(
        nome=nome,
        email=email,
        senha_hash=hash_password(senha),
        perfil=perfil,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, senha: str) -> UsuarioSistema | None:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(senha, user.senha_hash):
        return None
    if not user.ativo:
        return None
    # Rehash automático se necessário (algoritmo atualizado / parâmetros)
    if pwd_context.needs_update(user.senha_hash):
        user.senha_hash = hash_password(senha)
        await db.commit()
    return user
