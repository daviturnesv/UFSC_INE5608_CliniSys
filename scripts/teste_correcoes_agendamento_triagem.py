#!/usr/bin/env python3
"""
Script de teste para validar as correções no sistema de agendamento e triagem
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import asyncio
import tkinter as tk
from src.client_desktop.agendamento_visual import abrir_agendamento_consultas
from src.client_desktop.triagem_visual import abrir_triagem_visual

def test_agendamento():
    """Testa abertura do sistema de agendamento"""
    print("🧪 TESTE: Sistema de Agendamento")
    print("=" * 50)
    
    # Dados de usuário teste
    user_data = {
        'id': 6,  # ID de um aluno
        'nome': 'Carlos Estudante',
        'perfil': 'aluno'
    }
    
    try:
        # Criar janela root oculta
        root = tk.Tk()
        root.withdraw()
        
        print("📝 Tentando abrir sistema de agendamento...")
        app = abrir_agendamento_consultas(None, user_data)
        
        if app:
            print("✅ Sistema de agendamento aberto com sucesso!")
            print(f"   Usuário: {user_data['nome']} ({user_data['perfil']})")
            
            # Mostrar janela por alguns segundos para teste visual
            app.deiconify()
            root.after(3000, lambda: (app.destroy(), root.destroy()))  # Fechar após 3s
            root.mainloop()
            
            return True
        else:
            print("❌ Erro ao abrir sistema de agendamento")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de agendamento: {e}")
        return False

def test_triagem():
    """Testa abertura do sistema de triagem"""
    print("\n🧪 TESTE: Sistema de Triagem")
    print("=" * 50)
    
    # Dados de usuário teste
    user_data = {
        'id': 14,  # ID de admin
        'nome': 'Administrador',
        'perfil': 'admin'
    }
    
    try:
        # Criar janela root oculta
        root = tk.Tk()
        root.withdraw()
        
        print("📝 Tentando abrir sistema de triagem...")
        app = abrir_triagem_visual(None, user_data)
        
        if app:
            print("✅ Sistema de triagem aberto com sucesso!")
            print(f"   Usuário: {user_data['nome']} ({user_data['perfil']})")
            
            # Mostrar janela por alguns segundos para teste visual
            app.deiconify()
            root.after(3000, lambda: (app.destroy(), root.destroy()))  # Fechar após 3s
            root.mainloop()
            
            return True
        else:
            print("❌ Erro ao abrir sistema de triagem")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de triagem: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🚀 TESTE DE CORREÇÕES: Agendamento e Triagem")
    print("=" * 60)
    
    resultados = []
    
    # Teste 1: Sistema de Agendamento
    resultado_agendamento = test_agendamento()
    resultados.append(("Sistema de Agendamento", resultado_agendamento))
    
    # Teste 2: Sistema de Triagem
    resultado_triagem = test_triagem()
    resultados.append(("Sistema de Triagem", resultado_triagem))
    
    # Resumo dos resultados
    print(f"\n📊 RESUMO DOS TESTES:")
    print("=" * 50)
    
    sucesso = 0
    for nome, resultado in resultados:
        status = "✅ SUCESSO" if resultado else "❌ FALHA"
        print(f"{nome:25} {status}")
        if resultado:
            sucesso += 1
    
    print(f"\n🎯 RESULTADO FINAL: {sucesso}/{len(resultados)} testes passaram")
    
    if sucesso == len(resultados):
        print("🎉 Todos os problemas foram corrigidos com sucesso!")
    else:
        print("⚠️  Alguns problemas ainda precisam ser investigados.")

if __name__ == "__main__":
    main()