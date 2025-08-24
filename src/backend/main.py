from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
import time

from .database import engine, Base  # noqa: F401 (Base imported for potential runtime metadata introspection)
from .routers import auth, usuarios, pacientes

API_TITLE = "CliniSys-Escola API"
API_VERSION = "0.1.0"


def response_envelope(success: bool, data=None, error: dict | None = None, meta: dict | None = None):
    return {"success": success, "data": data, "error": error, "meta": meta or {}}


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:  # noqa: BLE001
            # Minimal log context; handlers will format final response
            print(f"Unhandled error during request timing: {exc}")
            raise
        duration = (time.perf_counter() - start) * 1000
        if hasattr(response, "media_type") and response.media_type == "application/json":
            try:
                body = b"".join([segment async for segment in response.body_iterator])  # type: ignore[attr-defined]
                # Reconstruct response body
                from json import loads, dumps

                payload = loads(body or b"null")
                if isinstance(payload, dict) and "success" in payload:
                    payload.setdefault("meta", {})["duration_ms"] = round(duration, 2)
                    new_body = dumps(payload).encode()
                    response.body_iterator = iter([new_body])  # type: ignore[assignment]
                    response.headers["content-length"] = str(len(new_body))
            except Exception:
                pass
        return response


app = FastAPI(title=API_TITLE, version=API_VERSION)
app.add_middleware(TimingMiddleware)

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(pacientes.router)


@app.on_event("startup")
async def startup() -> None:
    # Migrations are managed via Alembic (run `alembic upgrade head` externally).
    # No implicit metadata.create_all() here to avoid drift from migrations.
    return None


@app.get("/health", tags=["health"])
async def health() -> dict:
    return response_envelope(True, {"status": "ok"})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):  # type: ignore[override]
    return JSONResponse(
        status_code=422,
        content=response_envelope(
            False,
            None,
            error={
                "code": "validation_error",
                "detail": exc.errors(),
            },
            meta={"path": request.url.path},
        ),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):  # type: ignore[override]
    return JSONResponse(
        status_code=500,
        content=response_envelope(
            False,
            None,
            error={
                "code": "internal_error",
                "detail": "Ocorreu um erro interno.",
            },
            meta={"path": request.url.path},
        ),
    )
