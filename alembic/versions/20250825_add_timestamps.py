"""add timestamps a usuarios e pacientes

Revision ID: 20250825_add_timestamps
Revises: 20250824_ajuste
Create Date: 2025-08-25
"""
from __future__ import annotations

from alembic import op  # type: ignore
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250825_add_timestamps"
down_revision = "20250824_ajuste"
branch_labels = None
depends_on = None


def _add_col_if_absent(table: str, column: str, coltype) -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c.get("name") for c in insp.get_columns(table)]
    if column not in cols:
        op.add_column(table, sa.Column(column, coltype, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))


def upgrade() -> None:
    # Em produção as tabelas já foram renomeadas: usuarios, pacientes
    _add_col_if_absent("usuarios", "created_at", sa.DateTime(timezone=True))
    _add_col_if_absent("usuarios", "updated_at", sa.DateTime(timezone=True))
    _add_col_if_absent("pacientes", "created_at", sa.DateTime(timezone=True))
    _add_col_if_absent("pacientes", "updated_at", sa.DateTime(timezone=True))

    # Ajustar updated_at para refletir atualizações futuras: em SQLite não há on update automático.
    # Em Postgres poderia-se usar trigger, aqui mantemos aplicação cuidando do campo.


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    for table in ("usuarios", "pacientes"):
        if table in insp.get_table_names():
            cols = [c.get("name") for c in insp.get_columns(table)]
            for col in ("updated_at", "created_at"):
                if col in cols:
                    try:
                        op.drop_column(table, col)
                    except Exception:  # noqa: BLE001
                        pass
