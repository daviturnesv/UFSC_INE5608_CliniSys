from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_listar_usuarios_filtra_e_pagina(cliente: AsyncClient, usuario_admin):
    # Login para obter token
    resp = await cliente.post("/auth/token", data={"username": usuario_admin.email, "password": "admin123"})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Listar usuários (deve vir ao menos o admin)
    lista = await cliente.get("/usuarios/?skip=0&limit=10", headers=headers)
    assert lista.status_code == 200
    dados = lista.json()
    if isinstance(dados, dict) and "data" in dados:  # se envelope aplicado
        dados = dados["data"]
    assert isinstance(dados, list)
    assert any(u["email"] == usuario_admin.email for u in dados)


@pytest.mark.asyncio
async def test_ativar_desativar_usuario(cliente: AsyncClient, usuario_admin):
    # Criar novo usuario
    resp_login = await cliente.post("/auth/token", data={"username": usuario_admin.email, "password": "admin123"})
    token = resp_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    novo = await cliente.post(
        "/usuarios/",
        json={
            "nome": "Teste",
            "email": "teste@exemplo.com",
            "perfil": "aluno",
            "senha": "senha123",
        },
        headers=headers,
    )
    assert novo.status_code == 201, novo.text
    usuario_id = novo.json().get("id") or novo.json().get("data", {}).get("id")

    # desativar
    des = await cliente.patch(f"/usuarios/{usuario_id}/desativar", headers=headers)
    assert des.status_code == 200
    # ativar
    atv = await cliente.patch(f"/usuarios/{usuario_id}/ativar", headers=headers)
    assert atv.status_code == 200
