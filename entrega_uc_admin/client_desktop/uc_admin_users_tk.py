from __future__ import annotations

import asyncio
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from src.uc_administrador.db.database import AsyncSessionLocal, engine, Base
from src.uc_administrador.models.usuario import (
    UsuarioSistema,
    PerfilUsuario,
    PerfilProfessor,
    PerfilRecepcionista,
    PerfilAluno,
)
from src.uc_administrador.models.clinica import Clinica
from src.uc_administrador.services.usuario_service import (
    create_user as svc_create_user,
    get_user_by_email as svc_get_user_by_email,
    get_profile_data as svc_get_profile_data,
    validate_password_policy,
)
from src.uc_administrador.core.security import hash_password
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError

NOT_FOUND_MSG = "Usuário não encontrado"
ERR_EMAIL_DUP = "Email já cadastrado"
ERR_CPF_DUP = "CPF já cadastrado"
ERR_CPF_FORMAT = "CPF deve conter 11 dígitos numéricos"
ERR_EMAIL_INVALID = "Email inválido"
ERR_PASSWORDS_MISMATCH = "As senhas não conferem"
ERR_MISSING_PREFIX = "Preencha: "
ERR_CLINICA_REQUIRED = "clinica_id é obrigatório para aluno/professor"
ERR_CLINICA_NOT_FOUND = "Clínica informada não existe"


def _is_valid_cpf(cpf: str | None) -> bool:
    return bool(cpf) and cpf.isdigit() and len(cpf) == 11


def _is_valid_email(email: str | None) -> bool:
    if not email or "@" not in email:
        return False
    domain = email.split("@")[-1]
    return "." in domain


def _map_integrity_error(e: Exception) -> None:
    msg = str(getattr(e, "orig", e))
    if ("cpf" in msg) or ("usuarios.cpf" in msg) or ("UNIQUE" in msg and "cpf" in msg):
        raise ValueError(ERR_CPF_DUP)
    if ("email" in msg) or ("usuarios.email" in msg) or ("UNIQUE" in msg and "email" in msg):
        raise ValueError(ERR_EMAIL_DUP)
    raise


async def _exists_other_with(session, column, value, exclude_id: int) -> bool:
    res = await session.execute(
        select(UsuarioSistema).where(column == value, UsuarioSistema.id != exclude_id)
    )
    return res.scalars().first() is not None


async def _validate_and_prepare_email(session, current_email: str, new_email: Optional[str], user_id: int) -> Optional[str]:
    if new_email is None:
        return None
    if not _is_valid_email(new_email):
        raise ValueError(ERR_EMAIL_INVALID)
    if new_email != current_email and await _exists_other_with(session, UsuarioSistema.email, new_email, user_id):
        raise ValueError(ERR_EMAIL_DUP)
    return new_email


async def _validate_and_prepare_cpf(session, current_cpf: str, new_cpf: Optional[str], user_id: int) -> Optional[str]:
    if new_cpf is None:
        return None
    if not _is_valid_cpf(new_cpf):
        raise ValueError(ERR_CPF_FORMAT)
    if new_cpf != (current_cpf or "") and await _exists_other_with(session, UsuarioSistema.cpf, new_cpf, user_id):
        raise ValueError(ERR_CPF_DUP)
    return new_cpf


async def init_db_and_seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # seed admin mínimo (não sobrescreve existente)
    from src.uc_administrador.core.config import settings
    async with AsyncSessionLocal() as session:
        existing = await svc_get_user_by_email(session, settings.admin_email)
        if not existing:
            await svc_create_user(
                session,
                nome="Administrador",
                email=settings.admin_email,
                senha=settings.admin_password,
                perfil=PerfilUsuario.admin,
                dados_perfil=None,
                cpf=getattr(settings, "admin_cpf", "00000000000"),
            )

        # seed clinica padrão se não houver nenhuma
        from sqlalchemy import select as _select
        res = await session.execute(_select(Clinica).limit(1))
        if res.scalars().first() is None:
            default = Clinica(codigo="CLIN-001", nome="Clínica Escola")
            session.add(default)
            await session.commit()


async def list_users() -> list[dict]:
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(UsuarioSistema).order_by(UsuarioSistema.id))
        items = []
        for u in res.scalars().all():
            d = {
                "id": u.id,
                "nome": u.nome,
                "email": u.email,
                "perfil": u.perfil.value,
                "cpf": u.cpf,
                "ativo": u.ativo,
            }
            pd = await svc_get_profile_data(session, u)
            if pd:
                d["perfil_dados"] = pd
            items.append(d)
        return items


