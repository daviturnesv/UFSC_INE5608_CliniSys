## Escopo do projeto CliniSys-Escola

# 1. Introdução

## 1.1. Objetivo do Documento

Este documento tem como objetivo apresentar o escopo do sistema CliniSys-Escola,
estabelecendo seus requisitos, funcionalidades e as informações necessárias para sua
implementação.^ Ele servirá como um guia para a equipe de desenvolvimento, alinhando
expectativas e orientando a entrega das funcionalidades previstas para atender às
necessidades do sistema.

## 1.2. Referências

**DOC01** - Entrevista inicial com Maria Oliveira (diretora do departamento de odontologia),
realizada em 20/08/25. Ata da entrevista encontra-se disponível em:
<https://docs.google.com/document/d/1VURfIYOYReAEw78718ALJpqzVWv7fQkNilQ6dzA7O
g/edit?usp=sharing>.

**DOC02** - Formulário de cadastro e triagem de paciente. Recebida em 21/08/25 de Maria
Oliveira. Disponível em:
<https://docs.google.com/document/d/1xcHRO4b6sUm-KpVlQVyITb5A6zpKrnLMLrMCEGXgs
k/edit?tab=t.0>

**DOC03** - Planilha de procedimentos realizados em consultas. Recebida em 21/08/25 de Maria
Oliveira. Disponível em:
<https://docs.google.com/spreadsheets/d/1D7RW45vFZPGDGhXLXp34BK3Z-9Fw3oOqpYURvO
lP-dk/edit?gid=0#gid=0>

**DOC04** - Resolução nº 3. Institui as diretrizes curriculares nacionais do curso de graduação em
Odontologia e dá outras providências; 21 de junho de 2021; Conselho Nacional de Educação
(CNE); Disponível em:
<https://portal.mec.gov.br/docman/junho-2021-pdf/191741-rces003-21/file>

_____________________________________________________________________________________________


## 2.1 Visão Geral

As diretrizes curriculares nacionais do curso de graduação em odontologia, preveem
que pelo menos 40% da carga do curso devem ser destinadas às atividades de prática clínica.
Neste contexto, as clínicas-escola possibilitam aos estudantes a obtenção dessa formação
prática através de atendimentos às demandas reais da comunidade, sob supervisão de
professores.
A clínica-escola contratante do sistema faz parte do Departamento de Ensino de
Odontologia da UNILAVE, que oferece três disciplinas de prática clínica para o curso de
graduação (Clínica I, II e III).
Atualmente, a clínica-escola utiliza formulários e prontuários físicos para registrar as
demandas e os procedimentos realizados nos pacientes. Este método apresenta riscos de
perda de dados, inconsistências e dificuldades de acesso à informação pelos alunos,
professores e demais envolvidos no atendimento.
O controle atual da lista de triagem e de espera para consulta é feito em planilhas
eletrônicas, que limitam a gestão de prioridade de demandas pelos alunos
O registro de informações em meios físicos também dificulta a geração de relatório para
definição de indicadores de desempenho da clínica e para avaliação dos alunos pelos
professores.
Entre as soluções possíveis para os problemas levantados estão: a digitalização dos
formulários e prontuários físicos, para possibilitar que todos os procedimentos e informações
clínicas possam ser registrados e recuperados de forma automática; a apresentação da lista
de pacientes que estão aguardando triagem e consulta em uma lista ordenada e a possibilidade
para os professores gerarem relatório sobre os atendimentos.
Para a clínica-escola de odontologia da UNILAVE, o sistema CliniSys-Escola é uma
solução digital integrada para resolver os problemas de gerenciamento do fluxo de
atendimentos. A principal proposta de valor do sistema é a centralização de todas as
informações operacionais das clínicas em uma única plataforma, eliminando a dependência de
arquivos físicos e planilhas.


## 2.2 Descrição dos usuários

```
● Aluno : Estudante de graduação em odontologia entre 17 e 35 anos. Formação mínima
de 2° grau. Conhecimento de informática variando entre básico e avançado. Cursando
as disciplinas de prática clínica. Suas responsabilidades no sistema incluem a
realização da triagem dos pacientes, o agendamento e realização de consultas, o
preenchimento dos procedimentos realizados no prontuário e a obtenção de
permissões dos professores para realizar a alta ou desvinculação de pacientes.
● Professor : Docente responsável por orientar uma turma de alunos. Idade entre 25 e 60
anos. Formação mínima de 3° grau. Conhecimento de informática variando entre básico
e avançado. Suas responsabilidades no sistema incluem autorizar as solicitações de
alta ou desvinculação de pacientes feita pelos alunos, além da geração de relatórios
sobre os atendimentos realizados.
● Recepcionista : Funcionário responsável pelo primeiro atendimento na recepção da
clínica. Idade entre 18 e 30 anos. Formação mínima de 2° grau. Conhecimento básico de
informática. Suas responsabilidades são o cadastro inicial e o encaminhamento dos
pacientes para a fila de triagem.
● Administrador : Técnico responsável pelo sistema. Faixa etária de 25 a 50 anos, com
formação mínima de 3° grau, conhecimento avançado de informática. Possui
permissões globais para gerenciar todas as contas de usuário (alunos, professores,
recepcionistas), e extrair relatórios do sistema.
```
## 2.3 Benefícios

