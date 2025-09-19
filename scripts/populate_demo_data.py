#!/usr/bin/env python3
"""
Script para popular o banco de dados com dados de demonstração.
Execute: python scripts/populate_demo_data.py
"""
import sys
import os
import asyncio
from datetime import date, datetime
from pathlib import Path
from sqlalchemy import text

# Adicionar o diretório src ao path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))

from backend.db.database import AsyncSessionLocal
from backend.models import (
    UsuarioSistema, PerfilUsuario, PerfilProfessor, PerfilAluno, PerfilRecepcionista,
    Clinica, Paciente
)
try:
    from backend.models import FilaAtendimento, TipoAtendimento, StatusFila
    HAS_FILA = True
except ImportError:
    HAS_FILA = False
from backend.core.security import hash_password


async def create_clinicas(session):
    """Criar clínicas de demonstração"""
    clinicas_data = [
        {"codigo": "ODON001", "nome": "Clínica Odontológica Sorriso"},
        {"codigo": "ODON002", "nome": "Centro Odontológico Dente Perfeito"},
        {"codigo": "FISIO001", "nome": "Clínica de Fisioterapia Movimento"},
        {"codigo": "PSICO001", "nome": "Centro de Psicologia Bem-Estar"},
        {"codigo": "NUTRI001", "nome": "Clínica de Nutrição Vida Saudável"},
        {"codigo": "FONOAUD001", "nome": "Centro de Fonoaudiologia Som Claro"},
    ]
    
    clinicas_criadas = []
    for data in clinicas_data:
        clinica = Clinica(**data)
        session.add(clinica)
        clinicas_criadas.append(clinica)
    
    await session.commit()
    # Refresh para obter os IDs
    for clinica in clinicas_criadas:
        await session.refresh(clinica)
    
    print(f"✅ Criadas {len(clinicas_criadas)} clínicas")
    return clinicas_criadas


