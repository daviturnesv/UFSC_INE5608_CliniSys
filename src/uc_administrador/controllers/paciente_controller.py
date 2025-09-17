from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..views.paciente_view import PacienteCreate, Paciente
from ..views.envelope import envelope
from ..services.paciente_service import create_patient, list_patients_in_triage
from ..controllers.auth_controller import get_current_user
from ..models import UsuarioSistema, PerfilUsuario

router = APIRouter(prefix="/pacientes", tags=["pacientes"])


def require_recepcionista_or_admin(user: UsuarioSistema) -> None:
    if user.perfil not in [PerfilUsuario.recepcionista, PerfilUsuario.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Apenas recepcionistas e administradores podem gerenciar pacientes"
        )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=dict)
async def criar_paciente(
    payload: PacienteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioSistema = Depends(get_current_user),
):
    require_recepcionista_or_admin(current_user)
    
    try:
        paciente = await create_patient(db, payload)
        return envelope(True, Paciente.model_validate(paciente).model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        ) from e


@router.get("/fila-triagem", response_model=dict)
async def listar_fila_triagem(
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioSistema = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(50, ge=1, le=100, description="Número máximo de registros a retornar"),
):
    require_recepcionista_or_admin(current_user)
    
    pacientes = await list_patients_in_triage(db, skip=skip, limit=limit)
    pacientes_data = [Paciente.model_validate(p).model_dump() for p in pacientes]
    
    return envelope(True, {
        "pacientes": pacientes_data,
        "total": len(pacientes_data),
        "skip": skip,
        "limit": limit
    })