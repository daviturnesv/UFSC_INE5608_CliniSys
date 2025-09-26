#!/usr/bin/env python3
"""
Verificação das correções aplicadas no agendamento_visual.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def verificar_correcoes():
    """Verifica se as correções foram aplicadas corretamente"""
    print("🔍 Verificando correções no arquivo agendamento_visual.py...")
    
    arquivo_path = "src/client_desktop/agendamento_visual.py"
    
    try:
        with open(arquivo_path, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Verificações das correções aplicadas
        verificacoes = [
            ("❌ run_async ainda presente", "def run_async(self, coro):" not in conteudo),
            ("✅ Threading em _buscar_pacientes", "threading.Thread(target=buscar_pacientes" in conteudo),
            ("✅ Loop isolado em _buscar_pacientes", "loop = asyncio.new_event_loop()" in conteudo),
            ("✅ Threading em _carregar_horarios_disponiveis", "def carregar_horarios():" in conteudo),
            ("✅ Threading em _carregar_minhas_consultas", "def carregar_consultas():" in conteudo),
            ("✅ Threading em _agendar_consulta", "def agendar():" in conteudo),
            ("❌ Chamadas run_async ainda presentes", "self.run_async(" not in conteudo),
        ]
        
        print("\n📋 Resultado das verificações:")
        todas_corretas = True
        
        for descricao, condicao in verificacoes:
            if condicao:
                print(f"   ✅ {descricao.replace('❌ ', '').replace('✅ ', '')}")
            else:
                print(f"   ❌ {descricao.replace('❌ ', '').replace('✅ ', '')}")
                todas_corretas = False
        
        # Contar quantas funções async ainda usam o padrão antigo
        funcoes_async = conteudo.count("async def _async_")
        print(f"\n📊 Estatísticas:")
        print(f"   - Funções async encontradas: {funcoes_async}")
        print(f"   - Threading patterns aplicados: {conteudo.count('threading.Thread(target=')}")
        print(f"   - Loops isolados criados: {conteudo.count('asyncio.new_event_loop()')}")
        
        return todas_corretas
        
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {arquivo_path}")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar: {e}")
        return False

def verificar_triagem():
    """Verifica se triagem_visual.py também precisa das mesmas correções"""
    print("\n🔍 Verificando triagem_visual.py...")
    
    try:
        with open("src/client_desktop/triagem_visual.py", 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        if "self.run_async(" in conteudo:
            print("   ⚠️  triagem_visual.py ainda usa self.run_async() - pode precisar de correção")
        else:
            print("   ✅ triagem_visual.py não usa self.run_async()")
            
        if "def run_async(self, coro):" in conteudo:
            print("   ⚠️  Método run_async ainda presente em triagem_visual.py")
        else:
            print("   ✅ Método run_async não encontrado em triagem_visual.py")
            
    except FileNotFoundError:
        print("   ℹ️  Arquivo triagem_visual.py não encontrado")
    except Exception as e:
        print(f"   ❌ Erro ao verificar triagem: {e}")

def main():
    """Executa as verificações"""
    print("=" * 65)
    print("VERIFICAÇÃO: Correções Anti-Travamento CliniSys")
    print("=" * 65)
    
    sucesso_agendamento = verificar_correcoes()
    verificar_triagem()
    
    print("\n" + "=" * 65)
    if sucesso_agendamento:
        print("🎉 RESULTADO: Todas as correções foram aplicadas corretamente!")
        print("\n📝 Resumo das correções:")
        print("   1. Removido método run_async() obsoleto")
        print("   2. Implementado threading com loops asyncio isolados")
        print("   3. Cada operação async agora roda em thread separada")
        print("   4. UI Tkinter não deveria mais travar")
        print("\n✅ O problema de travamento na seleção de pacientes deve estar resolvido!")
    else:
        print("⚠️  RESULTADO: Algumas correções podem estar incompletas")
    print("=" * 65)

if __name__ == "__main__":
    main()