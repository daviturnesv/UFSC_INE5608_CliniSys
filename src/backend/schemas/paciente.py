from __future__ import annotations

from datetime import date
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

    class Config:
        from_attributes = True
