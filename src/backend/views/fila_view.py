from __future__ import annotations

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from ..models.fila import TipoAtendimento, StatusFila


class FilaCreate(BaseModel):
    paciente_id: int
    tipo: TipoAtendimento
    observacao: Optional[str] = None


class FilaUpdate(BaseModel):
    status: Optional[StatusFila] = None
    observacao: Optional[str] = None


class PacienteResumido(BaseModel):
    id: int
    nome: str
    cpf: str


class FilaResponse(BaseModel):
    id: int
    paciente: Optional[PacienteResumido] = None
    tipo: TipoAtendimento
    status: StatusFila
    observacao: Optional[str] = None
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True


class FilaListResponse(BaseModel):
    items: list[FilaResponse]
    total: int = 0


class FilaStatusUpdate(BaseModel):
    observacao: Optional[str] = None