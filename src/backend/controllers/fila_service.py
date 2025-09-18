from __future__ import annotations

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime

from ..models.fila import FilaAtendimento, TipoAtendimento, StatusFila
from ..models.paciente import Paciente


async def add_to_queue(
    session: AsyncSession,
    paciente_id: int,
    tipo: TipoAtendimento,
    observacao: Optional[str] = None
) -> FilaAtendimento:
    """Adiciona paciente à fila de atendimento"""
    
    # Verifica se paciente já está na fila para o mesmo tipo
    existing = await session.execute(
        select(FilaAtendimento).where(
            and_(
                FilaAtendimento.paciente_id == paciente_id,
                FilaAtendimento.tipo == tipo,
                FilaAtendimento.status.in_([StatusFila.aguardando, StatusFila.em_atendimento])
            )
        )
    )
    
    if existing.scalars().first():
        raise ValueError(f"Paciente já está na fila de {tipo.value}")
    
    fila_item = FilaAtendimento(
        paciente_id=paciente_id,
        tipo=tipo,
        status=StatusFila.aguardando,
        observacao=observacao
    )
    
    session.add(fila_item)
    await session.commit()
    await session.refresh(fila_item)
    
    return fila_item


async def get_queue_by_type(
    session: AsyncSession,
    tipo: TipoAtendimento,
    status: Optional[StatusFila] = None
) -> List[FilaAtendimento]:
    """Busca fila por tipo de atendimento"""
    
    conditions = [FilaAtendimento.tipo == tipo]
    
    if status:
        conditions.append(FilaAtendimento.status == status)
    else:
        # Por padrão, não mostra itens cancelados ou concluídos
        conditions.append(
            FilaAtendimento.status.in_([StatusFila.aguardando, StatusFila.em_atendimento])
        )
    
    stmt = (
        select(FilaAtendimento)
        .where(and_(*conditions))
        .options(selectinload(FilaAtendimento.paciente))
        .order_by(FilaAtendimento.criado_em)
    )
    
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_waiting_queue(session: AsyncSession) -> List[FilaAtendimento]:
    """Busca todos os pacientes aguardando (triagem ou consulta)"""
    
    stmt = (
        select(FilaAtendimento)
        .where(FilaAtendimento.status == StatusFila.aguardando)
        .options(selectinload(FilaAtendimento.paciente))
        .order_by(FilaAtendimento.tipo, FilaAtendimento.criado_em)
    )
    
    result = await session.execute(stmt)
    return result.scalars().all()


async def update_queue_status(
    session: AsyncSession,
    fila_id: int,
    new_status: StatusFila,
    observacao: Optional[str] = None
) -> Optional[FilaAtendimento]:
    """Atualiza status de um item na fila"""
    
    fila_item = await session.get(FilaAtendimento, fila_id)
    
    if not fila_item:
        return None
    
    fila_item.status = new_status
    fila_item.touch()  # Atualiza timestamp
    
    if observacao:
        fila_item.observacao = observacao
    
    await session.commit()
    await session.refresh(fila_item)
    
    return fila_item


async def start_attendance(
    session: AsyncSession,
    fila_id: int
) -> Optional[FilaAtendimento]:
    """Marca paciente como em atendimento"""
    
    return await update_queue_status(
        session, 
        fila_id, 
        StatusFila.em_atendimento
    )


async def finish_attendance(
    session: AsyncSession,
    fila_id: int,
    observacao: Optional[str] = None
) -> Optional[FilaAtendimento]:
    """Marca atendimento como concluído"""
    
    return await update_queue_status(
        session, 
        fila_id, 
        StatusFila.concluido,
        observacao
    )


async def cancel_attendance(
    session: AsyncSession,
    fila_id: int,
    observacao: Optional[str] = None
) -> Optional[FilaAtendimento]:
    """Cancela atendimento (ex: desistência)"""
    
    return await update_queue_status(
        session, 
        fila_id, 
        StatusFila.cancelado,
        observacao
    )


async def get_patient_queue_history(
    session: AsyncSession,
    paciente_id: int
) -> List[FilaAtendimento]:
    """Busca histórico de filas de um paciente"""
    
    stmt = (
        select(FilaAtendimento)
        .where(FilaAtendimento.paciente_id == paciente_id)
        .options(selectinload(FilaAtendimento.paciente))
        .order_by(FilaAtendimento.criado_em.desc())
    )
    
    result = await session.execute(stmt)
    return result.scalars().all()


async def remove_from_queue(
    session: AsyncSession,
    fila_id: int
) -> bool:
    """Remove item da fila (exclusão física)"""
    
    fila_item = await session.get(FilaAtendimento, fila_id)
    
    if not fila_item:
        return False
    
    await session.delete(fila_item)
    await session.commit()
    
    return True
