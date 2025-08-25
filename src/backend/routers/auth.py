from __future__ import annotations

from datetime import timedelta
import time
from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..crud.usuario import authenticate_user, get_user_by_email, create_user
from ..crud.refresh_token import criar_refresh_token, obter_refresh_token_valido, rotacionar_refresh_token
from ..core.security import create_access_token, decode_token, hash_password, verify_password, pwd_context
from sqlalchemy import select
from ..models.refresh_token import RefreshToken
from ..core.config import get_settings
from ..schemas import Usuario
from ..core.resposta import envelope_resposta
from ..models import PerfilUsuario
from ..models import UsuarioSistema

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


FAILED_ATTEMPTS: dict[str, list[float]] = {}
FAILED_TOTAL: dict[str, int] = {}
MAX_ATTEMPTS = 5  # tentativas dentro da janela curta
WINDOW_SECONDS = 60
# Escalonamento: após limite de ciclos, aumenta a penalidade
ESCALATE_THRESHOLD = 10  # falhas acumuladas
ESCALATED_WINDOW = 300   # 5 minutos

# Blacklist simples de jti revogados (memória)
REVOKED_JTIS: set[str] = set()


@router.post("/token")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    username = form_data.username.lower()
    agora = time.time()
    tentativas = FAILED_ATTEMPTS.get(username, [])
    tentativas = [t for t in tentativas if agora - t < WINDOW_SECONDS]
    escalated = False
    total_falhas = FAILED_TOTAL.get(username, 0)
    # Se passou do threshold, aplicamos janela maior (verificamos tentativas também nessa janela maior)
    if total_falhas >= ESCALATE_THRESHOLD:
        tentativas_escaladas = [t for t in FAILED_ATTEMPTS.get(username, []) if agora - t < ESCALATED_WINDOW]
        if len(tentativas_escaladas) >= MAX_ATTEMPTS:
            escalated = True
    if (len(tentativas) >= MAX_ATTEMPTS) or escalated:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Muitas tentativas. Tente novamente mais tarde.")

    user = await authenticate_user(db, username, form_data.password)
    if not user:
        tentativas.append(agora)
        FAILED_ATTEMPTS[username] = tentativas
        FAILED_TOTAL[username] = FAILED_TOTAL.get(username, 0) + 1
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
    # reset em sucesso
    FAILED_ATTEMPTS.pop(username, None)
    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    token = create_access_token({"sub": str(user.id), "perfil": user.perfil.value}, access_token_expires)
    refresh_raw, _ = await criar_refresh_token(db, user)
    return envelope_resposta(True, {"access_token": token, "token_type": "bearer", "refresh_token": refresh_raw})


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
    jti = payload.get("jti")
    if jti and jti in REVOKED_JTIS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revogado")
    user = await db.get(UsuarioSistema, int(user_id))
    if not user or not user.ativo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inativo ou não encontrado")
    return user


@router.get("/me")
async def read_current_user(current_user: UsuarioSistema = Depends(get_current_user)):
    return envelope_resposta(True, Usuario.model_validate(current_user).model_dump())


@router.post("/logout")
async def logout_atual(token: str = Depends(oauth2_scheme)):
    """Revoga o token atual adicionando seu jti à blacklist.

    Em produção, ideal persistir em armazenamento compartilhado (ex: Redis) com TTL.
    """
    try:
        payload = decode_token(token)
    except ValueError:
        # Se já inválido, tratamos como sucesso idempotente
        return envelope_resposta(True, {"revogado": True})
    jti = payload.get("jti")
    if jti:
        REVOKED_JTIS.add(jti)
    return envelope_resposta(True, {"revogado": True})


@router.post("/refresh")
async def refresh_tokens(
    refresh_token: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    """Recebe refresh_token válido e retorna novo par (access, refresh) com rotação.

    Estratégia: localizar usuário via comparação de hash (carregar tokens ativos do usuário exigiria usuário).
    Simples: exigir também access token expirado opcional? Mantemos somente refresh.
    Para otimização real, poderíamos armazenar identificador derivado (ex: parte truncada do hash) mas aqui MVP.
    """
    # Estratégia: varrer usuários poderia ser caro; assumimos que cliente sempre chama após login e envia access (não obrigatório).
    # Para manter simples, pedimos email opcional? Melhor decodificar se access fornecido no Authorization (mesmo expirado?).
    # MVP: percorrer tokens buscando match (limitação: precisa join). Implementação: consulta todos tokens não revogados recentes.
    # Busca tokens potencialmente válidos (não revogados e não expirados) e tenta comparar hash
    agora_limite = time.time()
    stmt = select(RefreshToken).where(RefreshToken.revogado.is_(False))
    res = await db.execute(stmt)
    candidatos = res.scalars().all()
    alvo_token = None
    for cand in candidatos:
        # filtra expiração
        if cand.expira_em.timestamp() < agora_limite:
            continue
        if verify_password(refresh_token, cand.token_hash):
            alvo_token = cand
            break
    if not alvo_token:
        raise HTTPException(status_code=401, detail="Refresh token inválido ou expirado")
    alvo_usuario = await db.get(UsuarioSistema, alvo_token.usuario_id)
    if not alvo_usuario or not alvo_usuario.ativo:
        raise HTTPException(status_code=401, detail="Usuário inválido para refresh")
    # Rotação (revoga antigo e cria novo)
    novo_refresh_raw, _ = await rotacionar_refresh_token(db, alvo_usuario, alvo_token)
    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    novo_access = create_access_token({"sub": str(alvo_usuario.id), "perfil": alvo_usuario.perfil.value}, access_token_expires)
    return envelope_resposta(True, {"access_token": novo_access, "refresh_token": novo_refresh_raw, "token_type": "bearer"})


async def seed_admin_user(db: AsyncSession, *, email: str, senha: str) -> bool:
    """Cria usuário admin padrão se não existir. Retorna True se criado."""
    existing = await get_user_by_email(db, email)
    if existing:
        return False
    await create_user(db, nome="Administrador", email=email, senha=senha, perfil=PerfilUsuario.admin)
    return True
