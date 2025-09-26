"""
Modelos para sistema de triagem clínica
Baseado no Protocolo Manchester de Classificação de Risco
"""
from __future__ import annotations

import enum
from datetime import datetime, timezone
from sqlalchemy import Integer, Enum, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base
from .paciente import Paciente


class PrioridadeTriagem(enum.Enum):
    """
    Classificação de risco baseada no Protocolo Manchester
    """
    EMERGENCIA = "emergencia"        # Vermelho - Atendimento imediato
    MUITO_URGENTE = "muito_urgente"  # Laranja - Até 10 minutos
    URGENTE = "urgente"              # Amarelo - Até 60 minutos
    POUCO_URGENTE = "pouco_urgente"  # Verde - Até 2 horas
    NAO_URGENTE = "nao_urgente"      # Azul - Até 4 horas


class SituacaoTriagem(enum.Enum):
    AGUARDANDO = "aguardando"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"


class RegistroTriagem(Base):
    """
    Registro de triagem de um paciente
    """
    __tablename__ = "registros_triagem"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False, index=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Dados da triagem
    prioridade: Mapped[PrioridadeTriagem | None] = mapped_column(
        Enum(PrioridadeTriagem, name="prioridade_triagem"), 
        nullable=True, 
        index=True
    )
    situacao: Mapped[SituacaoTriagem] = mapped_column(
        Enum(SituacaoTriagem, name="situacao_triagem"), 
        nullable=False, 
        default=SituacaoTriagem.AGUARDANDO,
        index=True
    )
    
    # Informações clínicas
    queixa_principal: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sinais_vitais: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string com PA, temp, etc.
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    necessidades_identificadas: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamps
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    triagem_iniciada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    triagem_concluida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    paciente: Mapped[Paciente] = relationship()
    
    @property
    def cor_prioridade(self) -> str:
        """Retorna a cor da prioridade para interface visual"""
        if not self.prioridade:
            return "#CCCCCC"  # Cinza - sem triagem
        
        cores = {
            PrioridadeTriagem.EMERGENCIA: "#DC2626",       # Vermelho
            PrioridadeTriagem.MUITO_URGENTE: "#EA580C",    # Laranja
            PrioridadeTriagem.URGENTE: "#EAB308",          # Amarelo
            PrioridadeTriagem.POUCO_URGENTE: "#16A34A",    # Verde
            PrioridadeTriagem.NAO_URGENTE: "#2563EB"       # Azul
        }
        return cores.get(self.prioridade, "#CCCCCC")
    
    @property
    def descricao_prioridade(self) -> str:
        """Retorna descrição legível da prioridade"""
        if not self.prioridade:
            return "Aguardando Triagem"
        
        descricoes = {
            PrioridadeTriagem.EMERGENCIA: "Emergência - Imediato",
            PrioridadeTriagem.MUITO_URGENTE: "Muito Urgente - 10 min",
            PrioridadeTriagem.URGENTE: "Urgente - 1 hora",
            PrioridadeTriagem.POUCO_URGENTE: "Pouco Urgente - 2 horas",
            PrioridadeTriagem.NAO_URGENTE: "Não Urgente - 4 horas"
        }
        return descricoes.get(self.prioridade, "Indeterminado")
    
    @property
    def tempo_espera_max_minutos(self) -> int | None:
        """Tempo máximo de espera em minutos baseado na prioridade"""
        if not self.prioridade:
            return None
        
        tempos = {
            PrioridadeTriagem.EMERGENCIA: 0,           # Imediato
            PrioridadeTriagem.MUITO_URGENTE: 10,       # 10 minutos
            PrioridadeTriagem.URGENTE: 60,             # 1 hora
            PrioridadeTriagem.POUCO_URGENTE: 120,      # 2 horas
            PrioridadeTriagem.NAO_URGENTE: 240         # 4 horas
        }
        return tempos.get(self.prioridade)

    def iniciar_triagem(self, aluno_id: int) -> None:
        """Inicia o processo de triagem"""
        self.aluno_id = aluno_id
        self.situacao = SituacaoTriagem.EM_ANDAMENTO
        self.triagem_iniciada_em = datetime.now(timezone.utc)
        self.atualizado_em = datetime.now(timezone.utc)

    def concluir_triagem(
        self, 
        prioridade: PrioridadeTriagem,
        queixa_principal: str | None = None,
        necessidades: str | None = None,
        observacoes: str | None = None
    ) -> None:
        """Conclui o processo de triagem"""
        self.prioridade = prioridade
        self.queixa_principal = queixa_principal
        self.necessidades_identificadas = necessidades
        self.observacoes = observacoes
        self.situacao = SituacaoTriagem.CONCLUIDA
        self.triagem_concluida_em = datetime.now(timezone.utc)
        self.atualizado_em = datetime.now(timezone.utc)