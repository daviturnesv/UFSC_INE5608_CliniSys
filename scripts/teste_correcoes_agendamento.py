#!/usr/bin/env python3
"""
Teste das correções do sistema de agendamento
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import date, time

async def teste_conversao_tipos():
    """Testa a conversão de tipos de consulta"""
    print("🧪 Testando conversão de tipos de consulta...")
    
    from src.backend.models.consulta import TipoConsulta
    
    # Mapear tipos como na interface
    tipo_map = {
        "Clínica I": "clinica_i",
        "Clínica II": "clinica_ii", 
        "Clínica III": "clinica_iii",
        "Triagem": "triagem",
        "Retorno": "retorno"
    }
    
    # Testar todas as conversões
    for display_name, enum_value in tipo_map.items():
        try:
            tipo_consulta = TipoConsulta(enum_value)
            print(f"   ✅ {display_name} -> {enum_value} -> {tipo_consulta}")
        except ValueError as e:
            print(f"   ❌ {display_name} -> {enum_value}: {e}")
    
    print()

async def teste_agendamento_service():
    """Testa o service de agendamento"""
    print("🏥 Testando AgendamentoService...")
    
    try:
        from src.backend.controllers.agendamento_service import AgendamentoService
        from src.backend.db.database import AsyncSessionLocal
        from src.backend.models.consulta import TipoConsulta, StatusConsulta
        from datetime import datetime
        
        async with AsyncSessionLocal() as session:
            # Testar listagem de consultas (sem filtros)
            consultas = await AgendamentoService.listar_consultas_aluno(
                session=session,
                aluno_id=1  # ID de exemplo
            )
            print(f"   ✅ Método listar_consultas_aluno funcionando")
            print(f"   📊 Encontradas {len(consultas)} consultas para aluno ID 1")
            
    except Exception as e:
        print(f"   ❌ Erro no AgendamentoService: {e}")
    
    print()

async def main():
    """Executa todos os testes"""
    print("=" * 60)
    print("🧪 TESTES: Correções do Sistema de Agendamento")
    print("=" * 60)
    
    await teste_conversao_tipos()
    await teste_agendamento_service()
    
    print("=" * 60)
    print("📋 RESUMO DAS CORREÇÕES IMPLEMENTADAS:")
    print("   1. ✅ Corrigida conversão de tipos de consulta")
    print("      - Removida conversão problemática com .lower().replace()")
    print("      - Implementado mapeamento explícito de tipos")
    print("   2. ✅ Corrigido erro 'Invalid column index id'") 
    print("      - Substituído set() por tags() na TreeView")
    print("      - IDs de consultas armazenados como tags")
    print("   3. ⚠️  Funcionalidades pendentes:")
    print("      - Detalhes de consulta (em desenvolvimento)")
    print("      - Reagendamento (em desenvolvimento)")
    print("      - Cancelamento (em desenvolvimento)")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())