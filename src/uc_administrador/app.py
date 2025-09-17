from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI

from .db.database import engine, Base, AsyncSessionLocal
from .core.config import settings
from .controllers import usuarios_controller, paciente_controller, auth_controller


@asynccontextmanager
async def lifespan(app: FastAPI):
    # migrações leves para bancos existentes (SQLite): adiciona colunas novas se faltarem
    async with engine.begin() as conn:
        # PRAGMA helpers
        async def _get_columns(table: str) -> set[str]:
            res = await conn.exec_driver_sql(f"PRAGMA table_info({table})")
            return {row[1] for row in res.fetchall()} if res is not None else set()

        # usuarios: cpf
        try:
            cols = await _get_columns("usuarios")
            if "cpf" not in cols:
                await conn.exec_driver_sql("ALTER TABLE usuarios ADD COLUMN cpf VARCHAR(14)")
                # garante unicidade via índice (permite múltiplos NULL segundo SQLite)
                await conn.exec_driver_sql("CREATE UNIQUE INDEX IF NOT EXISTS uq_usuarios_cpf ON usuarios (cpf)")
        except Exception:
            # best-effort; não falha start por erro de migração leve
            pass

        # perfil_professor: clinica_id
        try:
            cols = await _get_columns("perfil_professor")
            if "clinica_id" not in cols:
                await conn.exec_driver_sql("ALTER TABLE perfil_professor ADD COLUMN clinica_id INTEGER")
                await conn.exec_driver_sql(
                    "CREATE INDEX IF NOT EXISTS ix_perfil_professor_clinica_id ON perfil_professor (clinica_id)"
                )
        except Exception:
            pass

        # perfil_aluno: clinica_id (se ainda não existir)
        try:
            cols = await _get_columns("perfil_aluno")
            if "clinica_id" not in cols:
                await conn.exec_driver_sql("ALTER TABLE perfil_aluno ADD COLUMN clinica_id INTEGER")
                await conn.exec_driver_sql(
                    "CREATE INDEX IF NOT EXISTS ix_perfil_aluno_clinica_id ON perfil_aluno (clinica_id)"
                )
        except Exception:
            pass

        # cria tabelas novas que ainda não existam (ex: clinicas)
        await conn.run_sync(Base.metadata.create_all)
    # cria admin se não existir
    from .services.usuario_service import get_user_by_email, create_user
    from .models import PerfilUsuario
    async with AsyncSessionLocal() as session:
        # tenta achar pelo email configurado primeiro
        existing = await get_user_by_email(session, settings.admin_email)
        if not existing:
            # procura qualquer admin
            from sqlalchemy import select
            from .models import UsuarioSistema
            res = await session.execute(select(UsuarioSistema).where(UsuarioSistema.perfil == PerfilUsuario.admin))
            admin_user = res.scalar_one_or_none()
            if admin_user:
                # corrige email inválido rapidamente (sem ponto no domínio) atualizando para o email admin configurado
                if "@" in admin_user.email and "." not in admin_user.email.split("@")[-1]:
                    admin_user.email = settings.admin_email
                    await session.commit()
                # caso contrário, mantenha o admin existente válido
            else:
                # quando nenhum admin existe, cria um
                await create_user(
                    session,
                    nome="Administrador",
                    email=settings.admin_email,
                    senha=settings.admin_password,
                    perfil=PerfilUsuario.admin,
                )
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan, openapi_url="/uc-admin/openapi.json", docs_url="/uc-admin/docs")

app.include_router(auth_controller.router, prefix="/uc-admin")
app.include_router(usuarios_controller.router, prefix="/uc-admin")
app.include_router(paciente_controller.router, prefix="/uc-admin")
