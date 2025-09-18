# CliniSys-Escola

Sistema de Gestão Desktop para a Clínica-Escola de Odontologia da UFSC.

Projeto acadêmico desenvolvido para a disciplina **INE5608 - Análise e Projeto de Sistemas** (UFSC).

---

## Índice

1. [Visão Geral](#visão-geral)
2. [Funcionalidades Implementadas](#funcionalidades-implementadas)
3. [Arquitetura e Stack](#arquitetura-e-stack)
4. [Estrutura do Repositório](#estrutura-do-repositório)
5. [Configuração e Execução](#configuração-e-execução)
6. [Autenticação e Segurança](#autenticação-e-segurança)
7. [Testes](#testes)
8. [Atualizações Recentes](#atualizações-recentes)
9. [Autores](#autores)

---

## Visão Geral

O **CliniSys-Escola** centraliza dados acadêmicos e clínicos, substituindo planilhas e prontuários físicos, reduzindo inconsistências e melhorando a rastreabilidade e acesso ao histórico dos pacientes.

Principais objetivos:

* Unificar informações acadêmicas e clínicas.
* Oferecer controle de acesso por perfil.
* Fornecer prontuário eletrônico estruturado.
* Apoiar supervisão docente sobre atendimentos.

---

## Funcionalidades Implementadas

### Sistema Desktop Completo

**🔐 Autenticação e Segurança:**
* Sistema de login com interface Tkinter
* Autenticação via JWT (access tokens) + refresh tokens
* Política de senha segura (>=8 caracteres, letra + dígito)
* Logout com revogação de tokens
* Controle de acesso por perfis (admin, professor, recepcionista, aluno)

**👥 Gerenciamento de Usuários:**
* CRUD completo de usuários (criar, listar, editar, desativar)
* Interface gráfica para administração de usuários
* Perfis diferenciados com permissões específicas
* Ativação/desativação de contas

**👨‍⚕️ Gerenciamento de Pacientes:**
* CRUD completo de pacientes com interface Tkinter
* Busca avançada por nome e CPF
* Validação de dados (CPF único, campos obrigatórios)
* Controle de status de atendimento

**📊 Sistema de Banco de Dados:**
* SQLite integrado para persistência
* Migrações automáticas com Alembic
* Campos de auditoria (created_at/updated_at)
* Integridade referencial

---

## Arquitetura e Stack

**Aplicação Desktop 100% Local** com arquitetura MVC moderna e interface nativa Python.

| Componente | Tecnologia | Justificativa |
|-----------|------------|---------------|
| **Interface** | Tkinter | Interface nativa Python, distribuição simples, sem dependências externas |
| **Backend MVC** | SQLAlchemy + Pydantic | ORM robusto, validação de dados, separação clara de responsabilidades |
| **Banco de Dados** | SQLite + aiosqlite | Banco embarcado, operações assíncronas, zero configuração |
| **Autenticação** | bcrypt + python-jose | Hashing seguro de senhas e tokens JWT padrão industria |
| **Validação** | Pydantic | Validação automática de dados, serialização type-safe |
| **Estrutura** | MVC Pattern | Models (SQLAlchemy), Views (Pydantic), Controllers (business logic) |

### Vantagens da Arquitetura Escolhida

* **📦 Distribuição Simples**: Executável único, sem necessidade de servidor
* **🔒 Segurança**: Dados ficam na máquina local, controle total do ambiente
* **⚡ Performance**: Sem latência de rede, acesso direto ao banco
* **🛠️ Manutenção**: Atualizações simples, sem infraestrutura complexa
* **💻 Compatibilidade**: Funciona em Windows, Linux e macOS

---

## Estrutura do Repositório

```text
CliniSys-Escola/
├── src/
│   ├── backend/                 # 🏗️ Backend MVC
│   │   ├── models/             # 📊 Modelos de dados (SQLAlchemy)
│   │   │   ├── usuario.py      # Modelo de usuários
│   │   │   ├── paciente.py     # Modelo de pacientes
│   │   │   ├── clinica.py      # Modelo de clínica
│   │   │   └── ...
│   │   ├── views/              # 📋 Schemas de validação (Pydantic)
│   │   │   ├── usuario_view.py # Schemas de usuários
│   │   │   ├── paciente_view.py # Schemas de pacientes
│   │   │   └── ...
│   │   ├── controllers/        # 🎮 Lógica de negócio
│   │   │   ├── usuario_service.py
│   │   │   ├── paciente_service.py
│   │   │   └── ...
│   │   ├── core/              # ⚙️ Configurações e segurança
│   │   │   ├── config.py      # Configurações da aplicação
│   │   │   ├── security.py    # Autenticação e criptografia
│   │   │   └── ...
│   │   └── db/                # 💾 Conexão com banco
│   │       └── database.py    # Setup SQLAlchemy + SQLite
│   │
│   └── client_desktop/         # 🖥️ Interface Desktop (Tkinter)
│       ├── __main__.py        # 🚀 Ponto de entrada da aplicação
│       ├── clinisys_main.py   # 📱 Aplicação principal
│       ├── login_tk.py        # 🔐 Tela de login
│       ├── uc_admin_users_tk.py # 👥 Gestão de usuários
│       └── pacientes_tk.py    # 👨‍⚕️ Gestão de pacientes
│
├── tests/                      # 🧪 Testes automatizados
│   ├── test_auth.py           # Testes de autenticação
│   ├── test_usuarios.py       # Testes de usuários
│   └── test_pacientes.py      # Testes de pacientes
│
├── alembic/                   # 📦 Migrações de banco
├── Documentação/              # 📚 Documentação do projeto
├── requirements.txt           # 📋 Dependências Python
├── alembic.ini               # ⚙️ Configuração do Alembic
└── README.md                 # 📖 Este arquivo
```

---

## Configuração e Execução

### ⚡ Início Rápido

```bash
# Clonar o repositório
git clone https://github.com/daviturnesv/UFSC_INE5608_CliniSys.git
cd UFSC_INE5608_CliniSys

# Criar ambiente virtual
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS

# Instalar dependências
pip install -r requirements.txt

# Configurar banco de dados
alembic upgrade head

# Criar usuário administrador
python -m src.backend.cli seed-admin

# Executar aplicação desktop
python -m src.client_desktop
```

A aplicação será aberta com a tela de login. Use as credenciais padrão:
- **Email:** admin@exemplo.com  
- **Senha:** admin123

### 📋 Pré-requisitos

- Python 3.12 ou superior
- Git
- Sistema operacional: Windows, Linux ou macOS

### 🛠️ Configuração Detalhada

#### Ambiente e Dependências

```bash
# Clonar repositório
git clone https://github.com/daviturnesv/UFSC_INE5608_CliniSys.git
cd UFSC_INE5608_CliniSys

# Criar ambiente virtual (Python 3.12+)
python -m venv .venv

# Ativar ambiente virtual
# Windows PowerShell:
.\.venv\Scripts\activate
# Windows CMD:
.venv\Scripts\activate.bat
# Linux/macOS:
source .venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt
```

#### 📊 Configuração do Banco de Dados

O CliniSys usa SQLite como banco de dados padrão - **não requer configuração adicional**.

```bash
# Aplicar migrações (cria o banco automaticamente)
alembic upgrade head
```

#### 🔑 Configuração de Usuário Administrador

```bash
# Criar administrador com credenciais padrão
python -m src.backend.cli seed-admin

# Ou criar com credenciais personalizadas
python -m src.backend.cli seed-admin --email seu@email.com --senha SuaSenhaSegura
```

#### ▶️ Executar a Aplicação

```bash
# Iniciar aplicação desktop
python -m src.client_desktop
```

A interface gráfica será aberta automaticamente.

### 🔧 Comandos de Administração

#### Gerenciamento de Usuários Admin

```bash
# Visualizar ajuda
python -m src.backend.cli --help

# Criar administrador (idempotente)
python -m src.backend.cli seed-admin --email admin@exemplo.com --senha admin123

# Usar configurações do ambiente
python -m src.backend.cli seed-admin

# Auto-seed (respeita configurações)
python -m src.backend.cli auto-seed
```

#### Migrações do Banco

```bash
# Aplicar todas as migrações pendentes
alembic upgrade head

# Gerar nova migração após alterar models
alembic revision --autogenerate -m "descrição da mudança"

# Aplicar migração específica
alembic upgrade <revision_id>

# Visualizar histórico
alembic history
```

Saídas possíveis do seed-admin:
- `Admin criado (admin@exemplo.com)`
- `Admin já existia (admin@exemplo.com)`

---

## Autenticação e Segurança

### 🔐 Sistema de Login Desktop

O CliniSys utiliza autenticação local com interface gráfica Tkinter:

**Credenciais Padrão:**
* **Email:** admin@exemplo.com
* **Senha:** admin123

### 🛡️ Recursos de Segurança

**Autenticação JWT:**
* Tokens JWT para sessões seguras
* Refresh tokens com rotação automática
* Logout com revogação de tokens

**Política de Senhas:**
* Mínimo 8 caracteres
* Pelo menos 1 letra e 1 dígito
* Hashing bcrypt para armazenamento

**Controle de Acesso:**
* Perfis de usuário (admin, professor, recepcionista, aluno)
* Permissões baseadas em perfil
* Ativação/desativação de contas

### 🔑 Gerenciamento de Usuários

A aplicação permite:
* Criar novos usuários com diferentes perfis
* Editar informações de usuários existentes
* Ativar/desativar contas
* Redefinir senhas (apenas administradores)

---

## Testes

### 🧪 Executar Testes Automatizados

```bash
# Executar todos os testes
pytest -q

# Executar arquivo específico
pytest tests/test_auth.py -q

# Executar teste por nome (substring)
pytest -k login -q

# Executar com cobertura
pytest --cov=src tests/
```

### 📊 Cobertura de Testes

Os testes cobrem:
* Autenticação e autorização
* CRUD de usuários
* CRUD de pacientes
* Validação de dados
* Segurança (senhas, tokens)

### 🔍 Histórico de Versões

**v1.0** - Sistema web com FastAPI
**v2.0** - Migração completa para desktop com Tkinter

---

## 🔐 Segurança e Boas Práticas

### Recomendações Importantes:

* **Altere as credenciais padrão** imediatamente após a primeira execução
* **Use senhas fortes** (mínimo 8 caracteres, letras + números)
* **Mantenha backups regulares** do banco de dados SQLite
* **Atualize regularmente** as dependências Python
* **Execute testes** antes de fazer alterações no código

### Localização dos Dados:

* **Banco de dados:** `clinisys.db` (criado automaticamente)
* **Logs:** Console da aplicação
* **Configurações:** Arquivo de configuração interno

---

## Atualizações Recentes

### 🚀 v2.0 - Migração para Desktop (Setembro 2024)

**Principais Mudanças:**
* **Conversão completa para aplicação desktop** com interface Tkinter
* **Remoção do backend web** (FastAPI) - agora 100% local
* **Implementação da arquitetura MVC** com separação clara de responsabilidades
* **Interface gráfica completa** para login, usuários e pacientes
* **Banco SQLite integrado** - sem necessidade de configuração externa

**Melhorias Implementadas:**
* Sistema de login gráfico com autenticação JWT
* CRUD completo de usuários com interface visual
* CRUD completo de pacientes com validação avançada
* Busca inteligente por nome e CPF
* Controle de perfis e permissões
* Validação robusta de dados com Pydantic
* Testes automatizados mantidos e atualizados

**Benefícios da Nova Arquitetura:**
* 📦 **Distribuição simples** - executável único
* 🔒 **Maior segurança** - dados ficam localmente
* ⚡ **Performance superior** - sem latência de rede
* 🛠️ **Manutenção facilitada** - sem infraestrutura complexa

---

## Autores

* **Davi Turnes Vieira (24100904)** - [@daviturnesv](https://github.com/daviturnesv)
* Bruno Queiroz Castro (24102975)
* Igor Velmud Bandero (24102980)
* Kalel Gomes de Freitas (24102982)

