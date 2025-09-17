from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Paciente, UsuarioSistema
from ..views.paciente_view import PacienteCreate


async def get_patient_by_cpf(db: AsyncSession, cpf: str) -> Paciente | None:
    stmt = select(Paciente).where(Paciente.cpf == cpf)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def check_cpf_exists_in_system(db: AsyncSession, cpf: str) -> bool:
    patient_stmt = select(Paciente.id).where(Paciente.cpf == cpf)
    patient_result = await db.execute(patient_stmt)
    
    if patient_result.scalar_one_or_none():
        return True
    
    return False


async def create_patient(db: AsyncSession, patient_data: PacienteCreate) -> Paciente:
    cpf_exists = await check_cpf_exists_in_system(db, patient_data.cpf)
    if cpf_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CPF já cadastrado no sistema."
        )
    
    new_patient = Paciente(
        nome=patient_data.nome,
        cpf=patient_data.cpf,
        dataNascimento=patient_data.dataNascimento,
        statusAtendimento="Aguardando Triagem"
    )
    
    db.add(new_patient)
    await db.commit()
    await db.refresh(new_patient)
    
    return new_patient


async def list_patients_in_triage(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[Paciente]:
    stmt = (
        select(Paciente)
        .where(Paciente.statusAtendimento == "Aguardando Triagem")
        .order_by(Paciente.created_at)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())