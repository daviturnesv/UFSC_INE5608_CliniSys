from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field
from .paciente import Paciente
from ..models import TipoAtendimento, StatusFila


class FilaCreate(BaseModel):
    paciente_id: int
    tipo: TipoAtendimento
    observacao: str | None = Field(default=None, max_length=255)


class FilaItem(BaseModel):
    id: int
    paciente_id: int
    tipo: TipoAtendimento
    status: StatusFila
    observacao: str | None = None
    criado_em: datetime | None = None
    atualizado_em: datetime | None = None
    paciente: Paciente | None = None

    model_config = {"from_attributes": True}