async def create_usuarios(session, clinicas):
    """Criar usuários de demonstração com diferentes perfis"""
    
    # Admin do sistema
    admin_user = UsuarioSistema(
        cpf="11111111111",
        nome="Administrador do Sistema",
        email="admin@clinisys.ufsc.br",
        senha_hash=hash_password("admin123"),
        perfil=PerfilUsuario.admin
    )
    session.add(admin_user)
    
    # Professores
    professores_data = [
        {
            "cpf": "22222222222",
            "nome": "João Silva",
            "email": "joao.silva@ufsc.br",
            "especialidade": "Ortodontia",
            "clinica_id": clinicas[0].id  # Clínica Odontológica
        },
        {
            "cpf": "33333333333",
            "nome": "Maria Santos",
            "email": "maria.santos@ufsc.br",
            "especialidade": "Endodontia",
            "clinica_id": clinicas[1].id  # Centro Odontológico
        },
        {
            "cpf": "44444444444",
            "nome": "Pedro Oliveira",
            "email": "pedro.oliveira@ufsc.br",
            "especialidade": "Fisioterapia Esportiva",
            "clinica_id": clinicas[2].id  # Fisioterapia
        },
        {
            "cpf": "55555555555",
            "nome": "Ana Costa",
            "email": "ana.costa@ufsc.br",
            "especialidade": "Psicologia Clínica",
            "clinica_id": clinicas[3].id  # Psicologia
        }
    ]
    
    for prof_data in professores_data:
        professor = UsuarioSistema(
            cpf=prof_data["cpf"],
            nome=prof_data["nome"],
            email=prof_data["email"],
            senha_hash=hash_password("prof123"),
            perfil=PerfilUsuario.professor
        )
        session.add(professor)
        await session.flush()  # Para obter o ID
        
        perfil_prof = PerfilProfessor(
            user_id=professor.id,
            especialidade=prof_data["especialidade"],
            clinica_id=prof_data["clinica_id"]
        )
        session.add(perfil_prof)
    
    # Alunos
    alunos_data = [
        {
            "cpf": "66666666666",
            "nome": "Carlos Estudante",
            "email": "carlos.estudante@grad.ufsc.br",
            "matricula": "20210001",
            "telefone": "(48) 99999-1111",
            "clinica_id": clinicas[0].id
        },
        {
            "cpf": "77777777777",
            "nome": "Fernanda Graduanda",
            "email": "fernanda.graduanda@grad.ufsc.br",
            "matricula": "20210002",
            "telefone": "(48) 99999-2222",
            "clinica_id": clinicas[0].id
        },
        {
            "cpf": "88888888888",
            "nome": "Lucas Acadêmico",
            "email": "lucas.academico@grad.ufsc.br",
            "matricula": "20210003",
            "telefone": "(48) 99999-3333",
            "clinica_id": clinicas[1].id
        },
        {
            "cpf": "99999999999",
            "nome": "Júlia Universitária",
            "email": "julia.universitaria@grad.ufsc.br",
            "matricula": "20210004",
            "telefone": "(48) 99999-4444",
            "clinica_id": clinicas[2].id
        },
        {
            "cpf": "10101010101",
            "nome": "Rafael Discente",
            "email": "rafael.discente@grad.ufsc.br",
            "matricula": "20210005",
            "telefone": "(48) 99999-5555",
            "clinica_id": clinicas[3].id
        },
        {
            "cpf": "12121212121",
            "nome": "Isabela Formanda",
            "email": "isabela.formanda@grad.ufsc.br",
            "matricula": "20210006",
            "telefone": "(48) 99999-6666",
            "clinica_id": clinicas[4].id
        }
    ]
    
    for aluno_data in alunos_data:
        aluno = UsuarioSistema(
            cpf=aluno_data["cpf"],
            nome=aluno_data["nome"],
            email=aluno_data["email"],
            senha_hash=hash_password("aluno123"),
            perfil=PerfilUsuario.aluno
        )
        session.add(aluno)
        await session.flush()
        
        perfil_aluno = PerfilAluno(
            user_id=aluno.id,
            matricula=aluno_data["matricula"],
            telefone=aluno_data["telefone"],
            clinica_id=aluno_data["clinica_id"]
        )
        session.add(perfil_aluno)
    
    # Recepcionistas
    recepcionistas_data = [
        {
            "cpf": "13131313131",
            "nome": "Carla Recepção",
            "email": "carla.recepcao@ufsc.br",
            "telefone": "(48) 99999-7777"
        },
        {
            "cpf": "14141414141",
            "nome": "Roberto Atendimento",
            "email": "roberto.atendimento@ufsc.br",
            "telefone": "(48) 99999-8888"
        }
    ]
    
    for recep_data in recepcionistas_data:
        recepcionista = UsuarioSistema(
            cpf=recep_data["cpf"],
            nome=recep_data["nome"],
            email=recep_data["email"],
            senha_hash=hash_password("recep123"),
            perfil=PerfilUsuario.recepcionista
        )
        session.add(recepcionista)
        await session.flush()
        
        perfil_recep = PerfilRecepcionista(
            user_id=recepcionista.id,
            telefone=recep_data["telefone"]
        )
        session.add(perfil_recep)
    
    await session.commit()
    print("✅ Criados usuários: 1 admin, 4 professores, 6 alunos, 2 recepcionistas")


async def create_pacientes(session):
    """Criar pacientes de demonstração"""
    pacientes_data = [
        {
            "nome": "João da Silva",
            "cpf": "10010010010",
            "dataNascimento": date(1985, 3, 15),
            "telefone": "(48) 3333-1111",
            "statusAtendimento": "Aguardando Triagem"
        },
        {
            "nome": "Maria Oliveira",
            "cpf": "20020020020",
            "dataNascimento": date(1992, 7, 22),
            "telefone": "(48) 3333-2222",
            "statusAtendimento": "Em Atendimento"
        },
        {
            "nome": "Pedro Santos",
            "cpf": "30030030030",
            "dataNascimento": date(1978, 11, 8),
            "telefone": "(48) 3333-3333",
            "statusAtendimento": "Aguardando Triagem"
        },
        {
            "nome": "Ana Costa",
            "cpf": "40040040040",
            "dataNascimento": date(1990, 5, 12),
            "telefone": "(48) 3333-4444",
            "statusAtendimento": "Finalizado"
        },
        {
            "nome": "Carlos Ferreira",
            "cpf": "50050050050",
            "dataNascimento": date(1988, 9, 30),
            "telefone": "(48) 3333-5555",
            "statusAtendimento": "Aguardando Triagem"
        },
        {
            "nome": "Lucia Pereira",
            "cpf": "60060060060",
            "dataNascimento": date(1995, 1, 18),
            "telefone": "(48) 3333-6666",
            "statusAtendimento": "Em Atendimento"
        },
        {
            "nome": "Roberto Lima",
            "cpf": "70070070070",
            "dataNascimento": date(1982, 4, 25),
            "telefone": "(48) 3333-7777",
            "statusAtendimento": "Aguardando Triagem"
        },
        {
            "nome": "Fernanda Souza",
            "cpf": "80080080080",
            "dataNascimento": date(1993, 12, 3),
            "telefone": "(48) 3333-8888",
            "statusAtendimento": "Aguardando Triagem"
        }
    ]
    
    for paciente_data in pacientes_data:
        paciente = Paciente(**paciente_data)
        session.add(paciente)
    
    await session.commit()
    print(f"✅ Criados {len(pacientes_data)} pacientes")


