"""
Serviços para gerenciamento de triagem clínica
"""
from __future__ import annotations

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone

from ..models.triagem import RegistroTriagem, PrioridadeTriagem, SituacaoTriagem
from ..models.paciente import Paciente
from ..models.fila import FilaAtendimento, TipoAtendimento, StatusFila


async def criar_registro_triagem(
    session: AsyncSession,
    paciente_id: int
) -> RegistroTriagem:
    """
    Cria um novo registro de triagem para um paciente
    """
    # Verificar se já existe registro de triagem pendente
    stmt = select(RegistroTriagem).where(
        and_(
            RegistroTriagem.paciente_id == paciente_id,
            RegistroTriagem.situacao.in_([SituacaoTriagem.AGUARDANDO, SituacaoTriagem.EM_ANDAMENTO])
        )
    )
    resultado = await session.execute(stmt)
    triagem_existente = resultado.scalar_one_or_none()
    
    if triagem_existente:
        return triagem_existente
    
    # Criar novo registro
    novo_registro = RegistroTriagem(
        paciente_id=paciente_id,
        situacao=SituacaoTriagem.AGUARDANDO
    )
    
    session.add(novo_registro)
    await session.flush()
    await session.refresh(novo_registro)
    
    return novo_registro


async def listar_fila_triagem(
    session: AsyncSession,
    situacao: Optional[SituacaoTriagem] = None,
    prioridade: Optional[PrioridadeTriagem] = None,
    incluir_concluidas: bool = False
) -> List[RegistroTriagem]:
    """
    Lista registros da fila de triagem com filtros opcionais
    """
    stmt = select(RegistroTriagem).options(selectinload(RegistroTriagem.paciente))
    
    # Filtros
    condicoes = []
    
    if situacao:
        condicoes.append(RegistroTriagem.situacao == situacao)
    elif not incluir_concluidas:
        # Por padrão, excluir triagens concluídas e canceladas
        condicoes.append(RegistroTriagem.situacao.in_([
            SituacaoTriagem.AGUARDANDO,
            SituacaoTriagem.EM_ANDAMENTO
        ]))
    
    if prioridade:
        condicoes.append(RegistroTriagem.prioridade == prioridade)
    
    if condicoes:
        stmt = stmt.where(and_(*condicoes))
    
    # Ordenação: prioridade (emergência primeiro), depois por data de criação
    stmt = stmt.order_by(
        RegistroTriagem.prioridade.asc().nulls_last(),
        RegistroTriagem.criado_em.asc()
    )
    
    resultado = await session.execute(stmt)
    return list(resultado.scalars().all())


async def iniciar_triagem(
    session: AsyncSession,
    registro_id: int,
    aluno_id: int
) -> RegistroTriagem:
    """
    Inicia o processo de triagem de um paciente
    """
    registro = await session.get(RegistroTriagem, registro_id)
    if not registro:
        raise ValueError("Registro de triagem não encontrado")
    
    if registro.situacao != SituacaoTriagem.AGUARDANDO:
        raise ValueError("Triagem não está aguardando para ser iniciada")
    
    registro.iniciar_triagem(aluno_id)
    await session.commit()
    await session.refresh(registro)
    
    return registro


async def concluir_triagem(
    session: AsyncSession,
    registro_id: int,
    prioridade: PrioridadeTriagem,
    queixa_principal: Optional[str] = None,
    necessidades: Optional[str] = None,
    observacoes: Optional[str] = None
) -> RegistroTriagem:
    """
    Conclui o processo de triagem de um paciente
    """
    registro = await session.get(RegistroTriagem, registro_id)
    if not registro:
        raise ValueError("Registro de triagem não encontrado")
    
    if registro.situacao != SituacaoTriagem.EM_ANDAMENTO:
        raise ValueError("Triagem não está em andamento")
    
    # Concluir triagem
    registro.concluir_triagem(
        prioridade=prioridade,
        queixa_principal=queixa_principal,
        necessidades=necessidades,
        observacoes=observacoes
    )
    
    # Atualizar status do paciente
    paciente = await session.get(Paciente, registro.paciente_id)
    if paciente:
        paciente.statusAtendimento = "Triado - Aguardando Consulta"
    
    # Adicionar à fila de consultas se não estiver lá
    await _adicionar_a_fila_consulta(session, registro.paciente_id)
    
    await session.commit()
    await session.refresh(registro)
    
    return registro


