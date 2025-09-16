from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_crud_usuarios_basico(cliente: AsyncClient, usuario_admin):
    # login admin
    resp = await cliente.post("/auth/token", data={"username": usuario_admin.email, "password": "admin123"})
    assert resp.status_code == 200
    token = resp.json().get("data", {}).get("access_token") or resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # criar
    novo = await cliente.post(
        "/usuarios/",
        json={"nome": "User Admin UC", "email": "adminuc@exemplo.com", "perfil": "aluno", "senha": "Senha123"},
        headers=headers,
    )
    assert novo.status_code == 201, novo.text
    uid = novo.json()["data"]["id"]

    # obter
    get1 = await cliente.get(f"/usuarios/{uid}", headers=headers)
    assert get1.status_code == 200

    # atualizar
    put1 = await cliente.put(f"/usuarios/{uid}", json={"nome": "User Admin UC 2"}, headers=headers)
    assert put1.status_code == 200
    assert put1.json()["data"]["nome"] == "User Admin UC 2"

    # desativar/ativar
    des = await cliente.patch(f"/usuarios/{uid}/desativar", headers=headers)
    assert des.status_code == 200
    atv = await cliente.patch(f"/usuarios/{uid}/ativar", headers=headers)
    assert atv.status_code == 200

    # deletar
    rem = await cliente.delete(f"/usuarios/{uid}", headers=headers)
    assert rem.status_code in (200, 204)
