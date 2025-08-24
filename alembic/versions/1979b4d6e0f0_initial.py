"""initial

Revision ID: 1979b4d6e0f0
Revises: 
Create Date: 2025-08-24 00:00:00
"""
from __future__ import annotations

from alembic import op  # type: ignore
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1979b4d6e0f0"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usuariosistema",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "perfil",
            sa.Enum("ADMIN", "ATENDENTE", "MEDICO", name="perfilusuario"),
            nullable=False,
        ),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_usuariosistema_email", "usuariosistema", ["email"], unique=True)

    op.create_table(
        "paciente",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome_completo", sa.String(length=255), nullable=False),
        sa.Column("cpf", sa.String(length=14), nullable=False),
        sa.Column("data_nascimento", sa.Date(), nullable=True),
        sa.Column("telefone", sa.String(length=20), nullable=True),
        sa.UniqueConstraint("cpf", name="uq_paciente_cpf"),
    )
    op.create_index("ix_paciente_cpf", "paciente", ["cpf"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_paciente_cpf", table_name="paciente")
    op.drop_table("paciente")
    op.drop_index("ix_usuariosistema_email", table_name="usuariosistema")
    op.drop_table("usuariosistema")
