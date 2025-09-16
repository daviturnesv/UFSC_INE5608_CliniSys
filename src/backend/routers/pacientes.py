from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas import PacienteCreate, Paciente
from ..crud.paciente import (
    create_paciente,
    get_paciente,
    list_pacientes,
    get_paciente_by_cpf,
    update_paciente,
    delete_paciente,
    search_pacientes,
)
from .auth import get_current_user
from ..models import UsuarioSistema, PerfilUsuario
from ..core.resposta import envelope_resposta

router = APIRouter(prefix="/pacientes", tags=["pacientes"])

MSG_PACIENTE_NAO_ENCONTRADO = "Paciente não encontrado"


@router.get("/busca")
async def buscar_pacientes(
    nome: str | None = Query(default=None, description="Filtro parcial por nome"),
    cpf: str | None = Query(default=None, description="Filtro exato por CPF"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioSistema = Depends(get_current_user),
):
    # Qualquer autenticado pode buscar
    registros, total = await search_pacientes(db, nome=nome, cpf=cpf, skip=skip, limit=limit)
    meta = {"total": total, "skip": skip, "limit": limit, "count": len(registros)}
    return envelope_resposta(True, [Paciente.model_validate(p).model_dump() for p in registros], meta=meta)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def criar_paciente(
    payload: PacienteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioSistema = Depends(get_current_user),
):
    # Apenas recepcionista ou admin podem criar
    if current_user.perfil not in (PerfilUsuario.recepcionista, PerfilUsuario.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    existente = await get_paciente_by_cpf(db, payload.cpf)
    if existente:
        raise HTTPException(status_code=400, detail="CPF já cadastrado")
    paciente = await create_paciente(db, **payload.model_dump())
    return envelope_resposta(True, Paciente.model_validate(paciente).model_dump())


@router.get("/")
async def listar_pacientes(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db), current_user: UsuarioSistema = Depends(get_current_user)):
    # Qualquer autenticado pode listar
    registros = await list_pacientes(db, skip=skip, limit=limit)
    return envelope_resposta(True, [Paciente.model_validate(p).model_dump() for p in registros], meta={"count": len(registros), "skip": skip, "limit": limit})


@router.get("/{paciente_id}")
async def obter_paciente(paciente_id: int, db: AsyncSession = Depends(get_db), current_user: UsuarioSistema = Depends(get_current_user)):
    # Qualquer autenticado pode obter
    paciente = await get_paciente(db, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail=MSG_PACIENTE_NAO_ENCONTRADO)
    return envelope_resposta(True, Paciente.model_validate(paciente).model_dump())


@router.put("/{paciente_id}")
async def atualizar_paciente(
    paciente_id: int,
    payload: PacienteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioSistema = Depends(get_current_user),
):
    # Apenas recepcionista ou admin podem atualizar
    if current_user.perfil not in (PerfilUsuario.recepcionista, PerfilUsuario.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    paciente = await get_paciente(db, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail=MSG_PACIENTE_NAO_ENCONTRADO)
    paciente = await update_paciente(db, paciente, **payload.model_dump())
    return envelope_resposta(True, Paciente.model_validate(paciente).model_dump())


@router.delete("/{paciente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_paciente(paciente_id: int, db: AsyncSession = Depends(get_db), current_user: UsuarioSistema = Depends(get_current_user)):
    # Apenas recepcionista ou admin podem remover
    if current_user.perfil not in (PerfilUsuario.recepcionista, PerfilUsuario.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    paciente = await get_paciente(db, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail=MSG_PACIENTE_NAO_ENCONTRADO)
    await delete_paciente(db, paciente)
    return envelope_resposta(True, None)
