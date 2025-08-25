from __future__ import annotations

import enum
from datetime import datetime
from sqlalchemy import String, Boolean, Enum, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class PerfilUsuario(enum.Enum):
    admin = "admin"
    professor = "professor"
    aluno = "aluno"
    recepcionista = "recepcionista"


class UsuarioSistema(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    perfil: Mapped[PerfilUsuario] = mapped_column(Enum(PerfilUsuario, name="perfil_usuario"), nullable=False, index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
