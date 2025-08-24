from __future__ import annotations

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..crud.usuario import authenticate_user
from ..core.security import create_access_token, decode_token
from ..core.config import get_settings
from ..schemas import Usuario
from ..models import UsuarioSistema

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    token = create_access_token({"sub": str(user.id), "perfil": user.perfil.value}, access_token_expires)
    return {"access_token": token, "token_type": "bearer"}


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> UsuarioSistema:
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user = await db.get(UsuarioSistema, int(user_id))
    if not user or not user.ativo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inativo ou não encontrado")
    return user
