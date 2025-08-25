from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_fluxo_refresh_token(cliente: AsyncClient, usuario_admin):
    # Login inicial
    resp = await cliente.post("/auth/token", data={"username": usuario_admin.email, "password": "admin123"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    data = body.get("data", body)
    old_refresh = data["refresh_token"]
    access_1 = data["access_token"]

    # Chamar /auth/refresh
    ref1 = await cliente.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert ref1.status_code == 200, ref1.text
    body2 = ref1.json().get("data", ref1.json())
    new_refresh = body2["refresh_token"]
    access_2 = body2["access_token"]
    assert new_refresh != old_refresh
    assert access_2 != access_1

    # Reusar refresh antigo deve falhar (revogado)
    ref_fail = await cliente.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert ref_fail.status_code == 401

    # Usar novo deve funcionar uma vez
    ref2 = await cliente.post("/auth/refresh", json={"refresh_token": new_refresh})
    assert ref2.status_code == 200
    body3 = ref2.json().get("data", ref2.json())
    newer_refresh = body3["refresh_token"]
    assert newer_refresh != new_refresh


@pytest.mark.asyncio
async def test_criacao_usuario_senha_fraca(cliente: AsyncClient, usuario_admin):
    # Login admin para obter token
    login = await cliente.post("/auth/token", data={"username": usuario_admin.email, "password": "admin123"})
    token = login.json().get("data", login.json())["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # Tentar senha fraca (<8 chars)
    resp = await cliente.post(
        "/usuarios/",
        json={"nome": "Fraco", "email": "fraco@exemplo.com", "perfil": "aluno", "senha": "abc123"},
        headers=headers,
    )
    assert resp.status_code == 400
    detalhe = resp.json().get("detail")
    assert "Senha" in detalhe
