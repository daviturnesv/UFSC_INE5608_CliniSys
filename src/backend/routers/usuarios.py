from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas import UsuarioCreate, Usuario
from ..models import UsuarioSistema, PerfilUsuario  # usar enum do modelo para tipagem
from ..crud.usuario import create_user, get_user_by_email
from .auth import get_current_user

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


def require_admin(user: UsuarioSistema) -> None:
    if user.perfil != PerfilUsuario.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")


@router.post("/", response_model=Usuario, status_code=status.HTTP_201_CREATED)
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
    user = await create_user(db, nome=payload.nome, email=payload.email, senha=payload.senha, perfil=perfil)
    return user
