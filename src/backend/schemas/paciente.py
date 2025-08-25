from __future__ import annotations

from datetime import date, datetime
from pydantic import BaseModel


class PacienteBase(BaseModel):
    nome_completo: str
    cpf: str
    data_nascimento: date
    telefone: str | None = None


class PacienteCreate(PacienteBase):
    pass


class Paciente(PacienteBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {
        "from_attributes": True,
    }
