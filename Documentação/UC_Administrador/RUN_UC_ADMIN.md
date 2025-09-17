# UC Administrador (Isolado - MVC)

Este módulo roda isolado, expondo apenas autenticação e CRUD de usuários.

## Como executar

1. Crie e ative um ambiente virtual e instale deps do `requirements.txt` na raiz.
2. Rode a aplicação:

```powershell
# Windows PowerShell
$env:APP_DATABASE_URL="sqlite+aiosqlite:///./clinisys_uc_admin.db"
$env:APP_SECRET_KEY="dev-secret-change"
$env:APP_ADMIN_EMAIL="admin@local"
$env:APP_ADMIN_PASSWORD="admin123"
.venv\Scripts\uvicorn.exe src.uc_administrador.app:app --reload --port 8010
```

Swagger: [http://localhost:8010/uc-admin/docs](http://localhost:8010/uc-admin/docs)

## Fluxo

- POST /uc-admin/auth/token → access_token
- CRUD /uc-admin/usuarios → requer token de admin

Obs: O seed cria/garante um admin padrão com as envs acima.
