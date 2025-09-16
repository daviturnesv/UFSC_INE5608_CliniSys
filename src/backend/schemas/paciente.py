from __future__ import annotations

from datetime import date, datetime
from pydantic import BaseModel, field_validator
import re


class PacienteBase(BaseModel):
    nome_completo: str
    cpf: str
    data_nascimento: date
    telefone: str | None = None

    @field_validator("cpf")
    @classmethod
    def validar_cpf_formatado(cls, v: str) -> str:
        """Valida formato CPF ###.###.###-## (não faz validação de dígito verificador)."""
        padrao = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
        if not padrao.match(v):
            raise ValueError("CPF deve estar no formato 000.000.000-00")
        return v

    @field_validator("data_nascimento")
    @classmethod
    def validar_data_nascimento(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Data de nascimento não pode ser no futuro")
        return v


class PacienteCreate(PacienteBase):
    pass


class Paciente(PacienteBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {
        "from_attributes": True,
    }