async def create_fila_atendimento(session):
    """Criar registros na fila de atendimento"""
    
    if not HAS_FILA:
        print("⚠️  Módulo de fila não disponível, pulando criação da fila")
        return
    
    # Buscar alguns pacientes para adicionar na fila
    result = await session.execute(
        text("SELECT id FROM pacientes WHERE statusAtendimento = 'Aguardando Triagem' LIMIT 4")
    )
    pacientes_ids = [row[0] for row in result.fetchall()]
    
    if not pacientes_ids:
        print("⚠️  Nenhum paciente encontrado para adicionar na fila")
        return
    
    fila_data = [
        {
            "paciente_id": pacientes_ids[0],
            "tipo": TipoAtendimento.consulta,
            "status": StatusFila.aguardando,
            "observacao": "Consulta de rotina"
        },
        {
            "paciente_id": pacientes_ids[1],
            "tipo": TipoAtendimento.triagem,
            "status": StatusFila.aguardando,
            "observacao": "Triagem inicial"
        },
        {
            "paciente_id": pacientes_ids[2] if len(pacientes_ids) > 2 else pacientes_ids[0],
            "tipo": TipoAtendimento.consulta,
            "status": StatusFila.aguardando,
            "observacao": "Consulta de acompanhamento"
        },
        {
            "paciente_id": pacientes_ids[3] if len(pacientes_ids) > 3 else pacientes_ids[1],
            "tipo": TipoAtendimento.consulta,
            "status": StatusFila.em_atendimento,
            "observacao": "Em atendimento no momento"
        }
    ]
    
    for fila_item in fila_data:
        fila = FilaAtendimento(**fila_item)
        session.add(fila)
    
    await session.commit()
    print(f"✅ Criados {len(fila_data)} registros na fila de atendimento")


async def clean_database(session):
    """Limpar dados existentes (opcional)"""
    print("🧹 Limpando dados existentes...")
    
    # Ordem de deleção respeitando foreign keys
    if HAS_FILA:
        await session.execute(text("DELETE FROM fila_atendimento"))
    await session.execute(text("DELETE FROM perfil_professor"))
    await session.execute(text("DELETE FROM perfil_aluno")) 
    await session.execute(text("DELETE FROM perfil_recepcionista"))
    await session.execute(text("DELETE FROM refresh_tokens"))
    await session.execute(text("DELETE FROM pacientes"))
    await session.execute(text("DELETE FROM usuarios"))
    await session.execute(text("DELETE FROM clinicas"))
    
    await session.commit()
    print("✅ Banco de dados limpo")


async def main():
    """Função principal do script"""
    print("🚀 Iniciando população do banco de dados...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Perguntar se deve limpar dados existentes
            response = input("Deseja limpar dados existentes? (s/N): ").lower().strip()
            if response in ['s', 'sim', 'y', 'yes']:
                await clean_database(session)
            
            # Criar dados de demonstração
            print("\n📋 Criando dados de demonstração...")
            
            # 1. Criar clínicas
            clinicas = await create_clinicas(session)
            
            # 2. Criar usuários
            await create_usuarios(session, clinicas)
            
            # 3. Criar pacientes
            await create_pacientes(session)
            
            # 4. Criar registros na fila (se disponível)
            if HAS_FILA:
                await create_fila_atendimento(session)
            
            print("\n🎉 População do banco concluída com sucesso!")
            print("\n📊 Resumo dos dados criados:")
            print("   • 6 clínicas de diferentes especialidades")
            print("   • 1 administrador (admin@clinisys.ufsc.br / admin123)")
            print("   • 4 professores (prof123)")
            print("   • 6 alunos (aluno123)")
            print("   • 2 recepcionistas (recep123)")
            print("   • 8 pacientes")
            if HAS_FILA:
                print("   • 4 registros na fila de atendimento")
            print("\n💡 Use as credenciais acima para testar diferentes perfis!")
            
        except Exception as e:
            print(f"❌ Erro durante a população: {e}")
            await session.rollback()
            raise
        

if __name__ == "__main__":
    asyncio.run(main())