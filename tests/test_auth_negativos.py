from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_invalido(cliente: AsyncClient):
    resp = await cliente.post("/auth/token", data={"username": "naoexiste@x.com", "password": "errada"})
    assert resp.status_code == 401
    corpo = resp.json()
    assert corpo.get("detail") == "Credenciais inválidas"


@pytest.mark.asyncio
async def test_login_usuario_inativo(cliente: AsyncClient, usuario_admin):
    # criar usuario e desativar diretamente
    login_admin = await cliente.post("/auth/token", data={"username": usuario_admin.email, "password": "admin123"})
    login_json = login_admin.json()
    token = login_json.get("data", {}).get("access_token") if "data" in login_json else login_json["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    novo = await cliente.post(
        "/usuarios/",
        json={"nome": "Inativo", "email": "inativo@exemplo.com", "perfil": "aluno", "senha": "abc12345"},
        headers=headers,
    )
    assert novo.status_code == 201
    user_id = novo.json()["data"]["id"]

    # desativar
    des = await cliente.patch(f"/usuarios/{user_id}/desativar", headers=headers)
    assert des.status_code == 200

    # tentar login
    resp = await cliente.post("/auth/token", data={"username": "inativo@exemplo.com", "password": "abc12345"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_rate_limit_basico(cliente: AsyncClient):
    # realizar varias tentativas para gatilhar limite
    for i in range(6):
        resp = await cliente.post("/auth/token", data={"username": "flood@exemplo.com", "password": "x"})
        if i < 5:  # primeiras 5 devem falhar com 401 (credenciais)
            assert resp.status_code == 401, f"Tentativa {i+1} deveria ser 401, obtido {resp.status_code}"
        else:  # 6a deve retornar 429 rate limit
            assert resp.status_code == 429, f"Tentativa {i+1} deveria ser 429, obtido {resp.status_code}"
