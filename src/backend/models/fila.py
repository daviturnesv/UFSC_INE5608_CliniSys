from __future__ import annotations

import enum
from datetime import datetime, timezone
from sqlalchemy import Integer, Enum, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .paciente import Paciente


class TipoAtendimento(enum.Enum):
    triagem = "triagem"
    consulta = "consulta"


class StatusFila(enum.Enum):
    aguardando = "aguardando"
    em_atendimento = "em_atendimento"
    concluido = "concluido"
    cancelado = "cancelado"


class FilaAtendimento(Base):
    __tablename__ = "fila_atendimento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo: Mapped[TipoAtendimento] = mapped_column(Enum(TipoAtendimento, name="tipo_atendimento"), nullable=False, index=True)
    status: Mapped[StatusFila] = mapped_column(Enum(StatusFila, name="status_fila"), nullable=False, index=True, default=StatusFila.aguardando)
    observacao: Mapped[str | None] = mapped_column(String(255), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    paciente: Mapped[Paciente] = relationship()

    def touch(self) -> None:
        self.atualizado_em = datetime.now(timezone.utc)
