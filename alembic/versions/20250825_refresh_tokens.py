"""add refresh tokens table

Revision ID: 20250825_refresh_tokens
Revises: 20250825_add_timestamps
Create Date: 2025-08-25
"""
from __future__ import annotations

from alembic import op  # type: ignore
import sqlalchemy as sa

revision = "20250825_refresh_tokens"
down_revision = "20250825_add_timestamps"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "refresh_tokens" not in insp.get_table_names():
        op.create_table(
            "refresh_tokens",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False),
            sa.Column("token_hash", sa.String(length=255), nullable=False),
            sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
            sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revogado", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
        op.create_index("ix_refresh_tokens_usuario", "refresh_tokens", ["usuario_id"])    # noqa: E501
        op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)  # noqa: E501
        op.create_index("ix_refresh_tokens_expira_em", "refresh_tokens", ["expira_em"])  # noqa: E501


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "refresh_tokens" in insp.get_table_names():
        try:
            op.drop_index("ix_refresh_tokens_usuario", table_name="refresh_tokens")
            op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
            op.drop_index("ix_refresh_tokens_expira_em", table_name="refresh_tokens")
        except Exception:  # noqa: BLE001
            pass
        op.drop_table("refresh_tokens")
