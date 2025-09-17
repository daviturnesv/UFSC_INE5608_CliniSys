from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from fastapi.responses import JSONResponse
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from ..db.database import get_db
from ..views.usuario_view import UsuarioCreate, Usuario, UsuarioUpdate, PerfilUsuario as PerfilSchema
from ..models import UsuarioSistema, PerfilUsuario
from ..services.usuario_service import create_user, get_user_by_email, validate_password_policy, get_profile_data
from ..views.envelope import envelope


router = APIRouter(prefix="/usuarios", tags=["usuarios"])
MSG_USUARIO_NAO_ENCONTRADO = "Usuário não encontrado"


@router.post("/", status_code=status.HTTP_201_CREATED)
async def criar_usuario(
    payload: UsuarioCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        existente = await get_user_by_email(db, payload.email)
        if existente:
            raise HTTPException(status_code=400, detail="Email já cadastrado")
        if payload.cpf:
            res_cpf = await db.execute(select(UsuarioSistema).where(UsuarioSistema.cpf == payload.cpf))
            if res_cpf.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="CPF já cadastrado")

        user = await create_user(
            db,
            nome=payload.nome,
            email=payload.email,
            senha=payload.senha,
            perfil=PerfilUsuario(payload.perfil.value),
            dados_perfil=payload.dados_perfil,
            cpf=payload.cpf,
        )
        data = Usuario.model_validate(user).model_dump()
        perfil_dados = await get_profile_data(db, user)
        if perfil_dados is not None:
            data["perfil_dados"] = perfil_dados
        return envelope(True, data)
    except HTTPException as e:
        detail = e.detail if isinstance(e.detail, str) else str(e.detail)
        return JSONResponse(status_code=e.status_code, content=envelope(False, None, erro=detail))
    except IntegrityError as e:
        await db.rollback()
        return JSONResponse(status_code=400, content=envelope(False, None, erro=f"Violação de unicidade (email/cpf). {e}"))
    except ValueError as e:
        return JSONResponse(status_code=400, content=envelope(False, None, erro=str(e)))
    except SQLAlchemyError as e:
        await db.rollback()
        return JSONResponse(status_code=500, content=envelope(False, None, erro=f"Erro interno ao criar usuário. {e}"))
    except Exception as e:
        await db.rollback()
        return JSONResponse(status_code=500, content=envelope(False, None, erro=f"Erro inesperado ao criar usuário. {e}"))


@router.get("/")
async def listar_usuarios(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    perfil: Optional[PerfilSchema] = Query(None),
    ativo: Optional[bool] = Query(None),
):
    try:
        base = select(UsuarioSistema)
        filtros = []
        if perfil is not None:
            filtros.append(UsuarioSistema.perfil == PerfilUsuario(perfil.value))
        if ativo is not None:
            filtros.append(UsuarioSistema.ativo == ativo)
        for f in filtros:
            base = base.where(f)

        total_stmt = select(func.count()).select_from(UsuarioSistema)
        for f in filtros:
            total_stmt = total_stmt.where(f)
        total = (await db.execute(total_stmt)).scalar_one()

        pagina_stmt = base.order_by(UsuarioSistema.id).offset(skip).limit(limit)
        res = await db.execute(pagina_stmt)
        registros = res.scalars().all()
        meta = {"total": total, "limit": limit, "skip": skip, "count": len(registros)}
        items = []
        for r in registros:
            d = Usuario.model_validate(r).model_dump()
            pd = await get_profile_data(db, r)
            if pd is not None:
                d["perfil_dados"] = pd
            items.append(d)
        return envelope(True, items, meta=meta)
    except SQLAlchemyError:
        return JSONResponse(status_code=500, content=envelope(False, None, erro="Erro interno ao listar usuários."))
    except Exception:
        return JSONResponse(status_code=500, content=envelope(False, None, erro="Erro inesperado ao listar usuários."))


