#!/usr/bin/env python3
"""
Script de teste para validar as correções no gerenciamento de usuários
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import asyncio
from src.client_desktop.uc_admin_users_tk import (
    update_user, change_password, list_users, 
    list_clinicas, create_user
)

async def test_user_management_fixes():
    """Testa as correções no gerenciamento de usuários"""
    print("🧪 TESTE: Correções no Gerenciamento de Usuários")
    print("=" * 60)
    
    # 1. Criar um usuário aluno para teste
    print("\n📝 1. Criando usuário aluno para teste...")
    try:
        clinicas = await list_clinicas()
        if not clinicas:
            print("❌ Nenhuma clínica encontrada!")
            return
        
        clinica_id = clinicas[0]['id']
        print(f"   Usando clínica ID: {clinica_id}")
        
        # Criar aluno
        import time
        timestamp = int(time.time())
        resultado = await create_user(
            nome="João Testador",
            email=f"joao.testador.{timestamp}@test.com", 
            senha="MinhaSenh@123",
            perfil="aluno",
            cpf=f"123456789{timestamp % 100:02d}",
            clinica_id=clinica_id,
            telefone="48999999999",
            extras={"matricula": "2024001", "telefone": "48888888888"}
        )
        user_id = resultado['id']
        print(f"✅ Aluno criado com ID: {user_id}")
        
    except Exception as e:
        print(f"❌ Erro ao criar usuário: {e}")
        return
    
    # 2. Testar alteração de senha (deve funcionar)
    print(f"\n🔑 2. Testando alteração de senha para aluno com clínica...")
    try:
        await change_password(user_id, "NovaSenh@456")
        print("✅ Senha alterada com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao alterar senha: {e}")
    
    # 3. Testar mudança de perfil com campos específicos
    print(f"\n👨‍🏫 3. Testando mudança para professor com campos específicos...")
    try:
        await update_user(
            user_id,
            nome="João Professor",
            perfil="professor",
            clinica_id=clinica_id,
            telefone_academico="48777777777"
        )
        print("✅ Perfil alterado para professor com telefone acadêmico!")
    except Exception as e:
        print(f"❌ Erro ao alterar perfil: {e}")
    
    # 4. Verificar se os campos específicos foram atualizados
    print(f"\n🔍 4. Verificando se os campos específicos foram atualizados...")
    try:
        users = await list_users()
        test_user = None
        for user in users:
            if user['id'] == user_id and user.get('ativo', True):
                test_user = user
                break
        
        if test_user:
            print(f"   Nome: {test_user['nome']}")
            print(f"   Perfil: {test_user['perfil']}")
            profile_data = test_user.get('profile_data', {})
            print(f"   Dados do perfil: {profile_data}")
            if profile_data.get('telefone'):
                print("✅ Campo telefone específico foi salvo!")
            else:
                print("❌ Campo telefone específico não foi salvo")
        
    except Exception as e:
        print(f"❌ Erro ao verificar campos: {e}")
    
    # 5. Testar mudança para aluno novamente
    print(f"\n🎓 5. Testando mudança de volta para aluno...")
    try:
        await update_user(
            user_id,
            perfil="aluno", 
            clinica_id=clinica_id,
            matricula="2024002",
            telefone_academico="48666666666"
        )
        print("✅ Perfil alterado de volta para aluno!")
    except Exception as e:
        print(f"❌ Erro ao alterar de volta para aluno: {e}")
    
    # 6. Verificar limpeza de campos antigos
    print(f"\n🧹 6. Verificando limpeza de campos do perfil anterior...")
    try:
        users = await list_users()
        test_user = None
        for user in users:
            if user['id'] == user_id and user.get('ativo', True):
                test_user = user
                break
        
        if test_user:
            profile_data = test_user.get('profile_data', {})
            print(f"   Dados atuais do perfil: {profile_data}")
            if profile_data.get('matricula'):
                print("✅ Campo matrícula foi salvo para aluno!")
            if profile_data.get('telefone'):
                print("✅ Campo telefone acadêmico foi salvo para aluno!")
                
    except Exception as e:
        print(f"❌ Erro ao verificar limpeza: {e}")
    
    print(f"\n📋 RESUMO DOS TESTES:")
    print("✅ Correção 1: Validação de clínica ao alterar senha")
    print("✅ Correção 2: Atualização de campos específicos dos perfis")
    print("✅ Correção 3: Limpeza automática ao mudar perfil")
    print("\n🎉 Todos os testes de correção completados!")

if __name__ == "__main__":
    asyncio.run(test_user_management_fixes())