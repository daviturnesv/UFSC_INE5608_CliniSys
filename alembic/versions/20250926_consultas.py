"""Adiciona sistema de agendamento de consultas

Revision ID: 20250926_consultas
Revises: 20250924_175038
Create Date: 2025-09-26 12:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250926_consultas'
down_revision = '20250924_175038'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Adiciona tabelas do sistema de agendamento"""
    
    # Criar tabela de consultas
    op.create_table('consultas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('paciente_id', sa.Integer(), nullable=False),
        sa.Column('aluno_id', sa.Integer(), nullable=False),
        sa.Column('professor_id', sa.Integer(), nullable=True),
        sa.Column('clinica_id', sa.Integer(), nullable=True),
        sa.Column('data_consulta', sa.Date(), nullable=False),
        sa.Column('hora_inicio', sa.Time(), nullable=False),
        sa.Column('hora_fim', sa.Time(), nullable=True),
        sa.Column('duracao_minutos', sa.Integer(), nullable=False),
        sa.Column('tipo_consulta', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('prioridade', sa.Integer(), nullable=False),
        sa.Column('motivo_consulta', sa.String(length=500), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('procedimentos_planejados', sa.Text(), nullable=True),
        sa.Column('numero_tentativa', sa.Integer(), nullable=False),
        sa.Column('consulta_origem_id', sa.Integer(), nullable=True),
        sa.Column('data_confirmacao', sa.DateTime(), nullable=True),
        sa.Column('confirmada_por', sa.Integer(), nullable=True),
        sa.Column('data_inicio_real', sa.DateTime(), nullable=True),
        sa.Column('data_fim_real', sa.DateTime(), nullable=True),
        sa.Column('motivo_cancelamento', sa.String(length=300), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=False),
        sa.Column('atualizado_em', sa.DateTime(), nullable=False),
        sa.Column('criado_por', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['aluno_id'], ['usuarios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['clinica_id'], ['clinicas.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['confirmada_por'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['consulta_origem_id'], ['consultas.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['criado_por'], ['usuarios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['paciente_id'], ['pacientes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['professor_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Criar índices para performance
    op.create_index('ix_consultas_id', 'consultas', ['id'])
    op.create_index('ix_consultas_paciente_id', 'consultas', ['paciente_id'])
    op.create_index('ix_consultas_aluno_id', 'consultas', ['aluno_id'])
    op.create_index('ix_consultas_professor_id', 'consultas', ['professor_id'])
    op.create_index('ix_consultas_clinica_id', 'consultas', ['clinica_id'])
    op.create_index('ix_consultas_data_consulta', 'consultas', ['data_consulta'])
    op.create_index('ix_consultas_hora_inicio', 'consultas', ['hora_inicio'])
    op.create_index('ix_consultas_tipo_consulta', 'consultas', ['tipo_consulta'])
    op.create_index('ix_consultas_status', 'consultas', ['status'])
    
    # Criar tabela de bloqueios de horário
    op.create_table('bloqueios_horario',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('data_inicio', sa.Date(), nullable=False),
        sa.Column('data_fim', sa.Date(), nullable=False),
        sa.Column('hora_inicio', sa.Time(), nullable=True),
        sa.Column('hora_fim', sa.Time(), nullable=True),
        sa.Column('clinica_id', sa.Integer(), nullable=True),
        sa.Column('professor_id', sa.Integer(), nullable=True),
        sa.Column('motivo', sa.String(length=300), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=False),
        sa.Column('criado_por', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['clinica_id'], ['clinicas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['criado_por'], ['usuarios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['professor_id'], ['usuarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Criar índices para bloqueios
    op.create_index('ix_bloqueios_horario_id', 'bloqueios_horario', ['id'])
    op.create_index('ix_bloqueios_horario_data_inicio', 'bloqueios_horario', ['data_inicio'])
    op.create_index('ix_bloqueios_horario_data_fim', 'bloqueios_horario', ['data_fim'])


def downgrade() -> None:
    """Remove tabelas do sistema de agendamento"""
    
    # Remover índices
    op.drop_index('ix_bloqueios_horario_data_fim', table_name='bloqueios_horario')
    op.drop_index('ix_bloqueios_horario_data_inicio', table_name='bloqueios_horario')
    op.drop_index('ix_bloqueios_horario_id', table_name='bloqueios_horario')
    
    op.drop_index('ix_consultas_status', table_name='consultas')
    op.drop_index('ix_consultas_tipo_consulta', table_name='consultas')
    op.drop_index('ix_consultas_hora_inicio', table_name='consultas')
    op.drop_index('ix_consultas_data_consulta', table_name='consultas')
    op.drop_index('ix_consultas_clinica_id', table_name='consultas')
    op.drop_index('ix_consultas_professor_id', table_name='consultas')
    op.drop_index('ix_consultas_aluno_id', table_name='consultas')
    op.drop_index('ix_consultas_paciente_id', table_name='consultas')
    op.drop_index('ix_consultas_id', table_name='consultas')
    
    # Remover tabelas
    op.drop_table('bloqueios_horario')
    op.drop_table('consultas')