"""add_triagem_system

Revision ID: 20250924_175038
Revises: 96f7eca40376
Create Date: 2025-09-24 17:50:38.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '20250924_175038'
down_revision = '96f7eca40376'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Criar tabela de registros de triagem
    op.create_table('registros_triagem',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('paciente_id', sa.Integer(), nullable=False),
        sa.Column('aluno_id', sa.Integer(), nullable=True),
        sa.Column('prioridade', sa.Enum('EMERGENCIA', 'MUITO_URGENTE', 'URGENTE', 'POUCO_URGENTE', 'NAO_URGENTE', name='prioridade_triagem'), nullable=True),
        sa.Column('situacao', sa.Enum('AGUARDANDO', 'EM_ANDAMENTO', 'CONCLUIDA', 'CANCELADA', name='situacao_triagem'), nullable=False),
        sa.Column('queixa_principal', sa.String(length=500), nullable=True),
        sa.Column('sinais_vitais', sa.Text(), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('necessidades_identificadas', sa.Text(), nullable=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('triagem_iniciada_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('triagem_concluida_em', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['aluno_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['paciente_id'], ['pacientes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_registros_triagem_aluno_id'), 'registros_triagem', ['aluno_id'], unique=False)
    op.create_index(op.f('ix_registros_triagem_paciente_id'), 'registros_triagem', ['paciente_id'], unique=False)
    op.create_index(op.f('ix_registros_triagem_prioridade'), 'registros_triagem', ['prioridade'], unique=False)
    op.create_index(op.f('ix_registros_triagem_situacao'), 'registros_triagem', ['situacao'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_registros_triagem_situacao'), table_name='registros_triagem')
    op.drop_index(op.f('ix_registros_triagem_prioridade'), table_name='registros_triagem')
    op.drop_index(op.f('ix_registros_triagem_paciente_id'), table_name='registros_triagem')
    op.drop_index(op.f('ix_registros_triagem_aluno_id'), table_name='registros_triagem')
    op.drop_table('registros_triagem')
    
    # Remover enums
    sa.Enum(name='prioridade_triagem').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='situacao_triagem').drop(op.get_bind(), checkfirst=True)