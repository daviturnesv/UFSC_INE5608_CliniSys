from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
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
)
from .auth import get_current_user
from ..models import UsuarioSistema
from ..core.resposta import envelope_resposta

router = APIRouter(prefix="/pacientes", tags=["pacientes"])

MSG_PACIENTE_NAO_ENCONTRADO = "Paciente não encontrado"


@router.post("/", status_code=status.HTTP_201_CREATED)
async def criar_paciente(
    payload: PacienteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioSistema = Depends(get_current_user),
):
    existente = await get_paciente_by_cpf(db, payload.cpf)
    if existente:
        raise HTTPException(status_code=400, detail="CPF já cadastrado")
    paciente = await create_paciente(db, **payload.model_dump())
    return envelope_resposta(True, Paciente.model_validate(paciente).model_dump())


@router.get("/{paciente_id}")
async def obter_paciente(paciente_id: int, db: AsyncSession = Depends(get_db), current_user: UsuarioSistema = Depends(get_current_user)):
    paciente = await get_paciente(db, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail=MSG_PACIENTE_NAO_ENCONTRADO)
    return envelope_resposta(True, Paciente.model_validate(paciente).model_dump())


@router.get("/")
async def listar_pacientes(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db), current_user: UsuarioSistema = Depends(get_current_user)):
    registros = await list_pacientes(db, skip=skip, limit=limit)
    return envelope_resposta(True, [Paciente.model_validate(p).model_dump() for p in registros], meta={"count": len(registros), "skip": skip, "limit": limit})


@router.put("/{paciente_id}")
async def atualizar_paciente(
    paciente_id: int,
    payload: PacienteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioSistema = Depends(get_current_user),
):
    paciente = await get_paciente(db, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail=MSG_PACIENTE_NAO_ENCONTRADO)
    paciente = await update_paciente(db, paciente, **payload.model_dump())
    return envelope_resposta(True, Paciente.model_validate(paciente).model_dump())


@router.delete("/{paciente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_paciente(paciente_id: int, db: AsyncSession = Depends(get_db), current_user: UsuarioSistema = Depends(get_current_user)):
    paciente = await get_paciente(db, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail=MSG_PACIENTE_NAO_ENCONTRADO)
    await delete_paciente(db, paciente)
    return envelope_resposta(True, None)
