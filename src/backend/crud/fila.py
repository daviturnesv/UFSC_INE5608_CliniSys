from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import FilaAtendimento, StatusFila, TipoAtendimento, Paciente


async def enqueue(db: AsyncSession, *, paciente_id: int, tipo: TipoAtendimento, observacao: str | None = None) -> FilaAtendimento:
    # garante que paciente existe
    if not await db.get(Paciente, paciente_id):
        raise ValueError("Paciente não encontrado")
    item = FilaAtendimento(paciente_id=paciente_id, tipo=tipo, status=StatusFila.aguardando, observacao=observacao)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def list_fila(db: AsyncSession, *, tipo: TipoAtendimento | None = None, status: StatusFila | None = None) -> list[FilaAtendimento]:
    stmt = select(FilaAtendimento).order_by(FilaAtendimento.id)
    if tipo is not None:
        stmt = stmt.where(FilaAtendimento.tipo == tipo)
    if status is not None:
        stmt = stmt.where(FilaAtendimento.status == status)
    res = await db.execute(stmt)
    return list(res.scalars().unique().all())
