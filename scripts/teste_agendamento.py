"""
Script para testar o sistema de agendamento de consultas
Cria dados de teste e demonstra funcionalidades
"""

import asyncio
from datetime import date, time, datetime, timedelta
import sys
import os

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.backend.db.database import AsyncSessionLocal
from src.backend.controllers.agendamento_service import AgendamentoService
from src.backend.models.consulta import TipoConsulta, StatusConsulta
from src.backend.models.paciente import Paciente
from src.backend.models.usuario import UsuarioSistema, PerfilUsuario
from sqlalchemy import select


async def criar_dados_teste_agendamento():
    """Cria dados de teste para o sistema de agendamento"""
    
    print("🏥 Testando Sistema de Agendamento de Consultas...")
    
    async with AsyncSessionLocal() as session:
        
        # 1. Buscar aluno para testar
        result = await session.execute(
            select(UsuarioSistema)
            .where(UsuarioSistema.perfil == PerfilUsuario.aluno)
            .limit(1)
        )
        aluno = result.scalar_one_or_none()
        
        if not aluno:
            print("❌ Nenhum aluno encontrado! Certifique-se de ter dados de usuários.")
            return
        
        print(f"👨‍🎓 Usando aluno: {aluno.nome}")
        
        # 2. Buscar paciente para testar
        result = await session.execute(
            select(Paciente)
            .where(Paciente.statusAtendimento.in_([
                "Triado - Aguardando Consulta", 
                "Disponível"
            ]))
            .limit(3)
        )
        pacientes = result.scalars().all()
        
        if not pacientes:
            print("❌ Nenhum paciente disponível! Execute primeiro o script de dados de triagem.")
            return
        
        print(f"👥 Encontrados {len(pacientes)} pacientes disponíveis")
        
        # 3. Testar verificação de horários disponíveis
        hoje = date.today()
        amanha = hoje + timedelta(days=1)
        
        # Ajustar para próximo dia útil se necessário
        while amanha.weekday() > 4:  # Sábado=5, Domingo=6
            amanha += timedelta(days=1)
        
        print(f"📅 Verificando horários disponíveis para {amanha.strftime('%d/%m/%Y')}")
        
        horarios_disponiveis = await AgendamentoService.obter_horarios_disponiveis(
            session, amanha, duracao_minutos=60
        )
        
        print(f"🕒 Horários disponíveis: {[h.strftime('%H:%M') for h in horarios_disponiveis[:5]]}...")
        
        if not horarios_disponiveis:
            print("❌ Nenhum horário disponível!")
            return
        
        # 4. Criar algumas consultas de teste
        consultas_criadas = []
        tipos_teste = [TipoConsulta.clinica_i, TipoConsulta.clinica_ii, TipoConsulta.retorno]
        
        for i, paciente in enumerate(pacientes[:3]):
            if i < len(horarios_disponiveis):
                try:
                    consulta = await AgendamentoService.criar_consulta(
                        session=session,
                        paciente_id=paciente.id,
                        aluno_id=aluno.id,
                        data_consulta=amanha,
                        hora_inicio=horarios_disponiveis[i],
                        tipo_consulta=tipos_teste[i % len(tipos_teste)],
                        duracao_minutos=60,
                        motivo_consulta=f"Consulta de teste {i+1}",
                        observacoes=f"Observações da consulta {i+1}",
                        criado_por=aluno.id
                    )
                    
                    consultas_criadas.append(consulta)
                    
                    print(f"✅ Consulta {i+1} criada:")
                    print(f"   📋 Paciente: {paciente.nome}")
                    print(f"   🕒 Horário: {consulta.hora_inicio.strftime('%H:%M')}")
                    print(f"   🏥 Tipo: {consulta.tipo_consulta.value}")
                    print(f"   ⚡ Status: {consulta.status.value}")
                    
                except Exception as e:
                    print(f"❌ Erro ao criar consulta {i+1}: {e}")
        
        # 5. Commit das mudanças
        await session.commit()
        
        # 6. Testar listagem de consultas do aluno
        print(f"\n📋 Listando consultas do aluno {aluno.nome}...")
        
        consultas_aluno = await AgendamentoService.listar_consultas_aluno(
            session=session,
            aluno_id=aluno.id,
            data_inicio=hoje,
            data_fim=amanha + timedelta(days=7)
        )
        
        print(f"📊 Total de consultas encontradas: {len(consultas_aluno)}")
        
        for consulta in consultas_aluno:
            # Buscar paciente
            result = await session.execute(
                select(Paciente).where(Paciente.id == consulta.paciente_id)
            )
            paciente = result.scalar_one_or_none()
            
            print(f"   • {consulta.data_consulta.strftime('%d/%m/%Y')} {consulta.hora_inicio.strftime('%H:%M')} - {paciente.nome if paciente else 'N/A'} - {consulta.status.value}")
        
        # 7. Testar reagendamento (se temos consultas)
        if consultas_criadas:
            print(f"\n🔄 Testando reagendamento...")
            consulta_teste = consultas_criadas[0]
            
            # Nova data (2 dias depois)
            nova_data = amanha + timedelta(days=2)
            while nova_data.weekday() > 4:  # Próximo dia útil
                nova_data += timedelta(days=1)
            
            # Verificar horários para nova data
            novos_horarios = await AgendamentoService.obter_horarios_disponiveis(
                session, nova_data, duracao_minutos=60
            )
            
            if novos_horarios:
                try:
                    nova_consulta = await AgendamentoService.reagendar_consulta(
                        session=session,
                        consulta_id=consulta_teste.id,
                        nova_data=nova_data,
                        novo_horario=novos_horarios[0],
                        usuario_id=aluno.id,
                        motivo_reagendamento="Teste de reagendamento"
                    )
                    
                    await session.commit()
                    
                    print(f"✅ Consulta reagendada:")
                    print(f"   📅 Nova data: {nova_data.strftime('%d/%m/%Y')}")
                    print(f"   🕒 Novo horário: {novos_horarios[0].strftime('%H:%M')}")
                    print(f"   📝 Nova consulta ID: {nova_consulta.id}")
                    
                except Exception as e:
                    print(f"❌ Erro no reagendamento: {e}")
            else:
                print("⚠️  Nenhum horário disponível para reagendamento")
    
    print("\n🎉 Teste do sistema de agendamento concluído!")
    print("💡 Agora você pode testar a interface visual!")


async def main():
    """Função principal"""
    try:
        await criar_dados_teste_agendamento()
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())