# Entrega UC Administrador — Desktop (Tkinter)

Este pacote contém apenas os arquivos necessários para rodar a UC de Gerenciamento de Usuários 100% Desktop, com SQLite local e sem servidor HTTP.

## Como executar (Windows PowerShell)

Pré-requisitos: Python 3.12+, virtualenv ativado (opcional).

1. Instale as dependências mínimas:

```powershell
pip install -r requirements.txt
```

2. Execute a aplicação Desktop:

```powershell
python -m src.client_desktop
```

A base `clinisys_uc_admin.db` será criada automaticamente no primeiro run, com um usuário administrador seed (email: admin@exemplo.com, senha: admin123) e uma clínica padrão.

## Componentes incluídos

- src/client_desktop (Tkinter): `uc_admin_users_tk.py`, `__main__.py`
- src/uc_administrador (somente o que a tela usa): core/config.py, core/security.py, db/database.py, models/{usuario.py, clinica.py, __init__.py}, services/usuario_service.py
- requirements.txt (subset útil ao Desktop)

