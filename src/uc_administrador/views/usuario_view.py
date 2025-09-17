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
    cpf: str | None = None


class UsuarioCreate(UsuarioBase):
    senha: str
    # Dados opcionais específicos por perfil
    dados_perfil: dict | None = None


class UsuarioUpdate(BaseModel):
    nome: str | None = None
    email: EmailStr | None = None
    perfil: PerfilUsuario | None = None
    cpf: str | None = None


class Usuario(BaseModel):
    id: int
    nome: str
    email: EmailStr
    perfil: PerfilUsuario
    cpf: str | None = None
    ativo: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    perfil_dados: dict | None = None

    model_config = {
        "from_attributes": True,
    }
