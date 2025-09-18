from __future__ import annotations

from typing import Optional, List
from sqlalchemy import select, or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime, timezone

from ..models import Paciente, UsuarioSistema
from ..views.paciente_view import PacienteCreate, PacienteUpdate

# Constante para evitar duplicação
STATUS_AGUARDANDO_TRIAGEM = "Aguardando Triagem"


async def get_patient_by_cpf(db: AsyncSession, cpf: str) -> Paciente | None:
    """Busca paciente por CPF"""
    stmt = select(Paciente).where(Paciente.cpf == cpf)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def get_patient_by_id(db: AsyncSession, patient_id: int) -> Paciente | None:
    """Busca paciente por ID"""
    return await db.get(Paciente, patient_id)


async def search_patients(
    db: AsyncSession, 
    search_term: str, 
    skip: int = 0, 
    limit: int = 50
) -> List[Paciente]:
    """Busca pacientes por nome ou CPF"""
    
    # Remove caracteres especiais do CPF para busca
    clean_search = ''.join(filter(str.isalnum, search_term))
    
    stmt = (
        select(Paciente)
        .where(
            or_(
                func.lower(Paciente.nome).contains(search_term.lower()),
                Paciente.cpf.contains(clean_search)
            )
        )
        .order_by(Paciente.nome)
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def check_cpf_exists_in_system(db: AsyncSession, cpf: str) -> bool:
    """Verifica se CPF já existe no sistema"""
    patient_stmt = select(Paciente.id).where(Paciente.cpf == cpf)
    patient_result = await db.execute(patient_stmt)
    
    if patient_result.scalar_one_or_none():
        return True
    
    return False


async def create_patient(db: AsyncSession, patient_data: PacienteCreate) -> Paciente:
    """Cria um novo paciente"""
    cpf_exists = await check_cpf_exists_in_system(db, patient_data.cpf)
    if cpf_exists:
        raise ValueError("CPF já cadastrado no sistema.")
    
    new_patient = Paciente(
        nome=patient_data.nome,
        cpf=patient_data.cpf,
        dataNascimento=patient_data.dataNascimento,
        telefone=getattr(patient_data, 'telefone', None),  # Suporte a telefone opcional
        statusAtendimento=STATUS_AGUARDANDO_TRIAGEM
    )
    
    db.add(new_patient)
    await db.commit()
    await db.refresh(new_patient)
    
    return new_patient


async def list_patients_in_triage(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[Paciente]:
    """Lista pacientes aguardando triagem"""
    stmt = (
        select(Paciente)
        .where(Paciente.statusAtendimento == STATUS_AGUARDANDO_TRIAGEM)
        .order_by(Paciente.created_at)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def list_all_patients(db: AsyncSession, skip: int = 0, limit: int = 50) -> List[Paciente]:
    """Lista todos os pacientes"""
    stmt = (
        select(Paciente)
        .order_by(Paciente.nome)
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def count_patients(db: AsyncSession) -> int:
    """Conta total de pacientes"""
    stmt = select(func.count(Paciente.id))
    result = await db.execute(stmt)
    return result.scalar() or 0


async def update_patient(db: AsyncSession, patient_id: int, patient_data: PacienteUpdate) -> Paciente | None:
    """Atualiza dados de um paciente"""
    patient = await get_patient_by_id(db, patient_id)
    if not patient:
        return None
    
    # Atualiza apenas os campos fornecidos
    for field, value in patient_data.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)
    
    # Atualiza timestamp de modificação
    patient.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(patient)
    
    return patient


async def delete_patient(db: AsyncSession, patient_id: int) -> bool:
    """Remove um paciente do sistema"""
    patient = await get_patient_by_id(db, patient_id)
    if not patient:
        return False
    
    await db.delete(patient)
    await db.commit()
    
    return True


async def search_patients_by_name_or_cpf(
    db: AsyncSession, 
    nome: Optional[str] = None,
    cpf: Optional[str] = None,
    skip: int = 0, 
    limit: int = 50
) -> List[Paciente]:
    """Busca pacientes por nome e/ou CPF - versão mais específica"""
    
    conditions = []
    
    if nome:
        conditions.append(func.lower(Paciente.nome).contains(nome.lower()))
    
    if cpf:
        # Remove caracteres especiais do CPF para busca
        clean_cpf = ''.join(filter(str.isdigit, cpf))
        conditions.append(Paciente.cpf.contains(clean_cpf))
    
    if not conditions:
        # Se nenhum filtro foi fornecido, retorna lista vazia
        return []
    
    stmt = (
        select(Paciente)
        .where(and_(*conditions) if len(conditions) > 1 else conditions[0])
        .order_by(Paciente.nome)
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    return list(result.scalars().all())
