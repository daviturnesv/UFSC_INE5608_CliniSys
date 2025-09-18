# Interface Desktop (Tkinter) para UC Administrador

- Arquivo: `src/client_desktop/uc_admin_users_tk.py`
- Objetivo: GUI desktop mínima para listar/criar/atualizar/remover usuários, ativar/desativar e alterar senha, alinhada com UC Administrador.

## Como executar

- Garanta que o ambiente Python com os requisitos instalados e o BD acessível (usa as mesmas configurações de `src/uc_administrador`).
- Da raiz do projeto, execute:
  - Windows PowerShell: `python -m src.client_desktop.uc_admin_users_tk`

## Notas

- Para aluno/professor, o ID da Clínica é necessário na criação. Crie a Clínica via API antecipadamente ou adicione diretamente no BD.
- Usa os serviços assíncronos e sessão diretamente; não é necessário servidor HTTP.
- Inicializa o admin se estiver faltando usando `APP_ADMIN_EMAIL`, `APP_ADMIN_PASSWORD` e `APP_ADMIN_CPF`.
