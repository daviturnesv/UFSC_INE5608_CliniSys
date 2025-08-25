from __future__ import annotations

from pydantic import BaseModel, EmailStr
from datetime import datetime
from enum import Enum


class PerfilUsuario(str, Enum):
    admin = "admin"
    professor = "professor"
    aluno = "aluno"
    recepcionista = "recepcionista"


class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr
    perfil: PerfilUsuario


class UsuarioCreate(UsuarioBase):
    senha: str


class Usuario(UsuarioBase):
    id: int
    ativo: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {
        "from_attributes": True,
    }
