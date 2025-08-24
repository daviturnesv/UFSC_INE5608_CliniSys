# CliniSys-Escola

![Status do Projeto](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)

Sistema de Gestão para Clínica-Escola de Odontologia da UFSC.

Projeto acadêmico desenvolvido para a disciplina de **Análise e Projeto de Sistemas (INE5608)** da Universidade Federal de Santa Catarina (UFSC).

---

## Índice

1. [Sobre o Projeto](#sobre-o-projeto)
2. [Principais Funcionalidades](#principais-funcionalidades)
3. [Arquitetura e Stack Tecnológico](#arquitetura-e-stack-tecnológico)
4. [Estrutura do Repositório](#estrutura-do-repositório)
5. [Como Começar](#como-começar)
6. [Autores](#autores)
7. [Status futuro](#status-futuro)
8. [Contato](#contato)

---

## Sobre o Projeto

O **CliniSys-Escola** é um sistema de gestão multiplataforma (Desktop e Mobile) projetado para otimizar a administração e o fluxo de atendimentos da clínica-escola de odontologia da UFSC.

O objetivo principal é substituir o processo de trabalho atual, baseado em planilhas compartilhadas e prontuários físicos, que apresentam riscos de inconsistência, perda de dados e lentidão no acesso ao histórico dos pacientes. O sistema centraliza as informações em um ambiente digital integrado, seguro e eficiente, melhorando a experiência de alunos, professores supervisores e pacientes.

---

## Principais Funcionalidades

- **Gestão de Perfis de Usuário:** Controle de acesso para Aluno, Professor, Recepcionista e Administrador.
- **Controle de Triagem e Lista de Espera:** Digitalização do fluxo de triagem com fila centralizada.
- **Agenda de Consultas Sincronizada:** Agendamento, remarcação e cancelamento com sincronização em tempo real.
- **Prontuário Eletrônico do Paciente (PEP):** Registro completo de procedimentos e histórico clínico.
- **Módulo de Supervisão:** Revisão e validação de procedimentos por professores.
- **Gestão Acadêmica:** Cadastro de alunos e professores e associação às disciplinas de prática clínica.
- **Funcionamento Offline Parcial:** Cache local para consultas e registro temporário.

---

## Arquitetura e Stack Tecnológico

Arquitetura **Cliente-Servidor** com um backend centralizado (fonte única de verdade) consumido por clientes Desktop e Mobile via API.

| Componente | Tecnologia | Justificativa |
|-----------|------------|---------------|
| Backend (API) | FastAPI | Alta performance, suporte assíncrono, validação e docs automáticas. |
| Banco de Dados Central | PostgreSQL | Conformidade ACID e robustez para dados clínicos sensíveis. |
| Cliente Desktop | PySide6 (Qt for Python) | Widgets avançados e interface profissional. |
| Cliente Mobile | BeeWare | Interfaces 100% nativas (iOS/Android) e melhor UX. |
| Persistência Local | SQLite | Cache leve para operação offline e desempenho. |
| Formato de Comunicação | JSON | Padrão leve, interoperável e amplamente suportado. |

---

## Estrutura do Repositório

```text
/
├── Documentação/
│   ├── 1. Introdução.EAB
│   ├── 2. Descrição geral do produto.EAB
│   ├── 3.1 Requisitos funcionais.EAB
│   ├── 3.2 Requisitos Não Funcionais.EAB
│   ├── 3.3 Requisitos de domínio  Regras de negócio.EAB
│   ├── matriz_rastreabilidade.png
│   └── template_v2.eap
├── src/                  # (Futuro local do código fonte)
│   ├── backend/
│   ├── client_desktop/
│   └── client_mobile/
└── README.md
```

---

## Como Começar

### TL;DR (Quick Start)

```bash
git clone https://github.com/daviturnesv/UFSC_INE5608_CliniSys.git
cd UFSC_INE5608_CliniSys
python -m venv .venv && .".venv/Scripts/activate"
pip install -r requirements.txt
alembic upgrade head
python -m src.backend.cli seed-admin  # cria admin (opcionalmente configure .env)
uvicorn src.backend.main:app --reload
```

Abrir <http://127.0.0.1:8000/docs>

### 1. Clonar o repositório

```bash
git clone https://github.com/daviturnesv/UFSC_INE5608_CliniSys.git
cd UFSC_INE5608_CliniSys
```

### 2. Configurar o backend (API)

Criar ambiente virtual (Python 3.12+):

```bash
python -m venv .venv
".venv/Scripts/activate"  # Windows PowerShell
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Arquivo `.env`

Crie um arquivo `.env` na raiz (valores de exemplo, ajuste para seu ambiente):

```env
APP_DB_USER=postgres
APP_DB_PASSWORD=postgres
APP_DB_HOST=localhost
APP_DB_PORT=5432
APP_DB_NAME=clinisysschool
APP_SECRET_KEY=trocar_esta_chave
APP_SEED_CRIAR=false
APP_SEED_ADMIN_EMAIL=
APP_SEED_ADMIN_SENHA=
```

#### 3.1 Tabela de variáveis de ambiente

| Variável | Obrigatória | Default | Descrição | Produção |
|----------|-------------|---------|-----------|----------|
| APP_DB_HOST | não | localhost | Host do PostgreSQL | Usar host real/serviço |
| APP_DB_PORT | não | 5432 | Porta do PostgreSQL | Ajustar se diferente |
| APP_DB_USER | não | postgres | Usuário DB | Usuário dedicado com mínimos privilégios |
| APP_DB_PASSWORD | não | postgres | Senha DB | Usar senha forte / secret manager |
| APP_DB_NAME | não | clinisysschool | Nome do database | Nome provisionado |
| APP_SECRET_KEY | sim (prática) | changeme/trocar_esta_chave | Chave para assinar JWT | Gerar aleatória forte |
| APP_SEED_CRIAR | não | false | Habilita auto-seed via CLI | Manter false em prod |
| APP_SEED_ADMIN_EMAIL | não | `admin@exemplo.com`* | Email admin seed | Definir corporativo |
| APP_SEED_ADMIN_SENHA | não | admin123* | Senha admin seed | Senha forte temporária |

Valores marcados com * são usados apenas se chamados via CLI sem parâmetros e não devem ser usados em produção.

### 4. Banco de dados & Migrações

1. Certifique-se que o PostgreSQL está rodando e o database existe (`clinisysschool`).
2. Executar migração inicial:

```bash
alembic upgrade head
```

Gerar nova revisão após alterar modelos:

```bash
alembic revision --autogenerate -m "descricao"
alembic upgrade head
```

### 5. Rodar a API

```bash
uvicorn src.backend.main:app --reload
```

Abrir: <http://127.0.0.1:8000/docs>

### 6. Seed / Usuário Admin

Agora existe um CLI para criar (seed) o usuário administrador inicial de forma idempotente.

#### 6.1 Variáveis adicionais no `.env`

Adicione (opcional) para customizar/automatizar:

```env
APP_SEED_CRIAR=true                # se true permite e autoriza auto-seed
APP_SEED_ADMIN_EMAIL=admin@exemplo.com
APP_SEED_ADMIN_SENHA=admin123
```

Se não definir, o CLI usará valores padrão (`admin@exemplo.com` / `admin123`). NÃO usar em produção.

#### 6.2 Comandos do CLI

Listar ajuda:

```bash
python -m src.backend.cli --help
```

Criar (ou garantir) admin com parâmetros explícitos:

```bash
python -m src.backend.cli seed-admin --email meuadmin@dominio.com --senha MinhaSenhaSegura
```

Usar valores do `.env`:

```bash
python -m src.backend.cli seed-admin
```

Auto-seed (respeita `APP_SEED_CRIAR`):

```bash
python -m src.backend.cli auto-seed
```

Saídas possíveis:

```text
Admin criado (admin@exemplo.com)
```

ou

```text
Admin já existia (admin@exemplo.com)
```

#### 6.3 Fluxo sugerido de primeiro uso

1. Ajuste `.env` (incluindo seed se quiser).
2. Rode migrações: `alembic upgrade head`.
3. Execute: `python -m src.backend.cli seed-admin`.
4. Inicie API: `uvicorn src.backend.main:app --reload`.
5. Faça login em `/auth/token` com email/senha definidos.

> Segurança: Gere senha forte e altere após o primeiro login em produção.

### 6.4 Exemplo de Autenticação (Login e uso)

Endpoint de login:

`POST /auth/token` (form-urlencoded)

Campos:

| campo | valor |
|-------|-------|
| username | email do usuário |
| password | senha |

Resposta:

```json
{
	"access_token": "<JWT>",
	"token_type": "bearer"
}
```

Uso em chamadas subsequentes:

Header: `Authorization: Bearer <JWT>`

Validade padrão: 60 minutos (configurável em `access_token_expire_minutes`).

Exemplo curl:

```bash
curl -X POST -d "username=admin@exemplo.com&password=admin123" http://127.0.0.1:8000/auth/token
```

Depois:

```bash
curl -H "Authorization: Bearer <JWT>" http://127.0.0.1:8000/auth/me
```

### 6.5 Envelope de Resposta (Padrão)

Formato unificado (quando aplicado):

```json
{
	"success": true,
	"data": {"exemplo": 123},
	"error": null,
	"meta": {"request_id": "abc123", "duration_ms": 12}
}
```

Erro:

```json
{
	"success": false,
	"data": null,
	"error": {"message": "Credenciais inválidas"},
	"meta": {"request_id": "def456"}
}
```

### 7. Contribuindo com documentação

1. Crie uma branch:

```bash
git checkout -b docs/minha-contribuicao
```

1. Após alterações:

```bash
git add .
git commit -m "docs: melhora documentação de requisitos"
git push origin docs/minha-contribuicao
```

1. Abra um Pull Request.

---

## Autores

- **Davi Turnes Vieira (24100904)** - [@daviturnesv](https://github.com/daviturnesv)
- Bruno Queiroz Castro (24102975)
- Igor Velmud Bandero (24102980)
- Kalel Gomes de Freitas (24102982)

---

## Status Futuro

Próximos passos planejados (roadmap inicial):

- Definição do modelo de dados lógico
- Protótipo de telas (Desktop e Mobile)
- Implementação do esqueleto da API
- Módulo de autenticação e autorização
- MVP com agenda + triagem + prontuário básico

---

## Contato

---

## Testes

Executar todos:
```bash
pytest -q
```

Rodar arquivo específico:

```bash
pytest tests/test_auth.py -q
```

Rodar teste por nome (substring):

```bash
pytest -k login -q
```

---

## Nota de Segurança

- Gere uma SECRET forte:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```
- Não faça commit do `.env` com credenciais sensíveis.
- Nunca use as credenciais seed padrão em produção.
- Rotacione a chave JWT se suspeitar de vazamento (invalidando tokens ativos).

---

Sugestões ou dúvidas: abra uma Issue no repositório.
