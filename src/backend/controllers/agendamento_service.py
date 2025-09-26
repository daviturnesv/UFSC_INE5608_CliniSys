"""
Service para Agendamento de Consultas
Implementa regras de negócio e validações para sistema de agendamento clínico
Baseado em padrões de mercado e requisitos do CliniSys-Escola
"""

from __future__ import annotations

import asyncio
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from ..models.consulta import Consulta, StatusConsulta, TipoConsulta, BloqueioHorario
from ..models.paciente import Paciente
from ..models.usuario import UsuarioSistema, PerfilUsuario, PerfilAluno
from ..models.clinica import Clinica
from ..models.fila import FilaAtendimento, TipoAtendimento, StatusFila


class AgendamentoService:
    """Service para gerenciamento de agendamento de consultas"""
    
    # Configurações padrão do sistema
    HORARIO_INICIO = time(8, 0)      # 8:00
    HORARIO_FIM = time(18, 0)        # 18:00
    DURACAO_PADRAO = 60              # 60 minutos
    INTERVALO_SLOTS = 30             # Slots de 30 minutos
    DIAS_SEMANA_PERMITIDOS = [0, 1, 2, 3, 4]  # Segunda a sexta (0=segunda)
    
    @classmethod
    async def criar_consulta(
        cls,
        session: AsyncSession,
        paciente_id: int,
        aluno_id: int,
        data_consulta: date,
        hora_inicio: time,
        tipo_consulta: TipoConsulta,
        duracao_minutos: int = DURACAO_PADRAO,
        motivo_consulta: str = None,
        observacoes: str = None,
        criado_por: int = None
    ) -> Consulta:
        """
        Cria nova consulta com todas as validações de negócio
        
        Args:
            session: Sessão do banco
            paciente_id: ID do paciente
            aluno_id: ID do aluno responsável
            data_consulta: Data da consulta
            hora_inicio: Horário de início
            tipo_consulta: Tipo da consulta
            duracao_minutos: Duração em minutos
            motivo_consulta: Motivo da consulta
            observacoes: Observações adicionais
            criado_por: ID do usuário que criou
            
        Returns:
            Consulta criada
            
        Raises:
            ValueError: Se alguma validação falhar
        """
        
        # 1. Validações básicas
        await cls._validar_dados_consulta(
            session, paciente_id, aluno_id, data_consulta, hora_inicio, duracao_minutos
        )
        
        # 2. Validar regras de negócio específicas
        await cls._validar_regras_negocio(
            session, paciente_id, aluno_id, data_consulta, hora_inicio, duracao_minutos
        )
        
        # 3. Obter dados complementares
        aluno = await cls._obter_aluno_com_clinica(session, aluno_id)
        clinica_id = aluno.clinica_id if hasattr(aluno, 'clinica_id') else None
        
        # 4. Calcular hora fim
        datetime_inicio = datetime.combine(data_consulta, hora_inicio)
        datetime_fim = datetime_inicio + timedelta(minutes=duracao_minutos)
        hora_fim = datetime_fim.time()
        
        # 5. Definir prioridade baseada no tipo
        prioridade = cls._calcular_prioridade(tipo_consulta)
        
        # 6. Criar consulta
        now = datetime.now()
        consulta = Consulta(
            paciente_id=paciente_id,
            aluno_id=aluno_id,
            clinica_id=clinica_id,
            data_consulta=data_consulta,
            hora_inicio=hora_inicio,
            hora_fim=hora_fim,
            duracao_minutos=duracao_minutos,
            tipo_consulta=tipo_consulta,
            status=StatusConsulta.agendada,
            prioridade=prioridade,
            motivo_consulta=motivo_consulta,
            observacoes=observacoes,
            numero_tentativa=1,
            criado_por=criado_por or aluno_id,
            criado_em=now,
            atualizado_em=now
        )
        
        session.add(consulta)
        await session.flush()  # Para obter o ID
        
        # 7. Atualizar status do paciente
        await cls._atualizar_status_paciente(session, paciente_id, "Consulta Agendada")
        
        return consulta
    
    @classmethod
    async def listar_consultas_aluno(
        cls,
        session: AsyncSession,
        aluno_id: int,
        data_inicio: date = None,
        data_fim: date = None,
        status_filtro: List[StatusConsulta] = None
    ) -> List[Consulta]:
        """
        Lista consultas de um aluno específico
        
        Args:
            session: Sessão do banco
            aluno_id: ID do aluno
            data_inicio: Data de início do filtro
            data_fim: Data de fim do filtro
            status_filtro: Lista de status para filtrar
            
        Returns:
            Lista de consultas do aluno
        """
        
        query = select(Consulta).where(Consulta.aluno_id == aluno_id)
        
        # Aplicar filtros de data
        if data_inicio:
            query = query.where(Consulta.data_consulta >= data_inicio)
        if data_fim:
            query = query.where(Consulta.data_consulta <= data_fim)
            
        # Aplicar filtro de status
        if status_filtro:
            query = query.where(Consulta.status.in_(status_filtro))
            
        # Ordenar por data e hora
        query = query.order_by(Consulta.data_consulta, Consulta.hora_inicio)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @classmethod
    async def obter_horarios_disponiveis(
        cls,
        session: AsyncSession,
        data_consulta: date,
        duracao_minutos: int = DURACAO_PADRAO,
        clinica_id: int = None
    ) -> List[time]:
        """
        Retorna horários disponíveis para agendamento em uma data
        
        Args:
            session: Sessão do banco
            data_consulta: Data desejada
            duracao_minutos: Duração da consulta
            clinica_id: ID da clínica (filtro opcional)
            
        Returns:
            Lista de horários disponíveis
        """
        
        # 1. Validar se é dia útil (RN03)
        if data_consulta.weekday() not in cls.DIAS_SEMANA_PERMITIDOS:
            return []
        
        # 2. Verificar se não há bloqueios
        if await cls._data_bloqueada(session, data_consulta, clinica_id):
            return []
        
        # 3. Gerar slots de horário
        slots_disponiveis = []
        horario_atual = cls.HORARIO_INICIO
        
        while horario_atual < cls.HORARIO_FIM:
            # Verificar se o slot completo cabe no horário comercial
            datetime_inicio = datetime.combine(data_consulta, horario_atual)
            datetime_fim = datetime_inicio + timedelta(minutes=duracao_minutos)
            
            if datetime_fim.time() <= cls.HORARIO_FIM:
                # Verificar se não há conflito com consultas existentes
                if not await cls._horario_conflita(session, data_consulta, horario_atual, duracao_minutos, clinica_id):
                    slots_disponiveis.append(horario_atual)
            
            # Próximo slot
            datetime_proximo = datetime_inicio + timedelta(minutes=cls.INTERVALO_SLOTS)
            horario_atual = datetime_proximo.time()
        
        return slots_disponiveis
    
    @classmethod
    async def cancelar_consulta(
        cls,
        session: AsyncSession,
        consulta_id: int,
        motivo_cancelamento: str,
        usuario_id: int
    ) -> Consulta:
        """
        Cancela uma consulta
        
        Args:
            session: Sessão do banco
            consulta_id: ID da consulta
            motivo_cancelamento: Motivo do cancelamento
            usuario_id: ID do usuário que cancelou
            
        Returns:
            Consulta cancelada
            
        Raises:
            ValueError: Se consulta não pode ser cancelada
        """
        
        # Buscar consulta
        result = await session.execute(select(Consulta).where(Consulta.id == consulta_id))
        consulta = result.scalar_one_or_none()
        
        if not consulta:
            raise ValueError("Consulta não encontrada")
        
        if not consulta.pode_ser_cancelada:
            raise ValueError(f"Consulta não pode ser cancelada. Status atual: {consulta.status.value}")
        
        # Cancelar
        consulta.status = StatusConsulta.cancelada
        consulta.motivo_cancelamento = motivo_cancelamento
        consulta.atualizado_em = func.now()
        
        # Atualizar status do paciente se necessário
        await cls._atualizar_status_paciente(session, consulta.paciente_id, "Disponível")
        
        return consulta
    
    @classmethod
    async def reagendar_consulta(
        cls,
        session: AsyncSession,
        consulta_id: int,
        nova_data: date,
        novo_horario: time,
        usuario_id: int,
        motivo_reagendamento: str = None
    ) -> Consulta:
        """
        Reagenda uma consulta existente
        
        Args:
            session: Sessão do banco
            consulta_id: ID da consulta original
            nova_data: Nova data
            novo_horario: Novo horário
            usuario_id: ID do usuário que reagendou
            motivo_reagendamento: Motivo do reagendamento
            
        Returns:
            Nova consulta criada
            
        Raises:
            ValueError: Se validações falharem
        """
        
        # Buscar consulta original
        result = await session.execute(select(Consulta).where(Consulta.id == consulta_id))
        consulta_original = result.scalar_one_or_none()
        
        if not consulta_original:
            raise ValueError("Consulta não encontrada")
        
        if not consulta_original.pode_ser_reagendada:
            raise ValueError(f"Consulta não pode ser reagendada. Status atual: {consulta_original.status.value}")
        
        # Validar nova data/horário
        await cls._validar_regras_negocio(
            session, 
            consulta_original.paciente_id, 
            consulta_original.aluno_id, 
            nova_data, 
            novo_horario, 
            consulta_original.duracao_minutos
        )
        
        # Marcar consulta original como reagendada
        consulta_original.status = StatusConsulta.reagendada
        consulta_original.motivo_cancelamento = motivo_reagendamento or "Reagendada"
        
        # Criar nova consulta
        nova_consulta = await cls.criar_consulta(
            session=session,
            paciente_id=consulta_original.paciente_id,
            aluno_id=consulta_original.aluno_id,
            data_consulta=nova_data,
            hora_inicio=novo_horario,
            tipo_consulta=consulta_original.tipo_consulta,
            duracao_minutos=consulta_original.duracao_minutos,
            motivo_consulta=consulta_original.motivo_consulta,
            observacoes=consulta_original.observacoes,
            criado_por=usuario_id
        )
        
        # Vincular ao reagendamento
        nova_consulta.consulta_origem_id = consulta_id
        nova_consulta.numero_tentativa = consulta_original.numero_tentativa + 1
        
        return nova_consulta
    
    @classmethod
    async def registrar_falta(
        cls,
        session: AsyncSession,
        consulta_id: int,
        usuario_id: int,
        observacao: str = None
    ) -> Tuple[Consulta, bool]:
        """
        Registra falta de paciente e verifica regra das 2 faltas (RN05)
        
        Args:
            session: Sessão do banco
            consulta_id: ID da consulta
            usuario_id: ID do usuário que registrou
            observacao: Observação sobre a falta
            
        Returns:
            Tupla (consulta, deve_encaminhar_desistencia)
        """
        
        # Buscar consulta
        result = await session.execute(select(Consulta).where(Consulta.id == consulta_id))
        consulta = result.scalar_one_or_none()
        
        if not consulta:
            raise ValueError("Consulta não encontrada")
        
        # Registrar falta
        consulta.status = StatusConsulta.falta
        consulta.motivo_cancelamento = f"Falta registrada: {observacao or 'Sem observação'}"
        
        # Verificar faltas consecutivas (RN05)
        faltas_consecutivas = await cls._contar_faltas_consecutivas(session, consulta.paciente_id)
        deve_encaminhar_desistencia = faltas_consecutivas >= 2
        
        if deve_encaminhar_desistencia:
            # Atualizar status do paciente para indicar necessidade de autorização
            await cls._atualizar_status_paciente(
                session, 
                consulta.paciente_id, 
                "Aguardando Autorização - Desistência"
            )
        
        return consulta, deve_encaminhar_desistencia
    
    # Métodos auxiliares privados
    
    @classmethod
    async def _validar_dados_consulta(
        cls,
        session: AsyncSession,
        paciente_id: int,
        aluno_id: int,
        data_consulta: date,
        hora_inicio: time,
        duracao_minutos: int
    ):
        """Validações básicas dos dados"""
        
        if data_consulta < date.today():
            raise ValueError("Não é possível agendar consulta para data passada")
        
        if not cls._horario_comercial(hora_inicio, duracao_minutos):
            raise ValueError("Consulta deve ser agendada no horário comercial (8h às 18h)")
        
        if data_consulta.weekday() not in cls.DIAS_SEMANA_PERMITIDOS:
            raise ValueError("Consultas só podem ser agendadas de segunda a sexta-feira")
        
        # Verificar se paciente existe
        result = await session.execute(select(Paciente).where(Paciente.id == paciente_id))
        if not result.scalar_one_or_none():
            raise ValueError("Paciente não encontrado")
        
        # Verificar se aluno existe
        result = await session.execute(select(UsuarioSistema).where(UsuarioSistema.id == aluno_id))
        aluno = result.scalar_one_or_none()
        if not aluno or aluno.perfil != PerfilUsuario.aluno:
            raise ValueError("Aluno não encontrado")
    
    @classmethod
    async def _validar_regras_negocio(
        cls,
        session: AsyncSession,
        paciente_id: int,
        aluno_id: int,
        data_consulta: date,
        hora_inicio: time,
        duracao_minutos: int
    ):
        """Validações das regras de negócio específicas"""
        
        # RN02: Paciente não pode ter mais de uma consulta no mesmo dia
        result = await session.execute(
            select(func.count(Consulta.id))
            .where(
                Consulta.paciente_id == paciente_id,
                Consulta.data_consulta == data_consulta,
                Consulta.status.in_([StatusConsulta.agendada, StatusConsulta.confirmada])
            )
        )
        consultas_mesmo_dia = result.scalar()
        if consultas_mesmo_dia > 0:
            raise ValueError("Paciente já possui consulta agendada para esta data")
        
        # RN04: Aluno só pode agendar na clínica que está matriculado
        aluno = await cls._obter_aluno_com_clinica(session, aluno_id)
        if not hasattr(aluno, 'clinica_id') or not aluno.clinica_id:
            raise ValueError("Aluno não está associado a uma clínica")
        
        # RN06: Não pode ter conflito de horário
        if await cls._horario_conflita(session, data_consulta, hora_inicio, duracao_minutos):
            raise ValueError("Já existe consulta agendada para este horário")
    
    @classmethod
    async def _obter_aluno_com_clinica(cls, session: AsyncSession, aluno_id: int):
        """Obtém dados do aluno com informações da clínica"""
        
        result = await session.execute(
            select(UsuarioSistema)
            .join(PerfilAluno, UsuarioSistema.id == PerfilAluno.user_id)
            .where(UsuarioSistema.id == aluno_id)
        )
        aluno = result.scalar_one_or_none()
        
        if aluno:
            # Buscar perfil do aluno
            result_perfil = await session.execute(
                select(PerfilAluno).where(PerfilAluno.user_id == aluno_id)
            )
            perfil = result_perfil.scalar_one_or_none()
            if perfil:
                aluno.clinica_id = perfil.clinica_id
        
        return aluno
    
    @classmethod
    def _calcular_prioridade(cls, tipo_consulta: TipoConsulta) -> int:
        """Calcula prioridade baseada no tipo de consulta"""
        prioridades = {
            TipoConsulta.triagem: 1,      # Alta prioridade
            TipoConsulta.retorno: 2,      # Média prioridade
            TipoConsulta.clinica_i: 3,    # Normal
            TipoConsulta.clinica_ii: 3,   # Normal
            TipoConsulta.clinica_iii: 2,  # Média (mais complexa)
        }
        return prioridades.get(tipo_consulta, 3)
    
    @classmethod
    def _horario_comercial(cls, hora_inicio: time, duracao_minutos: int) -> bool:
        """Verifica se horário está dentro do comercial"""
        datetime_inicio = datetime.combine(date.today(), hora_inicio)
        datetime_fim = datetime_inicio + timedelta(minutes=duracao_minutos)
        
        return (
            hora_inicio >= cls.HORARIO_INICIO and
            datetime_fim.time() <= cls.HORARIO_FIM
        )
    
    @classmethod
    async def _horario_conflita(
        cls,
        session: AsyncSession,
        data_consulta: date,
        hora_inicio: time,
        duracao_minutos: int,
        clinica_id: int = None
    ) -> bool:
        """Verifica se horário conflita com consultas existentes"""
        
        datetime_inicio = datetime.combine(data_consulta, hora_inicio)
        datetime_fim = datetime_inicio + timedelta(minutes=duracao_minutos)
        
        query = select(func.count(Consulta.id)).where(
            Consulta.data_consulta == data_consulta,
            Consulta.status.in_([StatusConsulta.agendada, StatusConsulta.confirmada]),
            or_(
                # Novo horário inicia durante consulta existente
                and_(
                    Consulta.hora_inicio <= hora_inicio,
                    Consulta.hora_fim > hora_inicio
                ),
                # Novo horário termina durante consulta existente  
                and_(
                    Consulta.hora_inicio < datetime_fim.time(),
                    Consulta.hora_fim >= datetime_fim.time()
                ),
                # Novo horário engloba consulta existente
                and_(
                    Consulta.hora_inicio >= hora_inicio,
                    Consulta.hora_fim <= datetime_fim.time()
                )
            )
        )
        
        if clinica_id:
            query = query.where(Consulta.clinica_id == clinica_id)
        
        result = await session.execute(query)
        return result.scalar() > 0
    
    @classmethod
    async def _data_bloqueada(
        cls,
        session: AsyncSession,
        data_consulta: date,
        clinica_id: int = None
    ) -> bool:
        """Verifica se data está bloqueada"""
        
        query = select(func.count(BloqueioHorario.id)).where(
            BloqueioHorario.data_inicio <= data_consulta,
            BloqueioHorario.data_fim >= data_consulta
        )
        
        if clinica_id:
            query = query.where(
                or_(
                    BloqueioHorario.clinica_id == clinica_id,
                    BloqueioHorario.clinica_id.is_(None)
                )
            )
        
        result = await session.execute(query)
        return result.scalar() > 0
    
    @classmethod
    async def _contar_faltas_consecutivas(
        cls,
        session: AsyncSession,
        paciente_id: int
    ) -> int:
        """Conta faltas consecutivas de um paciente"""
        
        # Buscar últimas consultas do paciente ordenadas por data desc
        result = await session.execute(
            select(Consulta)
            .where(Consulta.paciente_id == paciente_id)
            .order_by(desc(Consulta.data_consulta), desc(Consulta.hora_inicio))
            .limit(5)  # Últimas 5 consultas
        )
        consultas = result.scalars().all()
        
        faltas_consecutivas = 0
        for consulta in consultas:
            if consulta.status == StatusConsulta.falta:
                faltas_consecutivas += 1
            else:
                break  # Para na primeira consulta que não foi falta
        
        return faltas_consecutivas
    
    @classmethod
    async def _atualizar_status_paciente(
        cls,
        session: AsyncSession,
        paciente_id: int,
        novo_status: str
    ):
        """Atualiza status do paciente"""
        
        result = await session.execute(select(Paciente).where(Paciente.id == paciente_id))
        paciente = result.scalar_one_or_none()
        
        if paciente:
            paciente.statusAtendimento = novo_status