from __future__ import annotations

from sqlalchemy import select
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    UsuarioSistema,
    PerfilUsuario,
    PerfilProfessor,
    PerfilRecepcionista,
    PerfilAluno,
    Clinica,
)
from ..core.security import hash_password, verify_password
import re


def validate_password_policy(senha: str) -> None:
    if not re.fullmatch(r"(?=.*[A-Za-z])(?=.*\d).{8,}", senha):
        raise ValueError("Senha não atende aos requisitos mínimos (>=8, letra e dígito)")


async def get_user_by_email(db: AsyncSession, email: str) -> UsuarioSistema | None:
    stmt = select(UsuarioSistema).where(UsuarioSistema.email == email)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def create_user(db: AsyncSession, *, nome: str, email: str, senha: str, perfil: PerfilUsuario, dados_perfil: dict | None = None, cpf: str | None = None) -> UsuarioSistema:
    validate_password_policy(senha)
    user = UsuarioSistema(
        nome=nome,
        email=email,
        senha_hash=hash_password(senha),
        perfil=perfil,
        cpf=cpf,
    )
    db.add(user)
    await db.flush()  # obtém user.id sem commit

    # cria registro de perfil específico (1:1) conforme o papel
    dados_perfil = dados_perfil or {}
    if perfil == PerfilUsuario.professor:
        if dados_perfil.get("clinica_id") is None:
            raise ValueError("clinica_id é obrigatório para professor")
        db.add(PerfilProfessor(
            user_id=user.id,
            especialidade=dados_perfil.get("especialidade"),
            clinica_id=dados_perfil.get("clinica_id"),
        ))
    elif perfil == PerfilUsuario.recepcionista:
        db.add(PerfilRecepcionista(user_id=user.id, telefone=dados_perfil.get("telefone")))
    elif perfil == PerfilUsuario.aluno:
        if dados_perfil.get("clinica_id") is None:
            raise ValueError("clinica_id é obrigatório para aluno")
        db.add(PerfilAluno(
            user_id=user.id,
            matricula=dados_perfil.get("matricula"),
            telefone=dados_perfil.get("telefone"),
            clinica_id=dados_perfil.get("clinica_id"),
        ))

    await db.commit()
    await db.refresh(user)
    return user


async def get_profile_data(db: AsyncSession, user: UsuarioSistema) -> dict | None:
    if user.perfil == PerfilUsuario.professor:
        res = await db.execute(select(PerfilProfessor).where(PerfilProfessor.user_id == user.id))
        p = res.scalar_one_or_none()
        if not p:
            return None
        data: dict[str, Any] = {"especialidade": p.especialidade}
        if p.clinica_id:
            c = await db.get(Clinica, p.clinica_id)
            if c:
                data["clinica"] = {"id": c.id, "codigo": c.codigo, "nome": c.nome}
            else:
                data["clinica_id"] = p.clinica_id
        return data
    if user.perfil == PerfilUsuario.recepcionista:
        res = await db.execute(select(PerfilRecepcionista).where(PerfilRecepcionista.user_id == user.id))
        p = res.scalar_one_or_none()
        return {"telefone": p.telefone} if p else None
    if user.perfil == PerfilUsuario.aluno:
        res = await db.execute(select(PerfilAluno).where(PerfilAluno.user_id == user.id))
        p = res.scalar_one_or_none()
        if not p:
            return None
        data: dict[str, Any] = {"matricula": p.matricula, "telefone": p.telefone}
        if p.clinica_id:
            c = await db.get(Clinica, p.clinica_id)
            if c:
                data["clinica"] = {"id": c.id, "codigo": c.codigo, "nome": c.nome}
            else:
                data["clinica_id"] = p.clinica_id
        return data
    return None


async def authenticate_user(db: AsyncSession, email: str, senha: str) -> UsuarioSistema | None:
    user = await get_user_by_email(db, email)
    if not user or not user.ativo:
        return None
    if not verify_password(senha, user.senha_hash):
        return None
    return user
