from __future__ import annotations

from datetime import datetime, date
from sqlalchemy import String, Integer, DateTime, Date, func
from sqlalchemy.orm import Mapped, mapped_column

from ..db.database import Base


class Paciente(Base):
    __tablename__ = "pacientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    cpf: Mapped[str] = mapped_column(String(14), unique=True, nullable=False, index=True)  # Aumentado para 14 chars (com pontos e hífen)
    dataNascimento: Mapped[date] = mapped_column(Date, nullable=False)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)  # Adicionado campo telefone
    statusAtendimento: Mapped[str] = mapped_column(String(50), nullable=False, default="Aguardando Triagem", server_default="Aguardando Triagem")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)