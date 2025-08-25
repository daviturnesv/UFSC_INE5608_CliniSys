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
