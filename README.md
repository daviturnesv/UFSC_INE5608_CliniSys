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
```

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

### 6. Criar usuário admin (provisório)

Ainda não há seed automático. Use o endpoint de criação de usuário (`POST /usuarios/`) autenticado com um token de um usuário ADMIN existente. Temporariamente você pode inserir manualmente via SQL ou adaptar um script de seed.

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

Sugestões ou dúvidas: abra uma Issue no repositório.
