from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.fila import FilaCreate, FilaItem
from ..crud.fila import enqueue, list_fila
from ..models import UsuarioSistema, PerfilUsuario, TipoAtendimento, StatusFila
from .auth import get_current_user
from ..core.resposta import envelope_resposta

router = APIRouter(prefix="/fila", tags=["fila"])


def require_recepcionista_ou_admin(user: UsuarioSistema) -> None:
    if user.perfil not in (PerfilUsuario.recepcionista, PerfilUsuario.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")


@router.post("/", status_code=status.HTTP_201_CREATED)
async def adicionar_na_fila(
    payload: FilaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioSistema = Depends(get_current_user),
):
    require_recepcionista_ou_admin(current_user)
    try:
        item = await enqueue(db, paciente_id=payload.paciente_id, tipo=payload.tipo, observacao=payload.observacao)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return envelope_resposta(True, FilaItem.model_validate(item).model_dump())


@router.get("/")
async def consultar_fila(
    tipo: TipoAtendimento | None = Query(default=None),
    status_fila: StatusFila | None = Query(default=StatusFila.aguardando, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioSistema = Depends(get_current_user),
):
    # qualquer autenticado pode visualizar a fila
    itens = await list_fila(db, tipo=tipo, status=status_fila)
    return envelope_resposta(True, [FilaItem.model_validate(i).model_dump() for i in itens], meta={"count": len(itens)})
