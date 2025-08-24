from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
import time

from .database import engine, Base  # noqa: F401 (Base importada caso seja necessário introspecção de metadados em runtime)
from .routers import auth, usuarios, pacientes

TITULO_API = "CliniSys-Escola API"
VERSAO_API = "0.1.0"


def envelope_resposta(sucesso: bool, dados=None, erro: dict | None = None, meta: dict | None = None):
    """Padroniza o formato de saída JSON da API.

    sucesso: indica se a operação foi concluída sem erro
    dados: payload retornado
    erro: informações estruturadas sobre a falha
    meta: metadados adicionais (ex: paginação, duração)
    """
    return {"success": sucesso, "data": dados, "error": erro, "meta": meta or {}}


class MiddlewareTempo(BaseHTTPMiddleware):
    """Mede o tempo de cada requisição e injeta em meta.duration_ms se resposta for JSON envelope."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        inicio = time.perf_counter()
        try:
            resposta = await call_next(request)
        except Exception as exc:  # noqa: BLE001
            # Log mínimo; handlers globais formatam retorno final
            print(f"Erro não tratado durante medição de tempo: {exc}")
            raise
        duracao = (time.perf_counter() - inicio) * 1000
        if hasattr(resposta, "media_type") and resposta.media_type == "application/json":
            try:
                corpo_bytes = b"".join([parte async for parte in resposta.body_iterator])  # type: ignore[attr-defined]
                from json import loads, dumps

                payload = loads(corpo_bytes or b"null")
                if isinstance(payload, dict) and "success" in payload:
                    payload.setdefault("meta", {})["duration_ms"] = round(duracao, 2)
                    novo_corpo = dumps(payload).encode()
                    resposta.body_iterator = iter([novo_corpo])  # type: ignore[assignment]
                    resposta.headers["content-length"] = str(len(novo_corpo))
            except Exception:  # noqa: BLE001
                pass
        return resposta


app = FastAPI(title=TITULO_API, version=VERSAO_API)
app.add_middleware(MiddlewareTempo)

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(pacientes.router)


# Substituir eventos deprecated por lifespan se necessitarmos lógica futura.


@app.get("/health", tags=["saude"])
async def health() -> dict:
    return envelope_resposta(True, {"status": "ok"})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):  # type: ignore[override]
    return JSONResponse(
        status_code=422,
        content=envelope_resposta(
            False,
            None,
            erro={
                "code": "erro_validacao",
                "detail": exc.errors(),
            },
            meta={"path": request.url.path},
        ),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):  # type: ignore[override]
    return JSONResponse(
        status_code=500,
        content=envelope_resposta(
            False,
            None,
            erro={
                "code": "erro_interno",
                "detail": "Ocorreu um erro interno.",
            },
            meta={"path": request.url.path},
        ),
    )
