from __future__ import annotations

from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from ..db.database import Base


class Clinica(Base):
    __tablename__ = "clinicas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