@router.get("/{usuario_id}")
async def obter_usuario(
    usuario_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
):
    try:
        u = await db.get(UsuarioSistema, usuario_id)
        if not u:
            raise HTTPException(status_code=404, detail=MSG_USUARIO_NAO_ENCONTRADO)
        data = Usuario.model_validate(u).model_dump()
        pd = await get_profile_data(db, u)
        if pd is not None:
            data["perfil_dados"] = pd
        return envelope(True, data)
    except HTTPException as e:
        detail = e.detail if isinstance(e.detail, str) else str(e.detail)
        return JSONResponse(status_code=e.status_code, content=envelope(False, None, erro=detail))
    except SQLAlchemyError:
        return JSONResponse(status_code=500, content=envelope(False, None, erro="Erro interno ao obter usuário."))
    except Exception:
        return JSONResponse(status_code=500, content=envelope(False, None, erro="Erro inesperado ao obter usuário."))


async def _atualizar_usuario_impl(db: AsyncSession, usuario_id: int, payload: UsuarioUpdate) -> dict:
    alvo = await db.get(UsuarioSistema, usuario_id)
    if not alvo:
        raise HTTPException(status_code=404, detail=MSG_USUARIO_NAO_ENCONTRADO)

    dados = payload.model_dump(exclude_unset=True)
    novo_email = dados.get("email")
    novo_cpf = dados.get("cpf")
    if novo_email and novo_email != alvo.email:
        existente = await get_user_by_email(db, novo_email)
        if existente:
            raise HTTPException(status_code=400, detail="Email já cadastrado")
    # nota: simples checagem de cpf duplicado (se houver outro usuário com mesmo cpf)
    if novo_cpf and novo_cpf != (alvo.cpf or None):
        res = await db.execute(select(UsuarioSistema).where(UsuarioSistema.cpf == novo_cpf, UsuarioSistema.id != alvo.id))
        if res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="CPF já cadastrado")

    if "perfil" in dados:
        alvo.perfil = (
            PerfilUsuario(dados["perfil"]) if isinstance(dados["perfil"], str) else PerfilUsuario(dados["perfil"].value)
        )
    if "nome" in dados:
        alvo.nome = dados["nome"]
    if novo_email:
        alvo.email = novo_email
    if novo_cpf is not None:
        alvo.cpf = novo_cpf

    await db.commit()
    await db.refresh(alvo)
    data = Usuario.model_validate(alvo).model_dump()
    pd = await get_profile_data(db, alvo)
    if pd is not None:
        data["perfil_dados"] = pd
    return data


@router.put("/{usuario_id}")
async def atualizar_usuario(
    usuario_id: int = Path(..., gt=0),
    payload: UsuarioUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await _atualizar_usuario_impl(db, usuario_id, payload)
        return envelope(True, data)
    except HTTPException as e:
        await db.rollback()
        detail = e.detail if isinstance(e.detail, str) else str(e.detail)
        return JSONResponse(status_code=e.status_code, content=envelope(False, None, erro=detail))
    except IntegrityError:
        await db.rollback()
        return JSONResponse(status_code=400, content=envelope(False, None, erro="Violação de unicidade (email)."))
    except SQLAlchemyError:
        await db.rollback()
        return JSONResponse(status_code=500, content=envelope(False, None, erro="Erro interno ao atualizar usuário."))
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=envelope(False, None, erro="Erro inesperado ao atualizar usuário."))


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_usuario(
    usuario_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
):
    try:
        alvo = await db.get(UsuarioSistema, usuario_id)
        if not alvo:
            raise HTTPException(status_code=404, detail=MSG_USUARIO_NAO_ENCONTRADO)
        await db.delete(alvo)
        await db.commit()
        return envelope(True, None)
    except HTTPException as e:
        await db.rollback()
        detail = e.detail if isinstance(e.detail, str) else str(e.detail)
        return JSONResponse(status_code=e.status_code, content=envelope(False, None, erro=detail))
    except SQLAlchemyError:
        await db.rollback()
        return JSONResponse(status_code=500, content=envelope(False, None, erro="Erro interno ao remover usuário."))
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=envelope(False, None, erro="Erro inesperado ao remover usuário."))


