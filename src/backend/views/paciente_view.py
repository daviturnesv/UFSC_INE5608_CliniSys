from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date
import re

# Constantes para evitar duplicação
DIGITS_ONLY_PATTERN = r'\D'


class PacienteBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=120, description="Nome completo do paciente")
    cpf: str = Field(..., description="CPF do paciente")
    dataNascimento: date = Field(..., description="Data de nascimento do paciente")
    telefone: str | None = Field(None, max_length=20, description="Telefone do paciente")

    @field_validator('cpf')
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        cpf = re.sub(DIGITS_ONLY_PATTERN, '', v)
        
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

    @field_validator('telefone')
    @classmethod
    def validate_telefone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        
        # Remove caracteres especiais
        telefone = re.sub(DIGITS_ONLY_PATTERN, '', v)
        
        if len(telefone) < 10 or len(telefone) > 11:
            raise ValueError('Telefone deve ter 10 ou 11 dígitos')
        
        return telefone

    @field_validator('dataNascimento')
    @classmethod
    def validate_data_nascimento(cls, v: date) -> date:
        if v > date.today():
            raise ValueError('Data de nascimento não pode ser no futuro')
        
        # Validação de idade mínima (não pode ser muito antiga)
        if date.today().year - v.year > 150:
            raise ValueError('Data de nascimento muito antiga')
        
        return v

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


class PacienteUpdate(BaseModel):
    nome: str | None = Field(None, min_length=2, max_length=120)
    telefone: str | None = Field(None, max_length=20)
    statusAtendimento: str | None = Field(None, max_length=50)

    @field_validator('telefone')
    @classmethod
    def validate_telefone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        
        # Remove caracteres especiais
        telefone = re.sub(DIGITS_ONLY_PATTERN, '', v)
        
        if len(telefone) < 10 or len(telefone) > 11:
            raise ValueError('Telefone deve ter 10 ou 11 dígitos')
        
        return telefone

    @field_validator('nome')
    @classmethod
    def validate_nome(cls, v: str | None) -> str | None:
        if v is None:
            return v
        
        nome = v.strip()
        if not nome:
            raise ValueError('Nome não pode ser vazio')
        if not re.match(r'^[a-zA-ZÀ-ÿ\s]+$', nome):
            raise ValueError('Nome deve conter apenas letras e espaços')
        return nome.title()


class Paciente(PacienteBase):
    id: int
    statusAtendimento: str = Field(default="Aguardando Triagem", description="Status atual do paciente na fila")
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {
        "from_attributes": True,
    }


class PacienteListResponse(BaseModel):
    items: list[Paciente]
    total: int = 0