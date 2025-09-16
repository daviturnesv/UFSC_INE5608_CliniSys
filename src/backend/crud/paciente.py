from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Paciente


async def get_paciente(db: AsyncSession, paciente_id: int) -> Paciente | None:
    return await db.get(Paciente, paciente_id)


async def get_paciente_by_cpf(db: AsyncSession, cpf: str) -> Paciente | None:
    stmt = select(Paciente).where(Paciente.cpf == cpf)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def list_pacientes(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[Paciente]:
    stmt = select(Paciente).offset(skip).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def search_pacientes(
    db: AsyncSession,
    *,
    nome: str | None = None,
    cpf: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[Paciente], int]:
    """Pesquisa pacientes por nome (ilike) e/ou CPF exato, com total.

    Retorna (registros, total_filtrado)
    """
    base = select(Paciente)
    count = select(func.count()).select_from(Paciente)
    filtros = []
    if nome:
        filtros.append(Paciente.nome_completo.ilike(f"%{nome}%"))
    if cpf:
        filtros.append(Paciente.cpf == cpf)
    for f in filtros:
        base = base.where(f)
        count = count.where(f)
    base = base.order_by(Paciente.id).offset(skip).limit(limit)
    res = await db.execute(base)
    regs = list(res.scalars().all())
    total = (await db.execute(count)).scalar_one()
    return regs, int(total)


async def create_paciente(db: AsyncSession, **data) -> Paciente:
    paciente = Paciente(**data)
    db.add(paciente)
    await db.commit()
    await db.refresh(paciente)
    return paciente


async def update_paciente(db: AsyncSession, paciente: Paciente, **data) -> Paciente:
    for k, v in data.items():
        setattr(paciente, k, v)
    await db.commit()
    await db.refresh(paciente)
    return paciente


async def delete_paciente(db: AsyncSession, paciente: Paciente) -> None:
    await db.delete(paciente)
    await db.commit()
