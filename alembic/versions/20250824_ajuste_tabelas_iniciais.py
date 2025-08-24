"""ajuste inicial tabelas e enum

Revision ID: 20250824_ajuste
Revises: 1979b4d6e0f0
Create Date: 2025-08-24
"""
from __future__ import annotations

from alembic import op  # type: ignore
import sqlalchemy as sa

revision = "20250824_ajuste"
down_revision = "1979b4d6e0f0"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Renomear tabela usuariosistema -> usuarios se existir
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "usuariosistema" in insp.get_table_names():
        op.rename_table("usuariosistema", "usuarios")
        # renomear índice se existir
        try:
            op.execute("ALTER INDEX ix_usuariosistema_email RENAME TO ix_usuarios_email")
        except Exception:  # noqa: BLE001
            pass
    # Ajustar enum para valores minúsculos se enum antigo existir
    # Em SQLite nada a fazer; em Postgres precisaríamos recriar enum — aqui mantemos simples.
    # Renomear paciente -> pacientes (plural) se necessário
    if "paciente" in insp.get_table_names() and "pacientes" not in insp.get_table_names():
        op.rename_table("paciente", "pacientes")
        try:
            op.execute("ALTER INDEX ix_paciente_cpf RENAME TO ix_pacientes_cpf")
        except Exception:  # noqa: BLE001
            pass


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "pacientes" in insp.get_table_names():
        op.rename_table("pacientes", "paciente")
        try:
            op.execute("ALTER INDEX ix_pacientes_cpf RENAME TO ix_paciente_cpf")
        except Exception:  # noqa: BLE001
            pass
    if "usuarios" in insp.get_table_names():
        op.rename_table("usuarios", "usuariosistema")
        try:
            op.execute("ALTER INDEX ix_usuarios_email RENAME TO ix_usuariosistema_email")
        except Exception:  # noqa: BLE001
            pass
