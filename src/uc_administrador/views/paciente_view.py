from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date
import re


class PacienteBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=120, description="Nome completo do paciente")
    cpf: str = Field(..., description="CPF do paciente")
    dataNascimento: date = Field(..., description="Data de nascimento do paciente")

    @field_validator('cpf')
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        cpf = re.sub(r'[^0-9]', '', v)
        
        if len(cpf) != 11:
            raise ValueError('CPF deve ter 11 dígitos')
        
        if cpf == cpf[0] * 11:
            raise ValueError('CPF inválido')
        
        def calculate_digit(cpf_partial: str, weights: list[int]) -> int:
            total = sum(int(digit) * weight for digit, weight in zip(cpf_partial, weights))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder
        
        first_digit = calculate_digit(cpf[:9], list(range(10, 1, -1)))
        second_digit = calculate_digit(cpf[:10], list(range(11, 1, -1)))
        
        if cpf[9] != str(first_digit) or cpf[10] != str(second_digit):
            raise ValueError('CPF inválido')
        
        return cpf

    @field_validator('nome')
    @classmethod
    def validate_nome(cls, v: str) -> str:
        nome = v.strip()
        if not nome:
            raise ValueError('Nome não pode ser vazio')
        if not re.match(r'^[a-zA-ZÀ-ÿ\s]+$', nome):
            raise ValueError('Nome deve conter apenas letras e espaços')
        return nome.title()


class PacienteCreate(PacienteBase):
    pass


class Paciente(PacienteBase):
    id: int
    statusAtendimento: str = Field(default="Aguardando Triagem", description="Status atual do paciente na fila")
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {
        "from_attributes": True,
    }