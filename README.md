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
7. [Licença](#licença)

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

O projeto está na fase de **especificação e modelagem**. As instruções de instalação e execução serão adicionadas quando a primeira versão funcional for liberada.

Enquanto isso, para contribuir com a documentação:

1. Clone o repositório:
   ```bash
   git clone https://github.com/daviturnesv/UFSC_INE5608_CliniSys.git
   ```
2. Acesse o diretório do projeto:
   ```bash
   cd UFSC_INE5608_CliniSys
   ```
3. Crie uma branch para sua contribuição:
   ```bash
   git checkout -b docs/minha-contribuicao
   ```
4. Após alterações:
   ```bash
   git add .
   git commit -m "docs: melhora documentação de requisitos"
   git push origin docs/minha-contribuicao
   ```
5. Abra um Pull Request no GitHub.

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