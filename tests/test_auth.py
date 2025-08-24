from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_fluxo_basico(cliente: AsyncClient, usuario_admin):
    # Tentar login com credenciais válidas
    resp = await cliente.post("/auth/token", data={"username": usuario_admin.email, "password": "admin123"})
    assert resp.status_code == 200, resp.text
    dados = resp.json()
    assert dados["token_type"] == "bearer"
    assert "access_token" in dados

    # Usar token em /auth/me
    headers = {"Authorization": f"Bearer {dados['access_token']}"}
    me = await cliente.get("/auth/me", headers=headers)
    assert me.status_code == 200, me.text
    corpo = me.json()
    # Para compatibilidade com envelope opcional
    if "data" in corpo:
        corpo = corpo["data"]
    assert corpo["email"] == usuario_admin.email
