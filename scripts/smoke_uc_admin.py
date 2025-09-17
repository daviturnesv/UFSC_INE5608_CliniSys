import os
import sys
import asyncio
from pathlib import Path

import httpx
import time

# Ensure project root on sys.path so `src` package is importable when running this file directly
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Run FastAPI app in-process (no external server) using ASGI transport
from src.uc_administrador.app import app

USUARIOS_PATH = "/uc-admin/usuarios/"


async def main() -> None:
    # Ensure defaults (can be overridden by environment)
    os.environ.setdefault("APP_ADMIN_EMAIL", "admin@exemplo.com")
    os.environ.setdefault("APP_ADMIN_PASSWORD", "admin123")
    os.environ.setdefault("APP_DATABASE_URL", "sqlite+aiosqlite:///./clinisys_uc_admin.db")

    # Ensure FastAPI lifespan (startup/shutdown) runs to create tables and seed admin
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # List users (no auth required in this isolated app)
            list_resp = await client.get(USUARIOS_PATH, follow_redirects=True)
            list_resp.raise_for_status()
            payload = list_resp.json()
            assert payload.get("success") is True, payload
            before = payload.get("meta", {}).get("total")

            # Create a user
            # Unique email per run to avoid duplicates
            unique_email = f"teste+smoke_{int(time.time())}@example.com"
            create_json = {
                "nome": "Teste",
                "email": unique_email,
                "perfil": "admin",
                "senha": "Senha1234",
                "cpf": str(int(time.time()))[-11:].rjust(11, "0"),
            }
            create_resp = await client.post(USUARIOS_PATH, json=create_json)
            if create_resp.is_error:
                print("Create status:", create_resp.status_code)
                try:
                    print("Create body:", create_resp.json())
                except Exception:
                    print("Create body (raw):", create_resp.text)
                create_resp.raise_for_status()
            create_payload = create_resp.json()
            assert create_payload.get("success") is True, create_payload

            # List again and ensure count >= before
            list2 = await client.get(USUARIOS_PATH, follow_redirects=True)
            list2.raise_for_status()
            payload2 = list2.json()
            assert payload2.get("success") is True, payload2
            after = payload2.get("meta", {}).get("total")
            assert after is None or before is None or after >= before, (before, after)

        print("OK: list and create users working.")


if __name__ == "__main__":
    asyncio.run(main())
