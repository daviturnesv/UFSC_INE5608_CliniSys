from __future__ import annotations

from fastapi import FastAPI

from .database import engine, Base  # noqa: F401 (Base imported for potential runtime metadata introspection)
from .routers import auth, usuarios, pacientes

app = FastAPI(title="CliniSys-Escola API", version="0.1.0")

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(pacientes.router)


@app.on_event("startup")
async def startup() -> None:
    # Migrations are managed via Alembic (run `alembic upgrade head` externally).
    # No implicit metadata.create_all() here to avoid drift from migrations.
    return None


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
