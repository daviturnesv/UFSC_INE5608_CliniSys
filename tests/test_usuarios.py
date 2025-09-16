from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_listar_usuarios_filtra_e_pagina(cliente: AsyncClient, usuario_admin):
    # Login para obter token
    resp = await cliente.post("/auth/token", data={"username": usuario_admin.email, "password": "admin123"})
    login_json = resp.json()
    token = login_json["data"]["access_token"] if "data" in login_json else login_json["access_token"]
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
    login_json = resp_login.json()
    token = login_json["data"]["access_token"] if "data" in login_json else login_json["access_token"]
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
    novo_json = novo.json()
    usuario_id = novo_json.get("data", {}).get("id") if "data" in novo_json else novo_json.get("id")

    # desativar
    des = await cliente.patch(f"/usuarios/{usuario_id}/desativar", headers=headers)
    assert des.status_code == 200
    # ativar
    atv = await cliente.patch(f"/usuarios/{usuario_id}/ativar", headers=headers)
    assert atv.status_code == 200


@pytest.mark.asyncio
async def test_alterar_senha_usuario_fluxos(cliente: AsyncClient, usuario_admin):
    # login admin
    resp_login = await cliente.post("/auth/token", data={"username": usuario_admin.email, "password": "admin123"})
    token = resp_login.json().get("data", {}).get("access_token") if "data" in resp_login.json() else resp_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # criar usuario alvo
    novo = await cliente.post(
        "/usuarios/",
        json={"nome": "TrocaSenha", "email": "troca@exemplo.com", "perfil": "aluno", "senha": "Senha123"},
        headers=headers,
    )
    assert novo.status_code == 201, novo.text
    user_id = novo.json()["data"]["id"]

    # admin altera senha sem senha_atual
    troca_admin = await cliente.patch(f"/usuarios/{user_id}/senha", json={"nova_senha": "NovaSenha123"}, headers=headers)
    assert troca_admin.status_code == 200, troca_admin.text

    # login como usuario com nova senha
    login_user = await cliente.post("/auth/token", data={"username": "troca@exemplo.com", "password": "NovaSenha123"})
    assert login_user.status_code == 200, login_user.text
    user_token = login_user.json().get("data", {}).get("access_token") if "data" in login_user.json() else login_user.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # usuário troca a própria senha (precisa senha_atual)
    troca_self_fail = await cliente.patch(f"/usuarios/{user_id}/senha", json={"nova_senha": "Outra1234"}, headers=user_headers)
    assert troca_self_fail.status_code == 400
    troca_self_ok = await cliente.patch(
        f"/usuarios/{user_id}/senha", json={"senha_atual": "NovaSenha123", "nova_senha": "Outra1234"}, headers=user_headers
    )
    assert troca_self_ok.status_code == 200

    # login com a nova
    login_user2 = await cliente.post("/auth/token", data={"username": "troca@exemplo.com", "password": "Outra1234"})
    assert login_user2.status_code == 200
