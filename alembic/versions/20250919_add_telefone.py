"""add telefone field to usuarios

Revision ID: 20250919_add_telefone
Revises: 20250825_refresh_tokens
Create Date: 2025-09-19 16:05:02.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250919_add_telefone'
down_revision = '20250825_refresh_tokens'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adicionar campo telefone na tabela usuarios (opcional)
    op.add_column('usuarios', sa.Column('telefone', sa.String(20), nullable=True))


def downgrade() -> None:
    # Remover campo telefone da tabela usuarios
    op.drop_column('usuarios', 'telefone')