```
● Reduzir em, no mínimo, 50% o tempo de registro e consulta de dados clínicos;
● Reduzir em, no mínimo, 30% o tempo de liberação de altas e desvinculação de
pacientes;
● Diminuir em 30% os custos de impressão na clínica;
```

```
● Aumentar a transparência e a confiabilidade das informações sobre os atendimentos;
● Apoiar a tomada de decisão pela direção da clínica-escola por meio da geração de
relatórios;
```
## 2.4 Limitações e Restrições

```
● O sistema não terá funcionalidades de gestão financeira ou de controle de estoques.
● O sistema não será integrado a sistemas externos de gestão hospitalar, acadêmica ou
administrativa já existentes na instituição.
● O sistema não fornecerá recursos de teleatendimento ou videoconferência para
consultas remotas.
● O sistema não será responsável por emitir documentos oficiais acadêmicos, como
históricos escolares ou diplomas, limitando-se ao suporte pedagógico e clínico.
```
_____________________________________________________________________________________________

## 3. Requisitos

## 3.1 Requisitos Funcionais

**RF01** : o sistema deve permitir o cadastro de alunos, professores e recepcionistas pelo
administrador

**RF02** : o sistema deve permitir que os usuários façam login;

**RF03** : o sistema deve permitir que os recepcionistas cadastrem os pacientes em uma lista para
triagem;

**RF04:** o sistema deve permitir que os alunos vejam a lista de pacientes para triagem e a lista de
pacientes triados que estão disponíveis para atendimento;

**RF05** : o sistema deve permitir que um aluno registre as necessidades e o nível de prioridade de
atendimento de um paciente na triagem;

**RF06** : o sistema deve permitir que um aluno agende consultas com um paciente triado;

**RF07** : o sistema deve permitir que um aluno veja a lista de pacientes com os quais tem


consulta agendada;

**RF08** : o sistema deve permitir que um aluno registre os procedimentos realizados em consulta;

**RF09** : o sistema deve permitir um aluno atualize a situação do paciente após a consulta;

**RF10** : o sistema deve permitir que professores autorizem altas ou desvinculações de pacientes
encaminhadas pelos alunos após consultas;

**RF11** : o sistema deve permitir que os professores gerem um relatório com todos os
atendimentos das clínicas no último mês.

**RF12** : o sistema deve permitir que alunos busquem pacientes por nome ou CPF.

## 3.2 Requisitos Não-Funcionais

**RNF01** : a lista de pacientes disponíveis para atendimento deve diferenciar os níveis de
prioridade de cada caso através de cores diferentes (ex: vermelho, amarelo e verde);

**RNF02** : os campos obrigatórios de um formulário deverão estar marcados com um asterisco;

**RNF03** : a renderização de telas devem ser concluídas em menos de 10 segundos;

**RNF04** : as senhas dos usuários devem ser criptografada antes de serem armazenadas;

**RNF05** : o sistema deve ser desenvolvido com arquitetura em camadas no padrão MVC;

**RNF06** : o sistema deve ser compatível com Windows 10;

**RNF07** : o sistema deve ser operado via interface gráfica.

**RNF08** : o sistema deve utilizar um banco de dados centralizado;

## 3.3 Requisitos de Domínio / Regras de Negócio

**RN01** : O CPF de usuários e de pacientes deve ser único em todo o sistema;


**RN02** : um paciente não pode ter mais de uma consulta agendada para o mesmo dia;

**RN03** : uma consulta só pode ser marcada para dias de semana, em horário comercial;
(segunda à sexta, das 8:00h às 18:00h);

**RN04** : um aluno só pode marcar consultas com os pacientes disponíveis para a clínica (I, II ou
III) em que está matriculado;

**RN05** : se um paciente faltar mais de duas vezes seguidas às consultas agendadas, o aluno
deve registrar o caso como desistência e encaminhar o caso para autorização do professor.

**RN06** : Um paciente não deve ter duas consultas marcadas para o mesmo horário.

## 3.4 Matriz de Rastreabilidade