async def list_clinicas() -> list[dict]:
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Clinica).order_by(Clinica.id))
        return [{"id": c.id, "codigo": c.codigo, "nome": c.nome} for c in res.scalars().all()]


async def create_user(nome: str, email: str, senha: str, perfil: str, cpf: str, clinica_id: Optional[int], extras: dict | None) -> dict:
    if not _is_valid_cpf(cpf):
        raise ValueError(ERR_CPF_FORMAT)
    validate_password_policy(senha)
    if not _is_valid_email(email):
        raise ValueError(ERR_EMAIL_INVALID)
    async with AsyncSessionLocal() as session:
        per = PerfilUsuario(perfil)
        dados_perfil = extras or {}
        if per in (PerfilUsuario.aluno, PerfilUsuario.professor):
            if clinica_id is None:
                raise ValueError(ERR_CLINICA_REQUIRED)
            if clinica_id:
                c = await session.get(Clinica, clinica_id)
                if not c:
                    raise ValueError(ERR_CLINICA_NOT_FOUND)
            dados_perfil["clinica_id"] = clinica_id

        # Pre-valida duplicidades amigavelmente
        if (await session.execute(select(UsuarioSistema).where(UsuarioSistema.email == email))).scalars().first():
            raise ValueError(ERR_EMAIL_DUP)
        if (await session.execute(select(UsuarioSistema).where(UsuarioSistema.cpf == cpf))).scalars().first():
            raise ValueError(ERR_CPF_DUP)

        try:
            u = await svc_create_user(
                session,
                nome=nome,
                email=email,
                senha=senha,
                perfil=per,
                dados_perfil=dados_perfil,
                cpf=cpf,
            )
            return {"id": u.id, "nome": u.nome, "email": u.email}
        except IntegrityError as e:
            _map_integrity_error(e)
            raise


async def update_user(
    user_id: int,
    nome: Optional[str] = None,
    email: Optional[str] = None,
    cpf: Optional[str] = None,
    perfil: Optional[str] = None,
    clinica_id: Optional[int] = None,
) -> None:
    async with AsyncSessionLocal() as session:
        u = await session.get(UsuarioSistema, user_id)
        if not u:
            raise ValueError(NOT_FOUND_MSG)
        if nome is not None:
            u.nome = nome
        upd_email = await _validate_and_prepare_email(session, u.email, email, user_id)
        if upd_email is not None:
            u.email = upd_email
        upd_cpf = await _validate_and_prepare_cpf(session, u.cpf or "", cpf, user_id)
        if upd_cpf is not None:
            u.cpf = upd_cpf
        new_perfil = PerfilUsuario(perfil) if perfil is not None else u.perfil
        perfil_changed = new_perfil != u.perfil
        if new_perfil in (PerfilUsuario.professor, PerfilUsuario.aluno):
            if clinica_id is not None:
                c = await session.get(Clinica, clinica_id)
                if not c:
                    raise ValueError(ERR_CLINICA_NOT_FOUND)
            elif perfil_changed:
                raise ValueError(ERR_CLINICA_REQUIRED)

        # Se for mudança de perfil, remove perfis antigos
        if perfil_changed:
            await session.execute(delete(PerfilProfessor).where(PerfilProfessor.user_id == user_id))
            await session.execute(delete(PerfilAluno).where(PerfilAluno.user_id == user_id))
            await session.execute(delete(PerfilRecepcionista).where(PerfilRecepcionista.user_id == user_id))
            u.perfil = new_perfil

        # Cria novo perfil específico se necessário
        if new_perfil == PerfilUsuario.professor:
            res = await session.execute(select(PerfilProfessor).where(PerfilProfessor.user_id == user_id))
            prof = res.scalar_one_or_none()
            if not prof:
                if clinica_id is None:
                    raise ValueError(ERR_CLINICA_REQUIRED)
                prof = PerfilProfessor(user_id=user_id, clinica_id=clinica_id)
                session.add(prof)
            else:
                if clinica_id is not None:
                    prof.clinica_id = clinica_id
        elif new_perfil == PerfilUsuario.aluno:
            res = await session.execute(select(PerfilAluno).where(PerfilAluno.user_id == user_id))
            alu = res.scalar_one_or_none()
            if not alu:
                if clinica_id is None:
                    raise ValueError(ERR_CLINICA_REQUIRED)
                alu = PerfilAluno(user_id=user_id, clinica_id=clinica_id)
                session.add(alu)
            else:
                if clinica_id is not None:
                    alu.clinica_id = clinica_id
        elif new_perfil == PerfilUsuario.recepcionista:
            res = await session.execute(select(PerfilRecepcionista).where(PerfilRecepcionista.user_id == user_id))
            rep = res.scalar_one_or_none()
            if not rep:
                session.add(PerfilRecepcionista(user_id=user_id))

        try:
            await session.commit()
        except IntegrityError as e:
            _map_integrity_error(e)