async def atualizar_status_usuario(
    usuario_id: int,
    ativo: bool,
    db: AsyncSession,
):
    stmt = (
        update(UsuarioSistema)
        .where(UsuarioSistema.id == usuario_id)
        .values(ativo=ativo)
        .returning(UsuarioSistema)
    )
    res = await db.execute(stmt)
    row = res.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=MSG_USUARIO_NAO_ENCONTRADO)
    await db.commit()
    return row[0]


@router.patch("/{usuario_id}/ativar")
async def ativar_usuario(
    usuario_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
):
    try:
        u = await atualizar_status_usuario(usuario_id, True, db)
        data = Usuario.model_validate(u).model_dump()
        pd = await get_profile_data(db, u)
        if pd is not None:
            data["perfil_dados"] = pd
        return envelope(True, data)
    except HTTPException as e:
        await db.rollback()
        detail = e.detail if isinstance(e.detail, str) else str(e.detail)
        return JSONResponse(status_code=e.status_code, content=envelope(False, None, erro=detail))
    except SQLAlchemyError:
        await db.rollback()
        return JSONResponse(status_code=500, content=envelope(False, None, erro="Erro interno ao ativar usuário."))
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=envelope(False, None, erro="Erro inesperado ao ativar usuário."))


@router.patch("/{usuario_id}/senha")
async def alterar_senha_usuario(
    usuario_id: int = Path(..., gt=0),
    payload: dict = Body(..., example={"nova_senha": "NovaSenha123"}),
    db: AsyncSession = Depends(get_db),
):
    try:
        alvo = await db.get(UsuarioSistema, usuario_id)
        if not alvo:
            raise HTTPException(status_code=404, detail=MSG_USUARIO_NAO_ENCONTRADO)

        nova = payload.get("nova_senha")
        if not nova:
            raise HTTPException(status_code=400, detail="Campo 'nova_senha' é obrigatório")
        try:
            validate_password_policy(nova)
        except ValueError as e:
            return JSONResponse(status_code=400, content=envelope(False, None, erro=str(e)))

        from ..core.security import hash_password

        alvo.senha_hash = hash_password(nova)
        await db.commit()
        await db.refresh(alvo)
        data = Usuario.model_validate(alvo).model_dump()
        pd = await get_profile_data(db, alvo)
        if pd is not None:
            data["perfil_dados"] = pd
        return envelope(True, data)
    except HTTPException as e:
        await db.rollback()
        detail = e.detail if isinstance(e.detail, str) else str(e.detail)
        return JSONResponse(status_code=e.status_code, content=envelope(False, None, erro=detail))
    except SQLAlchemyError:
        await db.rollback()
        return JSONResponse(status_code=500, content=envelope(False, None, erro="Erro interno ao alterar senha."))
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=envelope(False, None, erro="Erro inesperado ao alterar senha."))


@router.patch("/{usuario_id}/desativar")
async def desativar_usuario(
    usuario_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
):
    try:
        u = await atualizar_status_usuario(usuario_id, False, db)
        data = Usuario.model_validate(u).model_dump()
        pd = await get_profile_data(db, u)
        if pd is not None:
            data["perfil_dados"] = pd
        return envelope(True, data)
    except HTTPException as e:
        await db.rollback()
        detail = e.detail if isinstance(e.detail, str) else str(e.detail)
        return JSONResponse(status_code=e.status_code, content=envelope(False, None, erro=detail))
    except SQLAlchemyError:
        await db.rollback()
        return JSONResponse(status_code=500, content=envelope(False, None, erro="Erro interno ao desativar usuário."))
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=envelope(False, None, erro="Erro inesperado ao desativar usuário."))
