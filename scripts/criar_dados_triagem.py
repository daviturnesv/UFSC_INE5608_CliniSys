"""
Script para criar dados de teste para o sistema de triagem
"""
import asyncio
import sys
from pathlib import Path
from datetime import date, datetime, timezone

# Adicionar o projeto ao path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.backend.db.database import AsyncSessionLocal
from src.backend.models.paciente import Paciente
from src.backend.models.triagem import RegistroTriagem, PrioridadeTriagem, SituacaoTriagem
from src.backend.controllers.triagem_service import criar_registro_triagem
from sqlalchemy import select


async def criar_dados_teste_triagem():
    """Cria dados de teste específicos para triagem"""
    
    async with AsyncSessionLocal() as session:
        
        # Verificar se já existem pacientes
        result = await session.execute(select(Paciente))
        pacientes_existentes = result.scalars().all()
        
        print(f"🔍 Encontrados {len(pacientes_existentes)} pacientes existentes")
        
        if len(pacientes_existentes) < 3:
            print("📝 Criando pacientes adicionais para teste de triagem...")
            
            # Pacientes específicos para triagem
            novos_pacientes = [
                {
                    "nome": "Ana Silva Urgente",
                    "cpf": "99988877766",
                    "dataNascimento": date(1980, 5, 15),
                    "telefone": "(48) 99999-9999",
                    "statusAtendimento": "Aguardando Triagem"
                },
                {
                    "nome": "Pedro Costa Emergência",
                    "cpf": "88877766655",
                    "dataNascimento": date(1995, 8, 20),
                    "telefone": "(48) 88888-8888", 
                    "statusAtendimento": "Aguardando Triagem"
                },
                {
                    "nome": "Maria Oliveira Normal",
                    "cpf": "77766655544",
                    "dataNascimento": date(1970, 12, 3),
                    "telefone": "(48) 77777-7777",
                    "statusAtendimento": "Aguardando Triagem"
                }
            ]
            
            for dados in novos_pacientes:
                paciente = Paciente(**dados)
                session.add(paciente)
                
            await session.commit()
            print("✅ Pacientes criados para teste de triagem")
        
        # Buscar pacientes para criar registros de triagem
        result = await session.execute(
            select(Paciente).where(Paciente.statusAtendimento == "Aguardando Triagem").limit(5)
        )
        pacientes_triagem = result.scalars().all()
        
        print(f"🎯 Criando registros de triagem para {len(pacientes_triagem)} pacientes...")
        
        # Criar alguns registros de triagem em diferentes estados
        for i, paciente in enumerate(pacientes_triagem):
            
            # Verificar se já tem registro de triagem
            result = await session.execute(
                select(RegistroTriagem).where(RegistroTriagem.paciente_id == paciente.id)
            )
            
            if result.scalar_one_or_none():
                continue  # Já tem registro
            
            registro = await criar_registro_triagem(session, paciente.id)
            
            # Configurar diferentes situações para teste
            if i == 0:  # Primeiro - aguardando
                registro.situacao = SituacaoTriagem.AGUARDANDO
            elif i == 1:  # Segundo - em andamento
                registro.situacao = SituacaoTriagem.EM_ANDAMENTO
                registro.aluno_id = 1  # Assumindo que existe um usuário com ID 1
                registro.triagem_iniciada_em = datetime.now(timezone.utc)
            elif i == 2:  # Terceiro - concluído com alta prioridade
                registro.situacao = SituacaoTriagem.CONCLUIDA
                registro.prioridade = PrioridadeTriagem.EMERGENCIA
                registro.queixa_principal = "Dor torácica intensa"
                registro.necessidades_identificadas = "Avaliação cardiológica urgente"
                registro.triagem_concluida_em = datetime.now(timezone.utc)
                # Atualizar status do paciente
                paciente.statusAtendimento = "Triado - Aguardando Consulta"
            elif i == 3:  # Quarto - prioridade média
                registro.situacao = SituacaoTriagem.CONCLUIDA
                registro.prioridade = PrioridadeTriagem.URGENTE
                registro.queixa_principal = "Dor de cabeça persistente há 3 dias"
                registro.necessidades_identificadas = "Consulta neurológica"
                registro.triagem_concluida_em = datetime.now(timezone.utc)
                paciente.statusAtendimento = "Triado - Aguardando Consulta"
            elif i == 4:  # Quinto - baixa prioridade
                registro.situacao = SituacaoTriagem.CONCLUIDA
                registro.prioridade = PrioridadeTriagem.POUCO_URGENTE
                registro.queixa_principal = "Consulta de rotina para check-up"
                registro.necessidades_identificadas = "Avaliação geral"
                registro.triagem_concluida_em = datetime.now(timezone.utc)
                paciente.statusAtendimento = "Triado - Aguardando Consulta"
            
            await session.commit()
        
        print("✅ Registros de triagem criados com sucesso!")
        
        # Mostrar estatísticas
        aguardando = await session.execute(
            select(RegistroTriagem).where(RegistroTriagem.situacao == SituacaoTriagem.AGUARDANDO)
        )
        em_andamento = await session.execute(
            select(RegistroTriagem).where(RegistroTriagem.situacao == SituacaoTriagem.EM_ANDAMENTO)
        )
        concluidos = await session.execute(
            select(RegistroTriagem).where(RegistroTriagem.situacao == SituacaoTriagem.CONCLUIDA)
        )
        
        print("\n📊 Estatísticas criadas:")
        print(f"   • Aguardando triagem: {len(aguardando.scalars().all())}")
        print(f"   • Em andamento: {len(em_andamento.scalars().all())}")
        print(f"   • Concluídos: {len(concluidos.scalars().all())}")
        
        print("\n🎉 Dados de teste para triagem criados com sucesso!")
        print("💡 Agora você pode testar o sistema de triagem visual!")


if __name__ == "__main__":
    asyncio.run(criar_dados_teste_triagem())