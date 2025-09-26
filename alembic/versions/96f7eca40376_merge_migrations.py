"""Generic Alembic revision script.

Revision ID: 96f7eca40376
Revises: 20250918_migrations_consolidadas, 20250919_add_telefone
Create Date: 2025-09-19 16:28:40.681981
"""
from __future__ import annotations

from alembic import op  # type: ignore
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '96f7eca40376'
down_revision = ('20250918_migrations_consolidadas', '20250919_add_telefone')
branch_labels = None
depends_on = None



def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
