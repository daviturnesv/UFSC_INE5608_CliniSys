from __future__ import annotations

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..crud.usuario import authenticate_user, get_user_by_email, create_user
from ..core.security import create_access_token, decode_token
from ..core.config import get_settings
from ..schemas import Usuario
from ..core.resposta import envelope_resposta
from ..models import PerfilUsuario
from ..models import UsuarioSistema

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


FAILED_ATTEMPTS: dict[str, list[float]] = {}
MAX_ATTEMPTS = 5
WINDOW_SECONDS = 60


@router.post("/token")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    import time

    username = form_data.username.lower()
    agora = time.time()
    tentativas = FAILED_ATTEMPTS.get(username, [])
    tentativas = [t for t in tentativas if agora - t < WINDOW_SECONDS]
    if len(tentativas) >= MAX_ATTEMPTS:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Muitas tentativas. Tente novamente mais tarde.")

    user = await authenticate_user(db, username, form_data.password)
    if not user:
        tentativas.append(agora)
        FAILED_ATTEMPTS[username] = tentativas
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
    # reset em sucesso
    FAILED_ATTEMPTS.pop(username, None)
    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    token = create_access_token({"sub": str(user.id), "perfil": user.perfil.value}, access_token_expires)
    return envelope_resposta(True, {"access_token": token, "token_type": "bearer"})


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


@router.get("/me")
async def read_current_user(current_user: UsuarioSistema = Depends(get_current_user)):
    return envelope_resposta(True, Usuario.model_validate(current_user).model_dump())


async def seed_admin_user(db: AsyncSession, *, email: str, senha: str) -> bool:
    """Cria usuário admin padrão se não existir. Retorna True se criado."""
    existing = await get_user_by_email(db, email)
    if existing:
        return False
    await create_user(db, nome="Administrador", email=email, senha=senha, perfil=PerfilUsuario.admin)
    return True
