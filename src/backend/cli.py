from __future__ import annotations
import asyncio
import typer
from typing import Optional
from .database import get_database_url, Base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from .models import UsuarioSistema, PerfilUsuario
from .core.security import hash_password
from .core.config import get_settings

app_cli = typer.Typer(help="Ferramentas de linha de comando para manutenção/seed.")


async def _seed_admin(email: str, senha: str) -> bool:
    engine = create_async_engine(get_database_url(), future=True, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sess_factory = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    async with sess_factory() as session:
        from sqlalchemy import select
        res = await session.execute(select(UsuarioSistema).where(UsuarioSistema.email == email))
        existente = res.scalar_one_or_none()
        if existente:
            return False
        novo = UsuarioSistema(
            nome="Administrador",
            email=email,
            senha_hash=hash_password(senha),
            perfil=PerfilUsuario.admin,
            ativo=True,
        )
        session.add(novo)
        await session.commit()
        return True


@app_cli.command("seed-admin")
def seed_admin(
    email: Optional[str] = typer.Option(None, help="Email do admin"),
    senha: Optional[str] = typer.Option(None, help="Senha do admin"),
):
    """Cria usuário admin inicial se não existir."""
    settings = get_settings()
    email_final = email or settings.seed_admin_email or "admin@exemplo.com"
    senha_final = senha or settings.seed_admin_senha or "admin123"
    criado = asyncio.run(_seed_admin(email_final, senha_final))
    msg = "Admin criado" if criado else "Admin já existia"
    typer.echo(msg + f" ({email_final})")


@app_cli.command("auto-seed")
def auto_seed():
    """Executa seed se variáveis APP_SEED_CRIAR=True."""
    s = get_settings()
    if not s.seed_criar:
        typer.echo("Flag seed_criar desabilitada")
        raise typer.Exit(code=0)
    email = s.seed_admin_email or "admin@exemplo.com"
    senha = s.seed_admin_senha or "admin123"
    criado = asyncio.run(_seed_admin(email, senha))
    typer.echo(("Admin criado" if criado else "Admin já existia") + f" ({email})")


if __name__ == "__main__":  # pragma: no cover
    app_cli()
