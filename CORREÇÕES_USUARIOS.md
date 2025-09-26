# Correções no Sistema de Gerenciamento de Usuários

## 🚀 Problemas Identificados e Corrigidos

### 1. 🔑 **Erro ao alterar senha relacionado à clínica**
**Problema:** Usuários do tipo "aluno" ou "professor" sem clínica associada geravam erro ao tentar alterar senha.

**Causa:** A validação de clínica não estava sendo verificada adequadamente na função `change_password`.

**Correção Implementada:**
```python
# Em change_password()
if u.perfil in (PerfilUsuario.professor, PerfilUsuario.aluno):
    # Verificar se existe o perfil específico com clínica
    if u.perfil == PerfilUsuario.professor:
        res = await session.execute(select(PerfilProfessor).where(PerfilProfessor.user_id == user_id))
        prof = res.scalar_one_or_none()
        if not prof or not prof.clinica_id:
            raise ValueError(f"Usuário {u.perfil.value} deve ter uma clínica associada")
```

**Validação Adicional na UI:**
```python
# Em cmd_alterar_senha()
if user_data and user_data.get('perfil') in ('aluno', 'professor'):
    if not user_data.get('clinica_id'):
        messagebox.showerror(
            "Erro de dados", 
            f"Usuário {user_data.get('perfil')} deve ter uma clínica associada.\n"
            "Por favor, corrija os dados do usuário primeiro."
        )
        return
```

### 2. 📝 **Campos específicos não eram atualizados ao mudar perfil**
**Problema:** Ao alterar o tipo de usuário, campos específicos como `matricula`, `telefone_academico`, etc. não eram atualizados no banco.

**Causa:** A função `update_user` não tinha parâmetros para campos específicos dos perfis.

**Correção Implementada:**
```python
# Nova assinatura da função update_user
async def update_user(
    user_id: int,
    nome: Optional[str] = None,
    email: Optional[str] = None,
    cpf: Optional[str] = None,
    perfil: Optional[str] = None,
    clinica_id: Optional[int] = None,
    matricula: Optional[str] = None,           # ✅ NOVO
    telefone_academico: Optional[str] = None,  # ✅ NOVO
) -> None:
```

**Atualização de Perfis Específicos:**
```python
# Para alunos
if not alu:
    alu = PerfilAluno(user_id=user_id, clinica_id=clinica_id, matricula=matricula, telefone=telefone_academico)
    session.add(alu)
else:
    if clinica_id is not None:
        alu.clinica_id = clinica_id
    if matricula is not None:
        alu.matricula = matricula  # ✅ ATUALIZA MATRÍCULA
    if telefone_academico is not None:
        alu.telefone = telefone_academico  # ✅ ATUALIZA TELEFONE
```

### 3. 🎯 **UI não coletava campos específicos dos perfis**
**Problema:** A interface não estava coletando os valores dos campos específicos ao salvar alterações.

**Correção Implementada:**
```python
# Em cmd_atualizar() - Coleta de campos específicos
matricula = None
telefone_academico = None

if perfil == 'aluno' and 'aluno' in self.profile_fields:
    matricula = self.profile_fields['aluno']['matricula_var'].get().strip() or None
    telefone_academico = self.profile_fields['aluno']['telefone_var'].get().strip() or None
elif perfil == 'professor' and 'professor' in self.profile_fields:
    telefone_academico = self.profile_fields['professor']['telefone_var'].get().strip() or None

# Chamada atualizada
self.run_async(update_user(
    uid, 
    nome=nome, 
    email=email, 
    cpf=cpf, 
    perfil=perfil, 
    clinica_id=clinica_id,
    matricula=matricula,           # ✅ PASSA MATRÍCULA
    telefone_academico=telefone_academico  # ✅ PASSA TELEFONE
))
```

### 4. 🧹 **Limpeza automática de campos ao mudar perfil**
**Problema:** Ao alterar o tipo de usuário, campos do perfil anterior permaneciam visíveis.

**Correção Implementada:**
```python
def _clear_profile_fields_except(self, keep_perfil):
    """Limpa os campos específicos dos perfis que não são o atual"""
    for profile_type, fields in self.profile_fields.items():
        if profile_type != keep_perfil:
            # Limpar os valores dos campos
            for field_name, widget in fields.items():
                if 'var' in field_name and hasattr(widget, 'set'):
                    widget.set("")

def _show_profile_fields(self, perfil):
    # ... código existente ...
    # Limpar campos que não pertencem ao perfil atual
    self._clear_profile_fields_except(perfil)  # ✅ LIMPA CAMPOS
```

### 5. 📊 **Melhor carregamento de dados do perfil**
**Problema:** A função `list_users` não carregava adequadamente os dados específicos dos perfis.

**Correção Implementada:**
```python
# Em list_users() - Carregamento aprimorado
try:
    pd = await svc_get_profile_data(session, u)
    if pd and isinstance(pd, dict):
        d["profile_data"] = pd
        # ... extração de clinica_id ...
    elif pd and hasattr(pd, 'clinica_id'):
        d["clinica_id"] = pd.clinica_id
        # Converter objeto para dict
        profile_dict = {}
        if hasattr(pd, 'matricula'):
            profile_dict['matricula'] = pd.matricula  # ✅ CARREGA MATRÍCULA
        if hasattr(pd, 'telefone'):
            profile_dict['telefone'] = pd.telefone    # ✅ CARREGA TELEFONE
        # ... outros campos ...
        d["profile_data"] = profile_dict
except Exception as e:
    print(f"Erro ao carregar dados do perfil para usuário {u.id}: {e}")
    d["profile_data"] = {}
```

## 🧪 Testes de Validação

✅ **Teste 1:** Alteração de senha para aluno com clínica associada - **SUCESSO**
✅ **Teste 2:** Mudança de perfil com atualização de campos específicos - **SUCESSO** 
✅ **Teste 3:** Limpeza automática ao mudar tipo de usuário - **SUCESSO**
✅ **Teste 4:** Carregamento correto de dados específicos dos perfis - **SUCESSO**

## 📈 Benefícios das Correções

1. **Consistência de Dados**: Garantia de que usuários aluno/professor sempre têm clínica associada
2. **Integridade do Sistema**: Campos específicos são corretamente atualizados e validados
3. **Experiência do Usuário**: Interface mais limpa e clara ao trocar perfis
4. **Robustez**: Melhor tratamento de erros e validações
5. **Manutenibilidade**: Código mais organizado e fácil de manter

## 🔧 Arquivos Modificados

- `src/client_desktop/uc_admin_users_tk.py` - **Principal arquivo com todas as correções**
- `scripts/teste_correcoes_usuarios.py` - **Script de teste para validação**

## 🎯 Status Final

**TODAS AS CORREÇÕES IMPLEMENTADAS E TESTADAS COM SUCESSO** ✅

O sistema agora:
- ✅ Valida clínica antes de alterar senhas
- ✅ Atualiza corretamente campos específicos dos perfis
- ✅ Limpa automaticamente campos ao trocar perfis
- ✅ Carrega adequadamente dados específicos dos perfis
- ✅ Previne inconsistências de dados