async def remove_user(user_id: int) -> None:
    async with AsyncSessionLocal() as session:
        u = await session.get(UsuarioSistema, user_id)
        if not u:
            raise ValueError(NOT_FOUND_MSG)
        await session.delete(u)
        await session.commit()


async def set_active(user_id: int, ativo: bool) -> None:
    async with AsyncSessionLocal() as session:
        stmt = (
            update(UsuarioSistema)
            .where(UsuarioSistema.id == user_id)
            .values(ativo=ativo)
        )
        res = await session.execute(stmt)
        await session.commit()
        if res.rowcount == 0:
            raise ValueError(NOT_FOUND_MSG)


async def change_password(user_id: int, nova: str) -> None:
    validate_password_policy(nova)
    async with AsyncSessionLocal() as session:
        u = await session.get(UsuarioSistema, user_id)
        if not u:
            raise ValueError(NOT_FOUND_MSG)
        u.senha_hash = hash_password(nova)
        await session.commit()


class CreateUserDialog(tk.Toplevel):
    def __init__(self, master: tk.Tk, clinicas: Optional[list[dict]] = None, initial: Optional[dict] = None, on_submit=None):
        super().__init__(master)
        self.title("Adicionar Novo Usuário")
        self.resizable(False, False)
        self.result: Optional[dict] = None
        self._on_submit = on_submit

        row = 0
        ttk.Label(self, text="Nome Completo").grid(row=row, column=0, sticky="e", padx=6, pady=4)
        self.var_nome = tk.StringVar()
        ttk.Entry(self, textvariable=self.var_nome, width=32).grid(row=row, column=1, sticky="w", padx=6, pady=4)
        row += 1

        ttk.Label(self, text="CPF").grid(row=row, column=0, sticky="e", padx=6, pady=4)
        self.var_cpf = tk.StringVar()
        ttk.Entry(self, textvariable=self.var_cpf, width=32).grid(row=row, column=1, sticky="w", padx=6, pady=4)
        self.err_cpf = ttk.Label(self, text="", foreground="red")
        self.err_cpf.grid(row=row, column=2, sticky="w")
        row += 1

        ttk.Label(self, text="Email").grid(row=row, column=0, sticky="e", padx=6, pady=4)
        self.var_email = tk.StringVar()
        ttk.Entry(self, textvariable=self.var_email, width=32).grid(row=row, column=1, sticky="w", padx=6, pady=4)
        self.err_email = ttk.Label(self, text="", foreground="red")
        self.err_email.grid(row=row, column=2, sticky="w")
        row += 1

        ttk.Label(self, text="Perfil").grid(row=row, column=0, sticky="e", padx=6, pady=4)
        self.var_perfil = tk.StringVar(value="admin")
        self.cmb_perfil = ttk.OptionMenu(
            self,
            self.var_perfil,
            "admin",
            "admin",
            "professor",
            "aluno",
            "recepcionista",
        )
        self.cmb_perfil.grid(row=row, column=1, sticky="w", padx=6, pady=4)
        try:
            self.var_perfil.trace_add("write", lambda *_: self.on_perfil_change(self.var_perfil.get()))
        except Exception:
            pass
        row += 1

        ttk.Label(self, text="Senha").grid(row=row, column=0, sticky="e", padx=6, pady=4)
        self.var_senha = tk.StringVar()
        ttk.Entry(self, textvariable=self.var_senha, show="*", width=32).grid(row=row, column=1, sticky="w", padx=6, pady=4)
        row += 1

        ttk.Label(self, text="Confirmar Senha").grid(row=row, column=0, sticky="e", padx=6, pady=4)
        self.var_confirma = tk.StringVar()
        ttk.Entry(self, textvariable=self.var_confirma, show="*", width=32).grid(row=row, column=1, sticky="w", padx=6, pady=4)
        row += 1

        self.lbl_clin = ttk.Label(self, text="Clinica ID (Aluno/Prof)")
        self.var_clinica = tk.StringVar()
        self.ent_clin = ttk.Entry(self, textvariable=self.var_clinica, width=32)
        self.lbl_clin.grid(row=row, column=0, sticky="e", padx=6, pady=4)
        self.ent_clin.grid(row=row, column=1, sticky="w", padx=6, pady=4)
        row += 1

        btns = ttk.Frame(self)
        btns.grid(row=row, column=0, columnspan=2, pady=8)
        ttk.Button(btns, text="Cancelar", command=self.destroy).grid(row=0, column=0, padx=4)
        ttk.Button(btns, text="Salvar Usuário", command=self.on_save).grid(row=0, column=1, padx=4)
        row += 1
        self.err_general = ttk.Label(self, text="", foreground="red")
        self.err_general.grid(row=row, column=0, columnspan=3, sticky="w")

        if clinicas and len(clinicas) == 1:
            self.var_clinica.set(str(clinicas[0]["id"]))
        if initial:
            self.var_nome.set(initial.get("nome", ""))
            self.var_email.set(initial.get("email", ""))
            self.var_cpf.set(initial.get("cpf", ""))
            self.var_perfil.set(initial.get("perfil", self.var_perfil.get()))
            cid = initial.get("clinica_id")
            if cid is not None:
                self.var_clinica.set(str(cid))

        self.on_perfil_change(self.var_perfil.get())
        self.grab_set()
        self.transient(master)

    def on_perfil_change(self, value: str):
        need = value in ("aluno", "professor")
        state = "normal" if need else "disabled"
        self.ent_clin.configure(state=state)
        self.lbl_clin.configure(state=state)

    def _clear_errors(self):
        if hasattr(self, "err_email"):
            self.err_email.config(text="")
        if hasattr(self, "err_cpf"):
            self.err_cpf.config(text="")
        if hasattr(self, "err_general"):
            self.err_general.config(text="")

    def _collect_form_data(self) -> dict:
        clin_raw = self.var_clinica.get().strip()
        return {
            "nome": self.var_nome.get().strip(),
            "cpf": self.var_cpf.get().strip(),
            "email": self.var_email.get().strip(),
            "perfil": self.var_perfil.get(),
            "senha": self.var_senha.get(),
            "confirma": self.var_confirma.get(),
            "clinica_id": int(clin_raw) if clin_raw else None,
        }

    def _validate_form(self, data: dict) -> None:
        missing = [lbl for lbl, key in (("Nome", "nome"), ("Email", "email"), ("CPF", "cpf"), ("Senha", "senha")) if not data.get(key)]
        if missing:
            raise ValueError(ERR_MISSING_PREFIX + ", ".join(missing))
        if data["senha"] != data.get("confirma", ""):
            raise ValueError(ERR_PASSWORDS_MISMATCH)
        if not _is_valid_email(data["email"]):
            raise ValueError(ERR_EMAIL_INVALID)
        if not _is_valid_cpf(data["cpf"]):
            raise ValueError(ERR_CPF_FORMAT)
        if data["perfil"] in ("aluno", "professor") and data.get("clinica_id") is None:
            raise ValueError(ERR_CLINICA_REQUIRED)

    def _apply_error_message(self, msg: str) -> None:
        if ERR_CPF_DUP in msg:
            self.err_cpf.config(text=ERR_CPF_DUP)
        elif ERR_EMAIL_DUP in msg:
            self.err_email.config(text=ERR_EMAIL_DUP)
        else:
            self.err_general.config(text=msg)

    def on_save(self):
        try:
            self._clear_errors()
            data = self._collect_form_data()
            self._validate_form(data)
            if callable(self._on_submit):
                try:
                    created_obj = self._on_submit({k: v for k, v in data.items() if k != "confirma"})
                    created: Optional[dict] = created_obj if isinstance(created_obj, dict) else None
                    self.result = created or {k: v for k, v in data.items() if k != "confirma"}
                    self.destroy()
                    return
                except Exception as ex:
                    self._apply_error_message(str(ex))
                    return
            else:
                self.result = {k: v for k, v in data.items() if k != "confirma"}
                self.destroy()
        except Exception as e:
            if hasattr(self, "err_general"):
                self.err_general.config(text=str(e))
            else:
                messagebox.showerror("Validação", str(e), parent=self)


class UsersApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("CliniSys - UC Admin (Tkinter)")
        self.geometry("980x520")
        self.resizable(True, True)

        # Esquerda: listagem
        left = ttk.Frame(self)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.listbox = tk.Listbox(left)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        # Direita: formulário
        right = ttk.Frame(self)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=8, pady=8)

        row = 0
        ttk.Label(right, text="ID").grid(row=row, column=0, sticky="e")
        self.var_id = tk.StringVar()
        ttk.Entry(right, textvariable=self.var_id, state="readonly", width=30).grid(row=row, column=1, sticky="w")
        row += 1

        ttk.Label(right, text="Nome").grid(row=row, column=0, sticky="e")
        self.var_nome = tk.StringVar()
        ttk.Entry(right, textvariable=self.var_nome, width=30).grid(row=row, column=1, sticky="w")
        row += 1

        ttk.Label(right, text="Email").grid(row=row, column=0, sticky="e")
        self.var_email = tk.StringVar()
        ttk.Entry(right, textvariable=self.var_email, width=30).grid(row=row, column=1, sticky="w")
        row += 1

        ttk.Label(right, text="CPF").grid(row=row, column=0, sticky="e")
        self.var_cpf = tk.StringVar()
        ttk.Entry(right, textvariable=self.var_cpf, width=30).grid(row=row, column=1, sticky="w")
        row += 1

        ttk.Label(right, text="Perfil").grid(row=row, column=0, sticky="e")
        self.var_perfil = tk.StringVar(value="admin")
        ttk.OptionMenu(right, self.var_perfil, "admin", "admin", "professor", "aluno", "recepcionista").grid(row=row, column=1, sticky="w")
        row += 1

        ttk.Label(right, text="Senha (criação)").grid(row=row, column=0, sticky="e")
        self.var_senha = tk.StringVar()
        ttk.Entry(right, textvariable=self.var_senha, show="*", width=30).grid(row=row, column=1, sticky="w")
        row += 1

        ttk.Label(right, text="Clinica ID (Aluno/Prof)").grid(row=row, column=0, sticky="e")
        self.var_clinica = tk.StringVar()
        self.ent_clinica = ttk.Entry(right, textvariable=self.var_clinica, width=30)
        self.ent_clinica.grid(row=row, column=1, sticky="w")
        row += 1

        ttk.Label(right, text="Nova Senha (alterar)").grid(row=row, column=0, sticky="e")
        self.var_nova_senha = tk.StringVar()
        ttk.Entry(right, textvariable=self.var_nova_senha, show="*", width=30).grid(row=row, column=1, sticky="w")
        row += 1

        # Filtros (para dar propósito ao botão Listar)
        ttk.Label(right, text="Filtro Perfil").grid(row=row, column=0, sticky="e")
        self.var_filtro_perfil = tk.StringVar(value="todos")
        ttk.OptionMenu(right, self.var_filtro_perfil, "todos", "todos", "admin", "professor", "aluno", "recepcionista").grid(row=row, column=1, sticky="w")
        row += 1
        self.var_filtro_ativos = tk.BooleanVar(value=True)
        ttk.Checkbutton(right, text="Somente ativos", variable=self.var_filtro_ativos).grid(row=row, column=1, sticky="w")
        row += 1

        # Botões
        btns = ttk.Frame(right)
        btns.grid(row=row, column=0, columnspan=2, pady=8)
        ttk.Button(btns, text="Aplicar Filtros", command=self.cmd_listar).grid(row=0, column=0, padx=3)
        ttk.Button(btns, text="Novo", command=self.cmd_novo).grid(row=0, column=1, padx=3)
        ttk.Button(btns, text="Atualizar Selecionado", command=self.cmd_atualizar).grid(row=0, column=2, padx=3)
        ttk.Button(btns, text="Remover", command=self.cmd_remover).grid(row=0, column=3, padx=3)
        ttk.Button(btns, text="Ativar", command=lambda: self.cmd_set_ativo(True)).grid(row=1, column=0, padx=3, pady=4)
        ttk.Button(btns, text="Desativar", command=lambda: self.cmd_set_ativo(False)).grid(row=1, column=1, padx=3, pady=4)
        ttk.Button(btns, text="Alterar Senha", command=self.cmd_alterar_senha).grid(row=1, column=2, padx=3, pady=4)

        # react to perfil changes (enable/disable clinica input)
        try:
            self.var_perfil.trace_add("write", lambda *_: self._on_perfil_change())
        except Exception:
            pass

        # Start
        self.after(50, self.bootstrap)

    def run_async(self, coro):
        """Run async code in a blocking way (simple MVP)."""
        return asyncio.run(coro)

    def bootstrap(self):
        try:
            self.run_async(init_db_and_seed())
            self.cmd_listar()
        except Exception as e:
            messagebox.showerror("Erro ao iniciar", str(e))

    def _on_perfil_change(self):
        p = self.var_perfil.get()
        need = p in ("aluno", "professor")
        state = "normal" if need else "disabled"
        try:
            self.ent_clinica.configure(state=state)
        except Exception:
            pass

    def on_select(self, _evt=None):
        idxs = self.listbox.curselection()
        if not idxs:
            return
        data = self.listbox.get(idxs[0])
        # formato: "[id] nome (perfil) - ativo"
        try:
            uid = int(data.split("]", 1)[0].lstrip("["))
        except Exception:
            return

    def cmd_listar(self):
        try:
            users = self.run_async(list_users())
            # aplicar filtros
            perfil = self.var_filtro_perfil.get()
            if perfil != "todos":
                users = [u for u in users if u.get("perfil") == perfil]
            if self.var_filtro_ativos.get():
                users = [u for u in users if u.get("ativo")]
            self.listbox.delete(0, tk.END)
            for u in users:
                label = f"[{u['id']}] {u['nome']} ({u['perfil']}) - {'ativo' if u['ativo'] else 'inativo'}"
                self.listbox.insert(tk.END, label)
        except Exception as e:
            messagebox.showerror("Erro ao listar", str(e))

    def _submit_create(self, data: dict):
        return self.run_async(create_user(
            data["nome"], data["email"], data["senha"], data["perfil"], data["cpf"], data["clinica_id"], None
        ))

    def cmd_novo(self):
        try:
            clinicas = self.run_async(list_clinicas())
        except Exception:
            clinicas = []
        dlg = CreateUserDialog(self, clinicas=clinicas, on_submit=self._submit_create)
        self.wait_window(dlg)
        if not dlg.result:
            return
        created = dlg.result
        self.cmd_listar()
        try:
            new_id = created.get("id") if isinstance(created, dict) else None
            if new_id:
                for i in range(self.listbox.size()):
                    if self.listbox.get(i).startswith(f"[{new_id}]"):
                        self.listbox.selection_clear(0, tk.END)
                        self.listbox.selection_set(i)
                        self.listbox.see(i)
                        break
            messagebox.showinfo("Sucesso", "Usuário criado")
        except Exception:
            pass

    def cmd_atualizar(self):
        try:
            if not self.var_id.get().strip().isdigit():
                messagebox.showwarning("Seleção necessária", "Selecione um usuário da lista")
                return
            uid = int(self.var_id.get())
            nome = self.var_nome.get().strip() or None
            email = self.var_email.get().strip() or None
            cpf = self.var_cpf.get().strip() or None
            perfil = self.var_perfil.get().strip() or None
            clin_raw = self.var_clinica.get().strip()
            clinica_id = int(clin_raw) if clin_raw else None
            self.run_async(update_user(uid, nome=nome, email=email, cpf=cpf, perfil=perfil, clinica_id=clinica_id))
            self.cmd_listar()
            messagebox.showinfo("Sucesso", "Usuário atualizado")
        except Exception as e:
            messagebox.showerror("Erro ao atualizar", str(e))

    def cmd_remover(self):
        try:
            if not self.var_id.get().strip().isdigit():
                messagebox.showwarning("Seleção necessária", "Selecione um usuário da lista")
                return
            uid = int(self.var_id.get())
            if messagebox.askyesno("Confirmação", "Remover usuário?"):
                self.run_async(remove_user(uid))
                self.cmd_listar()
        except Exception as e:
            messagebox.showerror("Erro ao remover", str(e))

    def cmd_set_ativo(self, ativo: bool):
        try:
            if not self.var_id.get().strip().isdigit():
                messagebox.showwarning("Seleção necessária", "Selecione um usuário da lista")
                return
            uid = int(self.var_id.get())
            self.run_async(set_active(uid, ativo))
            self.cmd_listar()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def cmd_alterar_senha(self):
        try:
            if not self.var_id.get().strip().isdigit():
                messagebox.showwarning("Seleção necessária", "Selecione um usuário da lista")
                return
            uid = int(self.var_id.get())
            nova = self.var_nova_senha.get()
            self.run_async(change_password(uid, nova))
            self.var_nova_senha.set("")
            messagebox.showinfo("Sucesso", "Senha alterada")
        except Exception as e:
            messagebox.showerror("Erro ao alterar senha", str(e))


def main():
    app = UsersApp()
    app.mainloop()


if __name__ == "__main__":
    main()