async def cancelar_triagem(
    session: AsyncSession,
    registro_id: int,
    motivo: Optional[str] = None
) -> RegistroTriagem:
    """
    Cancela um registro de triagem
    """
    registro = await session.get(RegistroTriagem, registro_id)
    if not registro:
        raise ValueError("Registro de triagem não encontrado")
    
    registro.situacao = SituacaoTriagem.CANCELADA
    if motivo:
        registro.observacoes = f"Cancelado: {motivo}"
    registro.atualizado_em = datetime.now(timezone.utc)
    
    await session.commit()
    await session.refresh(registro)
    
    return registro


async def obter_estatisticas_triagem(session: AsyncSession) -> dict:
    """
    Obtém estatísticas da fila de triagem
    """
    # Contar por situação
    stmt_aguardando = select(func.count(RegistroTriagem.id)).where(
        RegistroTriagem.situacao == SituacaoTriagem.AGUARDANDO
    )
    stmt_em_andamento = select(func.count(RegistroTriagem.id)).where(
        RegistroTriagem.situacao == SituacaoTriagem.EM_ANDAMENTO
    )
    
    # Contar por prioridade (apenas não concluídas)
    stmt_emergencia = select(func.count(RegistroTriagem.id)).where(
        and_(
            RegistroTriagem.prioridade == PrioridadeTriagem.EMERGENCIA,
            RegistroTriagem.situacao.in_([SituacaoTriagem.AGUARDANDO, SituacaoTriagem.EM_ANDAMENTO])
        )
    )
    
    aguardando = (await session.execute(stmt_aguardando)).scalar() or 0
    em_andamento = (await session.execute(stmt_em_andamento)).scalar() or 0
    emergencia = (await session.execute(stmt_emergencia)).scalar() or 0
    
    return {
        'aguardando_triagem': aguardando,
        'triagem_em_andamento': em_andamento,
        'casos_emergencia': emergencia,
        'total_pendente': aguardando + em_andamento
    }


async def obter_pacientes_aguardando_triagem(session: AsyncSession) -> List[Paciente]:
    """
    Obtém lista de pacientes que ainda não passaram por triagem
    """
    # Buscar pacientes com status "Aguardando Triagem" que não têm registro de triagem
    stmt = select(Paciente).where(
        and_(
            Paciente.statusAtendimento == "Aguardando Triagem",
            ~Paciente.id.in_(
                select(RegistroTriagem.paciente_id).where(
                    RegistroTriagem.situacao.in_([
                        SituacaoTriagem.AGUARDANDO,
                        SituacaoTriagem.EM_ANDAMENTO,
                        SituacaoTriagem.CONCLUIDA
                    ])
                )
            )
        )
    ).order_by(Paciente.created_at)
    
    resultado = await session.execute(stmt)
    return list(resultado.scalars().all())


async def _adicionar_a_fila_consulta(
    session: AsyncSession,
    paciente_id: int
) -> None:
    """
    Adiciona paciente à fila de consultas após triagem (função auxiliar)
    """
    # Verificar se já está na fila de consultas
    stmt = select(FilaAtendimento).where(
        and_(
            FilaAtendimento.paciente_id == paciente_id,
            FilaAtendimento.tipo == TipoAtendimento.consulta,
            FilaAtendimento.status == StatusFila.aguardando
        )
    )
    
    resultado = await session.execute(stmt)
    if not resultado.scalar_one_or_none():
        # Adicionar à fila de consultas
        nova_entrada = FilaAtendimento(
            paciente_id=paciente_id,
            tipo=TipoAtendimento.consulta,
            status=StatusFila.aguardando,
            observacao="Paciente triado e liberado para consulta"
        )
        session.add(nova_entrada)


async def buscar_registro_por_paciente(
    session: AsyncSession,
    paciente_id: int,
    incluir_historico: bool = False
) -> List[RegistroTriagem]:
    """
    Busca registros de triagem de um paciente específico
    """
    stmt = select(RegistroTriagem).options(selectinload(RegistroTriagem.paciente)).where(
        RegistroTriagem.paciente_id == paciente_id
    )
    
    if not incluir_historico:
        # Apenas registros ativos
        stmt = stmt.where(RegistroTriagem.situacao.in_([
            SituacaoTriagem.AGUARDANDO,
            SituacaoTriagem.EM_ANDAMENTO,
            SituacaoTriagem.CONCLUIDA
        ]))
    
    stmt = stmt.order_by(RegistroTriagem.criado_em.desc())
    
    resultado = await session.execute(stmt)
    return list(resultado.scalars().all())