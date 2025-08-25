# CliniSys-Escola

Sistema de Gestão para a Clínica-Escola de Odontologia da UFSC.

Projeto acadêmico desenvolvido para a disciplina **INE5608 - Análise e Projeto de Sistemas** (UFSC).

---

## Índice

1. [Visão Geral](#visão-geral)
2. [Funcionalidades Implementadas](#funcionalidades-implementadas)
3. [Arquitetura e Stack](#arquitetura-e-stack)
4. [Estrutura do Repositório](#estrutura-do-repositório)
5. [Configuração e Execução](#configuração-e-execução)
	1. [Ambiente e Dependências](#ambiente-e-dependências)
	2. [Variáveis de Ambiente](#variáveis-de-ambiente)
	3. [Migrações](#migrações)
	4. [Seed (Usuário Admin)](#seed-usuário-admin)
6. [Autenticação e Segurança](#autenticação-e-segurança)
7. [Padrão de Resposta](#padrão-de-resposta)
8. [Testes](#testes)
9. [Atualizações Recentes](#atualizações-recentes)
10. [Autores](#autores)

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

Implementado no backend até o momento:

* CRUD de usuários com perfis (admin, professor, recepcionista, aluno) e ativação/desativação.
* Autenticação via JWT (access tokens) + refresh tokens persistentes com rotação obrigatória.
* Logout com revogação de access token (blacklist em memória para MVP).
* Política mínima de senha (>=8 caracteres, ao menos 1 letra e 1 dígito) e rehash automático de senhas quando parâmetros mudam.
* CRUD básico de pacientes.
* Envelope de resposta padronizado para endpoints.
* Rate limiting simples no login (limite de tentativas em janela curta).
* Campos de auditoria `created_at` / `updated_at` (atualização automática via listener).
* Testes automatizados (pytest) cobrindo fluxos principais (auth, refresh/logout, política de senha, usuários, pacientes).

---

## Arquitetura e Stack

Arquitetura **cliente-servidor**: backend (FastAPI) exposto via HTTP (JSON). Clientes Desktop/Mobile (em desenvolvimento) consumirão a API. PostgreSQL como banco principal (SQLite em testes).

| Componente | Tecnologia | Justificativa |
|-----------|------------|---------------|
| Backend (API) | FastAPI | Alta performance, suporte assíncrono, validação e docs automáticas. |
| Banco de Dados Central | PostgreSQL | Confiabilidade e robustez para dados clínicos. |
| Cliente Desktop | PySide6 | Interface nativa rica. |
| Cliente Mobile | BeeWare | Apps nativos. |
| Persistência Local | SQLite | Cache offline leve. |
| Formato de Comunicação | JSON | Interoperabilidade. |

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
├── src/
│   ├── backend/          # API FastAPI
│   ├── client_desktop/   # Futuro cliente desktop
│   └── client_mobile/    # Futuro cliente mobile
├── tests/                # Testes automatizados
└── README.md
```

---

## Configuração e Execução

### TL;DR

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

### Ambiente e Dependências

```bash
git clone https://github.com/daviturnesv/UFSC_INE5608_CliniSys.git
cd UFSC_INE5608_CliniSys
```

Criar ambiente virtual (Python 3.12+):

```bash
python -m venv .venv
".venv/Scripts/activate"  # Windows PowerShell
pip install --upgrade pip
pip install -r requirements.txt
```

### Variáveis de Ambiente

Criar um arquivo `.env` na raiz (exemplo):

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

Observações:

* APP_SECRET_KEY: definir valor forte/aleatório (não usar default).
* APP_SEED_*: apenas para criação inicial de administrador.

### Migrações

Banco deve existir previamente (PostgreSQL) ou usar SQLite para experimentação.

```bash
alembic upgrade head
```

Gerar nova revisão ao alterar modelos:

```bash
alembic revision --autogenerate -m "descricao"
alembic upgrade head
```

Rodar a API:

```bash
uvicorn src.backend.main:app --reload
```

Abrir: <http://127.0.0.1:8000/docs>

### Seed (Usuário Admin)

CLI para criação idempotente do administrador inicial.

Opcional no `.env`:

```env
APP_SEED_CRIAR=true                # se true permite e autoriza auto-seed
APP_SEED_ADMIN_EMAIL=admin@exemplo.com
APP_SEED_ADMIN_SENHA=admin123
```

Comandos principais:

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

Fluxo inicial resumido:

1. Ajustar `.env`.
2. `alembic upgrade head`.
3. `python -m src.backend.cli seed-admin`.
4. `uvicorn src.backend.main:app --reload`.
5. Login em `/auth/token`.

---

## Autenticação e Segurança

### Login

Endpoint de login:

`POST /auth/token` (form-urlencoded)

Campos:

| campo | valor |
|-------|-------|
| username | email do usuário |
| password | senha |

Resposta (envelopada):

```json
{
	"success": true,
	"data": {
		"access_token": "<JWT>",
		"token_type": "bearer"
	},
	"error": null,
	"meta": {
		"request_id": "...",
		"duration_ms": 7
	}
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

### Refresh Tokens

Fluxo:

1. `POST /auth/token` retorna também `refresh_token`.
2. Cliente armazena o valor de forma segura.
3. `POST /auth/refresh` com `{ "refresh_token": "..." }` quando o access expira.
4. API valida, revoga o usado e retorna novo par (rotação obrigatória).
5. Reuso de token antigo resulta em `401`.

Armazenamento: apenas hash (bcrypt) + expiração configurável (`refresh_token_expire_minutes`).

### Logout

`POST /auth/logout` revoga o access token atual (blacklist em memória no MVP).

### Política de Senha

Requisitos mínimos:

* >= 8 caracteres
* Pelo menos uma letra
* Pelo menos um dígito

Violação: HTTP 400.

### Rate Limiting (Login)

Limite de tentativas inválidas em janela curta com resposta 429 em abuso.

### Campos de Auditoria

`created_at` e `updated_at` mantidos automaticamente (listener na aplicação).

---

## Padrão de Resposta

Formato unificado (quando aplicado):

```json
{
	"success": true,
	"data": {"exemplo": 123},
	"error": null,
	"meta": {"request_id": "abc123", "duration_ms": 12}
}
```

Erro (exemplo):

```json
{
	"success": false,
	"data": null,
	"error": {"message": "Credenciais inválidas"},
	"meta": {"request_id": "def456"}
}
```

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

Gerar uma SECRET forte:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Recomendações básicas:

* Não versionar `.env`.
* Substituir credenciais padrão imediatamente.
* Rotacionar a chave JWT em caso de suspeita de comprometimento.

---

## Atualizações Recentes

* Padronização do envelope `{success, data, error, meta}`.
* Campos de auditoria `created_at` / `updated_at` (listener aplicativo).
* Rate limiting simples no login.
* Logout com revogação de token (blacklist em memória).
* Refresh tokens persistentes com rotação obrigatória.
* Política mínima de senha e rehash automático.
* Testes cobrindo autenticação, refresh/logout, política de senha, usuários e pacientes.

---

## Autores

* **Davi Turnes Vieira (24100904)** - [@daviturnesv](https://github.com/daviturnesv)
* Bruno Queiroz Castro (24102975)
* Igor Velmud Bandero (24102980)
* Kalel Gomes de Freitas (24102982)

