from __future__ import annotations
from typing import Any, Dict


def envelope_resposta(sucesso: bool, dados: Any = None, erro: Dict | None = None, meta: Dict | None = None) -> Dict:
    """Cria envelope padronizado de resposta JSON.

    sucesso: indica se a operação foi bem sucedida
    dados: payload principal
    erro: dict com codigo/mensagem/detalhes
    meta: metadados adicionais (paginacao, tempo, request_id, etc)
    """
    return {"success": sucesso, "data": dados, "error": erro, "meta": meta or {}}
