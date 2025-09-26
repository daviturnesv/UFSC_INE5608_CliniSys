"""
Modelo de Consulta para Sistema de Agendamento
Baseado em sistemas clínicos padrão e regras do projeto CliniSys-Escola
"""

from __future__ import annotations

import enum
from datetime import datetime, date, time
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Date, Time, Text, ForeignKey, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base


class StatusConsulta(enum.Enum):
    """Status da consulta seguindo workflow clínico padrão"""
    agendada = "agendada"           # Consulta agendada
    confirmada = "confirmada"       # Paciente confirmou presença
    em_andamento = "em_andamento"   # Consulta em progresso
    concluida = "concluida"         # Consulta finalizada
    cancelada = "cancelada"         # Cancelada pelo sistema/paciente
    falta = "falta"                 # Paciente faltou
    reagendada = "reagendada"       # Reagendada para outra data


class TipoConsulta(enum.Enum):
    """Tipo de consulta baseado nas clínicas do projeto"""
    clinica_i = "clinica_i"         # Clínica I - procedimentos básicos
    clinica_ii = "clinica_ii"       # Clínica II - procedimentos intermediários  
    clinica_iii = "clinica_iii"     # Clínica III - procedimentos avançados
    triagem = "triagem"             # Consulta de triagem
    retorno = "retorno"             # Consulta de retorno


class Consulta(Base):
    """
    Modelo para agendamento de consultas
    Baseado em padrões de sistemas hospitalares e regras de negócio do projeto
    """
    __tablename__ = "consultas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Relacionamentos principais
    paciente_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("pacientes.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    aluno_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("usuarios.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    professor_id: Mapped[int | None] = mapped_column(
        Integer, 
        ForeignKey("usuarios.id", ondelete="SET NULL"), 
        nullable=True,
        index=True
    )
    clinica_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("clinicas.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Dados do agendamento
    data_consulta: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False, index=True)
    hora_fim: Mapped[time | None] = mapped_column(Time, nullable=True)
    duracao_minutos: Mapped[int] = mapped_column(Integer, default=60, nullable=False)  # Duração padrão 60min
    
    # Classificação e controle
    tipo_consulta: Mapped[TipoConsulta] = mapped_column(
        Enum(TipoConsulta, name="tipo_consulta"), 
        nullable=False,
        index=True
    )
    status: Mapped[StatusConsulta] = mapped_column(
        Enum(StatusConsulta, name="status_consulta"), 
        default=StatusConsulta.agendada,
        nullable=False,
        index=True
    )
    prioridade: Mapped[int] = mapped_column(Integer, default=3, nullable=False)  # 1=Alta, 2=Média, 3=Normal
    
    # Informações complementares
    motivo_consulta: Mapped[str | None] = mapped_column(String(500), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    procedimentos_planejados: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Controle de faltas (RN05)
    numero_tentativa: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    consulta_origem_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("consultas.id", ondelete="SET NULL"),
        nullable=True  # Para reagendamentos, referência à consulta original
    )
    
    # Dados de confirmação
    data_confirmacao: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmada_por: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Dados de conclusão
    data_inicio_real: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    data_fim_real: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    motivo_cancelamento: Mapped[str | None] = mapped_column(String(300), nullable=True)
    
    # Timestamps padrão
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=func.now(), 
        nullable=False
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
    criado_por: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("usuarios.id", ondelete="CASCADE"), 
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<Consulta(id={self.id}, data={self.data_consulta}, status='{self.status.value}')>"

    @property
    def datetime_inicio(self) -> datetime:
        """Combina data e hora de início em datetime"""
        return datetime.combine(self.data_consulta, self.hora_inicio)
    
    @property
    def datetime_fim(self) -> datetime:
        """Combina data e hora de fim em datetime"""
        if self.hora_fim:
            return datetime.combine(self.data_consulta, self.hora_fim)
        # Calcular fim baseado na duração
        from datetime import timedelta
        return self.datetime_inicio + timedelta(minutes=self.duracao_minutos)
    
    @property
    def pode_ser_cancelada(self) -> bool:
        """Verifica se consulta pode ser cancelada"""
        return self.status in [StatusConsulta.agendada, StatusConsulta.confirmada]
    
    @property
    def pode_ser_reagendada(self) -> bool:
        """Verifica se consulta pode ser reagendada"""
        return self.status in [StatusConsulta.agendada, StatusConsulta.confirmada, StatusConsulta.falta]
    
    @property
    def esta_no_horario_comercial(self) -> bool:
        """Verifica se está no horário comercial (RN03)"""
        if not self.hora_inicio:
            return False
        # Segunda a sexta, 8h às 18h
        return (8 <= self.hora_inicio.hour < 18)
    
    @property
    def cor_status(self) -> str:
        """Retorna cor para interface baseada no status"""
        cores = {
            StatusConsulta.agendada: "#4CAF50",      # Verde
            StatusConsulta.confirmada: "#2196F3",    # Azul
            StatusConsulta.em_andamento: "#FF9800",  # Laranja
            StatusConsulta.concluida: "#757575",     # Cinza
            StatusConsulta.cancelada: "#F44336",     # Vermelho
            StatusConsulta.falta: "#E91E63",         # Rosa
            StatusConsulta.reagendada: "#9C27B0"     # Roxo
        }
        return cores.get(self.status, "#757575")


class BloqueioHorario(Base):
    """
    Modelo para bloqueios de horário (feriados, férias, etc.)
    Impede agendamentos em períodos específicos
    """
    __tablename__ = "bloqueios_horario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    data_fim: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    hora_inicio: Mapped[time | None] = mapped_column(Time, nullable=True)  # Se None, bloqueia o dia todo
    hora_fim: Mapped[time | None] = mapped_column(Time, nullable=True)
    
    # Escopo do bloqueio
    clinica_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("clinicas.id", ondelete="CASCADE"),
        nullable=True  # Se None, bloqueio vale para todas as clínicas
    )
    professor_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=True  # Se None, bloqueio vale para todos os professores
    )
    
    motivo: Mapped[str] = mapped_column(String(300), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamps
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=func.now(), 
        nullable=False
    )
    criado_por: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("usuarios.id", ondelete="CASCADE"), 
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<BloqueioHorario(id={self.id}, data={self.data_inicio}, motivo='{self.motivo}')>"