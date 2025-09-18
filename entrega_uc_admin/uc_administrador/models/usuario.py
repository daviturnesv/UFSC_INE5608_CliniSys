from __future__ import annotations

import enum
from datetime import datetime
from sqlalchemy import String, Boolean, Enum, Integer, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ..db.database import Base

USUARIOS_FK = "usuarios.id"


class PerfilUsuario(enum.Enum):
    admin = "admin"
    professor = "professor"
    aluno = "aluno"
    recepcionista = "recepcionista"


class UsuarioSistema(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cpf: Mapped[str | None] = mapped_column(String(14), unique=True, index=True, nullable=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    perfil: Mapped[PerfilUsuario] = mapped_column(Enum(PerfilUsuario, name="perfil_usuario"), nullable=False, index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


# Perfis 1:1 por papel (campos específicos), com PK = user_id

class PerfilProfessor(Base):
    __tablename__ = "perfil_professor"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(USUARIOS_FK, ondelete="CASCADE"), primary_key=True)
    especialidade: Mapped[str | None] = mapped_column(String(120), nullable=True)
    clinica_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("clinicas.id", ondelete="SET NULL"),
        nullable=True,
    )


class PerfilRecepcionista(Base):
    __tablename__ = "perfil_recepcionista"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(USUARIOS_FK, ondelete="CASCADE"), primary_key=True)
    telefone: Mapped[str | None] = mapped_column(String(30), nullable=True)


class PerfilAluno(Base):
    __tablename__ = "perfil_aluno"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(USUARIOS_FK, ondelete="CASCADE"), primary_key=True)
    matricula: Mapped[str | None] = mapped_column(String(50), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    clinica_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("clinicas.id", ondelete="SET NULL"),
        nullable=True,
    )
