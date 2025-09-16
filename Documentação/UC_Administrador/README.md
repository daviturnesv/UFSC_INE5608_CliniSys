# UC Administrador: CRUD Geral

Este pacote documenta e permite demonstrar a UC do Administrador (CRUD geral), cobrindo gestão de usuários e visões auxiliares de pacientes e fila.

## Escopo e Permissões (RBAC)

- Administrador
  - Pode: criar/listar/obter/atualizar/remover usuários; ativar/desativar; alterar senha de qualquer usuário.
  - Pode: listar/buscar pacientes; (CRUD de pacientes também permitido, mas tipicamente delegado à Recepção).
- Perfis (referência): admin, recepcionista, aluno, professor.

## Endpoints Principais (Usuários)

- POST /usuarios/
- GET /usuarios?skip=&limit=&perfil=&ativo=
- GET /usuarios/{id}
- PUT /usuarios/{id}
- PATCH /usuarios/{id}/ativar
- PATCH /usuarios/{id}/desativar
- PATCH /usuarios/{id}/senha
- DELETE /usuarios/{id}

Envelope de resposta: { success, data, error, meta }

## Modelos/Schemas Relevantes

- src/backend/models/usuario.py (UsuarioSistema, PerfilUsuario)
- src/backend/schemas/usuario.py (Usuario, UsuarioCreate, UsuarioUpdate)

## Fluxo Rápido de Demonstração

1. Login admin
   - POST /auth/token (x-www-form-urlencoded)
     - username=`admin@exemplo.com`
     - password=`admin123`
2. Criar usuário
   - POST /usuarios/ { "nome":"Recepção", "email":"recep@exemplo.com", "perfil":"recepcionista", "senha":"recep123" }
3. Listar usuários
   - GET /usuarios?skip=0&limit=10
4. Atualizar dados
   - PUT /usuarios/{id} { "nome": "Recepção 1" }
5. Desativar/Ativar
   - PATCH /usuarios/{id}/desativar
   - PATCH /usuarios/{id}/ativar
6. Remover usuário
   - DELETE /usuarios/{id}

## Notas Técnicas

- Validação de senha: mínimo 8, letra e dígito.
- Usuário inativo não autentica.
- Atualização valida email único.

## Extras

- CLI: seed-usuario — cria rapidamente usuários de demo.
- Fila (consulta): GET /fila com filtros tipo/status.

