from __future__ import annotations

from datetime import date
from sqlalchemy import String, Integer, Date, UniqueConstraint, DateTime, func
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Paciente(Base):
    __tablename__ = "pacientes"
    __table_args__ = (
        UniqueConstraint("cpf", name="uq_paciente_cpf"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome_completo: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    cpf: Mapped[str] = mapped_column(String(14), nullable=False, unique=True)
    data_nascimento: Mapped[date] = mapped_column(Date, nullable=False)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
