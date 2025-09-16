from __future__ import annotations
import asyncio
import typer
from typing import Optional
from .database import get_database_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from .models import UsuarioSistema, PerfilUsuario
from .core.security import hash_password
from .core.config import get_settings

app_cli = typer.Typer(help="Ferramentas de linha de comando para manutenção/seed.")


async def _seed_admin(email: str, senha: str) -> bool:
    engine = create_async_engine(get_database_url(), future=True, echo=False)
    # Assume que as migrações alembic já foram aplicadas. Não criar schema aqui.
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


async def _seed_usuario_generico(nome: str, email: str, senha: str, perfil: PerfilUsuario, ativo: bool = True) -> bool:
    engine = create_async_engine(get_database_url(), future=True, echo=False)
    sess_factory = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    async with sess_factory() as session:
        from sqlalchemy import select
        res = await session.execute(select(UsuarioSistema).where(UsuarioSistema.email == email))
        existente = res.scalar_one_or_none()
        if existente:
            return False
        novo = UsuarioSistema(
            nome=nome,
            email=email,
            senha_hash=hash_password(senha),
            perfil=perfil,
            ativo=ativo,
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


@app_cli.command("seed-usuario")
def seed_usuario(
    nome: str = typer.Option(..., help="Nome do usuário"),
    email: str = typer.Option(..., help="Email do usuário"),
    senha: str = typer.Option(..., help="Senha do usuário"),
    perfil: PerfilUsuario = typer.Option(PerfilUsuario.recepcionista, help="Perfil do usuário"),
    ativo: bool = typer.Option(True, help="Usuário ativo"),
):
    """Cria um usuário com perfil especificado (ex.: recepcionista, aluno)."""
    criado = asyncio.run(_seed_usuario_generico(nome, email, senha, perfil, ativo))
    typer.echo(("Usuário criado" if criado else "Usuário já existia") + f" ({email}, perfil={perfil.name})")


if __name__ == "__main__":  # pragma: no cover
    app_cli()
