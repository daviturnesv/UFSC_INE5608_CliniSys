from typing import Any, Optional

def envelope(sucesso: bool, dados: Any, erro: Optional[str] = None, meta: Optional[dict] = None):
    body = {"success": sucesso, "data": dados}
    if erro is not None:
        body["error"] = erro
    if meta is not None:
        body["meta"] = meta
    return body
