from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas import UsuarioCreate, Usuario
from ..models import UsuarioSistema, PerfilUsuario  # usar enum do modelo para tipagem
from ..crud.usuario import create_user, get_user_by_email, validate_password_policy
from sqlalchemy import select, update, func
from ..core.resposta import envelope_resposta
from .auth import get_current_user

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


def require_admin(user: UsuarioSistema) -> None:
    if user.perfil != PerfilUsuario.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")


@router.post("/", status_code=status.HTTP_201_CREATED)
async def criar_usuario(
    payload: UsuarioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioSistema = Depends(get_current_user),
):
    require_admin(current_user)
    existente = await get_user_by_email(db, payload.email)
    if existente:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    perfil = PerfilUsuario(payload.perfil.value)  # garantir enum correto
    try:
        user = await create_user(db, nome=payload.nome, email=payload.email, senha=payload.senha, perfil=perfil)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return envelope_resposta(True, Usuario.model_validate(user).model_dump())


@router.get("/")
async def listar_usuarios(
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioSistema = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    perfil: Optional[PerfilUsuario] = Query(None),
    ativo: Optional[bool] = Query(None),
):
    require_admin(current_user)
    base = select(UsuarioSistema)
    filtros = []
    if perfil is not None:
        filtros.append(UsuarioSistema.perfil == perfil)
    if ativo is not None:
        filtros.append(UsuarioSistema.ativo == ativo)
    if filtros:
        for f in filtros:
            base = base.where(f)

    # total
    total_stmt = select(func.count()).select_from(UsuarioSistema)
    if filtros:
        for f in filtros:
            total_stmt = total_stmt.where(f)
    total = (await db.execute(total_stmt)).scalar_one()

    pagina_stmt = base.order_by(UsuarioSistema.id).offset(skip).limit(limit)
    res = await db.execute(pagina_stmt)
    registros = res.scalars().all()
    meta = {"total": total, "limit": limit, "skip": skip, "count": len(registros)}
    return envelope_resposta(True, [
        Usuario.model_validate(r) for r in registros
    ], meta=meta)


async def atualizar_status_usuario(
    usuario_id: int,
    ativo: bool,
    db: AsyncSession,
    current_user: UsuarioSistema,
) -> UsuarioSistema:
    require_admin(current_user)
    stmt = (
        update(UsuarioSistema)
        .where(UsuarioSistema.id == usuario_id)
        .values(ativo=ativo)
        .returning(UsuarioSistema)
    )
    res = await db.execute(stmt)
    row = res.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    await db.commit()
    return row[0]


@router.patch("/{usuario_id}/ativar")
async def ativar_usuario(
    usuario_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioSistema = Depends(get_current_user),
):
    u = await atualizar_status_usuario(usuario_id, True, db, current_user)
    return envelope_resposta(True, Usuario.model_validate(u).model_dump())


@router.patch("/{usuario_id}/senha")
async def alterar_senha_usuario(
    usuario_id: int = Path(..., gt=0),
    payload: dict = Body(..., example={"senha_atual": "antiga", "nova_senha": "NovaSenha123"}),
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioSistema = Depends(get_current_user),
):
    """Altera a senha de um usuário.

    Regras:
    - O próprio usuário pode alterar sua senha informando senha_atual.
    - Admin pode alterar a senha de qualquer usuário sem senha_atual.
    - Aplica política de senha.
    """
    alvo = await db.get(UsuarioSistema, usuario_id)
    if not alvo:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    is_admin = current_user.perfil == PerfilUsuario.admin
    is_self = current_user.id == usuario_id
    if not (is_admin or is_self):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")

    nova = payload.get("nova_senha")
    if not nova:
        raise HTTPException(status_code=400, detail="Campo 'nova_senha' é obrigatório")
    try:
        validate_password_policy(nova)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    # Se for o próprio usuário, exigir senha atual correta
    if is_self and not is_admin:
        atual = payload.get("senha_atual")
        if not atual:
            raise HTTPException(status_code=400, detail="Campo 'senha_atual' é obrigatório para alteração própria")
        from ..core.security import verify_password

        if not verify_password(atual, alvo.senha_hash):
            raise HTTPException(status_code=400, detail="Senha atual incorreta")

    from ..core.security import hash_password

    alvo.senha_hash = hash_password(nova)
    await db.commit()
    await db.refresh(alvo)
    return envelope_resposta(True, Usuario.model_validate(alvo).model_dump())


@router.patch("/{usuario_id}/desativar")
async def desativar_usuario(
    usuario_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioSistema = Depends(get_current_user),
):
    u = await atualizar_status_usuario(usuario_id, False, db, current_user)
    return envelope_resposta(True, Usuario.model_validate(u).model_dump())
