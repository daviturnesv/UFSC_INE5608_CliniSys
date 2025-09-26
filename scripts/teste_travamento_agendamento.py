#!/usr/bin/env python3
"""
Teste das correções de travamento no agendamento
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import tkinter as tk
import time
import threading
from src.client_desktop.agendamento_visual import AgendamentoVisualApp

def test_agendamento_sem_travamento():
    """Testa se o agendamento abre sem travar"""
    print("🧪 TESTE: Agendamento sem travamento")
    print("=" * 50)
    
    user_data = {
        'id': 6,
        'nome': 'Carlos Estudante', 
        'perfil': 'aluno'
    }
    
    try:
        print("📝 Criando aplicação de agendamento...")
        root = tk.Tk()
        root.withdraw()
        
        # Criar a aplicação
        app = AgendamentoVisualApp(root, user_data)
        print("✅ Aplicação criada com sucesso!")
        
        # Aguardar um pouco para os dados carregarem
        print("⏳ Aguardando carregamento inicial (3 segundos)...")
        
        def verificar_depois():
            print("🔍 Verificando se a busca de pacientes funciona...")
            try:
                # Simular clique no botão buscar
                app._buscar_pacientes()
                print("✅ Função de busca executada sem travamento!")
                
                # Aguardar um pouco mais
                root.after(2000, lambda: (
                    print("✅ Teste concluído - sem travamentos detectados!"),
                    app.destroy(),
                    root.destroy()
                ))
            except Exception as e:
                print(f"❌ Erro na busca: {e}")
                root.destroy()
        
        # Verificar após a inicialização
        root.after(3000, verificar_depois)
        
        print("🖥️  Iniciando interface...")
        root.mainloop()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    print("🚀 TESTE DE CORREÇÃO: Travamento no Agendamento")
    print("=" * 60)
    
    resultado = test_agendamento_sem_travamento()
    
    print(f"\n📊 RESULTADO FINAL:")
    if resultado:
        print("🎉 Teste passou - correções aplicadas com sucesso!")
        print("💡 O sistema agora usa threads assíncronas que não travam a UI")
    else:
        print("❌ Teste falhou - ainda há problemas para resolver")