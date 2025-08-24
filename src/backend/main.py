from __future__ import annotations

from fastapi import FastAPI

from .database import engine, Base
from .routers import auth, usuarios, pacientes

app = FastAPI(title="CliniSys-Escola API", version="0.1.0")

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(pacientes.router)


@app.on_event("startup")
async def startup() -> None:
    # Em produção usar migrações (Alembic). Aqui apenas para bootstrap inicial.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
