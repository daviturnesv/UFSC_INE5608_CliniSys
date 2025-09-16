from __future__ import annotations

import pytest
from httpx import AsyncClient
from datetime import date


@pytest.mark.asyncio
async def test_crud_paciente_basico(cliente: AsyncClient, usuario_admin):
    # login
    resp_login = await cliente.post("/auth/token", data={"username": usuario_admin.email, "password": "admin123"})
    token = resp_login.json()["data"]["access_token"] if "data" in resp_login.json() else resp_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "nome_completo": "Paciente Teste",
        "cpf": "123.456.789-00",
        "data_nascimento": str(date(2000,1,1)),
        "telefone": "48999990000"
    }
    # create
    criado = await cliente.post("/pacientes/", json=payload, headers=headers)
    assert criado.status_code == 201, criado.text
    pid = criado.json()["data"]["id"]

    # get
    obtido = await cliente.get(f"/pacientes/{pid}", headers=headers)
    assert obtido.status_code == 200
    assert obtido.json()["data"]["cpf"] == payload["cpf"]

    # list
    lista = await cliente.get("/pacientes/?skip=0&limit=10", headers=headers)
    assert lista.status_code == 200
    assert any(p["cpf"] == payload["cpf"] for p in lista.json()["data"])

    # update
    payload_up = payload | {"telefone": "48911112222"}
    atualizado = await cliente.put(f"/pacientes/{pid}", json=payload_up, headers=headers)
    assert atualizado.status_code == 200
    assert atualizado.json()["data"]["telefone"] == "48911112222"

    # delete
    remov = await cliente.delete(f"/pacientes/{pid}", headers=headers)
    assert remov.status_code == 204 or remov.status_code == 200

    # confirm deletion
    not_found = await cliente.get(f"/pacientes/{pid}", headers=headers)
    assert not_found.status_code == 404


@pytest.mark.asyncio
async def test_uc_recepcionista_pode_crud(cliente: AsyncClient, usuario_recepcionista):
    # login recepcionista
    login = await cliente.post("/auth/token", data={"username": usuario_recepcionista.email, "password": "recep123"})
    token = login.json().get("data", {}).get("access_token") if "data" in login.json() else login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "nome_completo": "Paciente Recep",
        "cpf": "000.111.222-33",
        "data_nascimento": str(date(2001,1,1)),
        "telefone": None,
    }
    criado = await cliente.post("/pacientes/", json=payload, headers=headers)
    assert criado.status_code == 201, criado.text
    pid = criado.json()["data"]["id"]

    # update
    up = await cliente.put(f"/pacientes/{pid}", json=payload | {"telefone": "48900001111"}, headers=headers)
    assert up.status_code == 200

    # search/list
    busca = await cliente.get("/pacientes/busca?nome=Recep", headers=headers)
    assert busca.status_code == 200
    lista = await cliente.get("/pacientes/?skip=0&limit=5", headers=headers)
    assert lista.status_code == 200

    # delete
    rem = await cliente.delete(f"/pacientes/{pid}", headers=headers)
    assert rem.status_code in (200, 204)


@pytest.mark.asyncio
async def test_uc_aluno_nao_pode_modificar_pacientes(cliente: AsyncClient, usuario_aluno):
    login = await cliente.post("/auth/token", data={"username": usuario_aluno.email, "password": "aluno123"})
    token = login.json().get("data", {}).get("access_token") if "data" in login.json() else login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "nome_completo": "Paciente Aluno",
        "cpf": "999.888.777-66",
        "data_nascimento": str(date(2002,2,2)),
        "telefone": None,
    }
    # create should be forbidden
    criado = await cliente.post("/pacientes/", json=payload, headers=headers)
    assert criado.status_code == 403

    # listing should be allowed
    lista = await cliente.get("/pacientes/?skip=0&limit=5", headers=headers)
    assert lista.status_code == 200


@pytest.mark.asyncio
async def test_busca_pacientes_por_nome_e_cpf(cliente: AsyncClient, usuario_admin):
    # login
    resp_login = await cliente.post("/auth/token", data={"username": usuario_admin.email, "password": "admin123"})
    token = resp_login.json()["data"]["access_token"] if "data" in resp_login.json() else resp_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # cria dois pacientes
    dados = [
        {"nome_completo": "Maria da Silva", "cpf": "111.222.333-44", "data_nascimento": str(date(1990, 5, 20)), "telefone": None},
        {"nome_completo": "Mariana Souza", "cpf": "555.666.777-88", "data_nascimento": str(date(1985, 7, 15)), "telefone": None},
    ]
    for p in dados:
        await cliente.post("/pacientes/", json=p, headers=headers)

    # busca por nome parcial
    resp = await cliente.get("/pacientes/busca?nome=mari", headers=headers)
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert "meta" in corpo and "total" in corpo["meta"]
    nomes = [r["nome_completo"].lower() for r in corpo["data"]]
    assert any("maria" in n for n in nomes) and any("mariana" in n for n in nomes)

    # busca por cpf exato
    resp2 = await cliente.get("/pacientes/busca?cpf=111.222.333-44", headers=headers)
    assert resp2.status_code == 200
    corpo2 = resp2.json()
    assert len(corpo2["data"]) == 1 and corpo2["data"][0]["cpf"] == "111.222.333-44"
