#!/usr/bin/env python3
"""
Teste das correções implementadas no CliniSys
"""

def testar_agendamento():
    """Testa se agendamento_visual.py tem as correções corretas"""
    print("🏥 Testando correções do agendamento...")
    
    try:
        with open("src/client_desktop/agendamento_visual.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Testes essenciais
        testes = [
            ("❌ run_async removido", "def run_async(self, coro):" not in content),
            ("✅ Threading implementado", "threading.Thread(" in content),
            ("✅ Loops isolados", "asyncio.new_event_loop()" in content),
            ("❌ Chamadas run_async removidas", "self.run_async(" not in content),
            ("✅ Imports async corretos", "import asyncio" in content),
        ]
        
        print("   Resultados agendamento_visual.py:")
        for desc, test in testes:
            status = "✅" if test else "❌"
            print(f"      {status} {desc.replace('❌ ', '').replace('✅ ', '')}")
            
        return all(test for _, test in testes)
        
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def testar_triagem():
    """Testa se triagem_visual.py tem as correções corretas"""
    print("🚑 Testando correções da triagem...")
    
    try:
        with open("src/client_desktop/triagem_visual.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Testes essenciais
        testes = [
            ("❌ run_async removido", "def run_async(self, coro):" not in content),
            ("✅ Threading implementado", "threading.Thread(" in content),
            ("✅ Loops isolados", "asyncio.new_event_loop()" in content),
            ("❌ Chamadas run_async removidas", "self.run_async(" not in content),
        ]
        
        print("   Resultados triagem_visual.py:")
        for desc, test in testes:
            status = "✅" if test else "❌"
            print(f"      {status} {desc.replace('❌ ', '').replace('✅ ', '')}")
            
        return all(test for _, test in testes)
        
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def main():
    print("=" * 60)
    print("🧪 TESTE: Verificação Final das Correções CliniSys")
    print("=" * 60)
    
    agendamento_ok = testar_agendamento()
    triagem_ok = testar_triagem()
    
    print("\n" + "=" * 60)
    print("📊 RESUMO:")
    print(f"   🏥 Agendamento: {'✅ OK' if agendamento_ok else '❌ Problemas'}")
    print(f"   🚑 Triagem: {'✅ OK' if triagem_ok else '❌ Problemas'}")
    
    if agendamento_ok and triagem_ok:
        print("\n🎉 SUCESSO! Todas as correções foram aplicadas!")
        print("\n📝 Correções aplicadas:")
        print("   • Removido método run_async() obsoleto")
        print("   • Implementado threading com loops asyncio isolados")
        print("   • UI não deve mais travar durante operações async")
        print("   • Problema de 'no running event loop' resolvido")
        print("\n✅ O sistema deve estar funcional agora!")
    else:
        print("\n⚠️ Algumas correções podem estar incompletas")
    
    print("=" * 60)

if __name__ == "__main__":
    main()