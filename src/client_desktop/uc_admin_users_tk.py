from __future__ import annotations

import asyncio
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from src.backend.db.database import AsyncSessionLocal, engine, Base
from src.backend.models.usuario import (
    UsuarioSistema,
    PerfilUsuario,
    PerfilProfessor,
    PerfilRecepcionista,
    PerfilAluno,
)
from src.backend.models.clinica import Clinica
from src.backend.controllers.usuario_service import (
    create_user as svc_create_user,
    get_user_by_email as svc_get_user_by_email,
    get_profile_data as svc_get_profile_data,
    validate_password_policy,
)
from src.backend.core.security import hash_password
from src.client_desktop.user_profile import UserProfileDialog
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


def _normalize_cpf(cpf: str | None) -> str | None:
    """Remove pontos e hífens do CPF, mantendo apenas números"""
    if not cpf:
        return None
    return ''.join(filter(str.isdigit, cpf))


def _is_valid_cpf(cpf: str | None) -> bool:
    """Valida CPF aceitando formato com ou sem pontos e hífens"""
    if not cpf:
        return False
    normalized = _normalize_cpf(cpf)
    return bool(normalized) and len(normalized) == 11


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
    
    # Normalizar CPF (remover pontos e hífens)
    new_cpf_normalizado = _normalize_cpf(new_cpf)
    current_cpf_normalizado = _normalize_cpf(current_cpf) or ""
    
    if new_cpf_normalizado != current_cpf_normalizado and await _exists_other_with(session, UsuarioSistema.cpf, new_cpf_normalizado, user_id):
        raise ValueError(ERR_CPF_DUP)
    return new_cpf_normalizado


async def init_db_and_seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # seed admin mínimo (não sobrescreve existente)
    from src.backend.core.config import settings
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
                "clinica_id": None,  # Será preenchido abaixo se aplicável
            }
            
            # Buscar clinica_id dos perfis específicos
            pd = await svc_get_profile_data(session, u)
            if pd and hasattr(pd, 'clinica_id'):
                d["clinica_id"] = pd.clinica_id
            
            if pd:
                d["perfil_dados"] = pd
            items.append(d)
        return items


async def get_user_detail(user_id: int) -> dict:
    """Busca detalhes completos de um usuário específico"""
    async with AsyncSessionLocal() as session:
        user = await session.get(UsuarioSistema, user_id)
        if not user:
            raise ValueError("Usuário não encontrado")
        
        clinica_id = None
        telefone_perfil = None
        
        # Buscar dados dos perfis específicos
        pd = await svc_get_profile_data(session, user)
        if pd:
            # Extrair clinica_id se disponível
            if "clinica" in pd and isinstance(pd["clinica"], dict):
                clinica_id = pd["clinica"]["id"]
            elif "clinica_id" in pd:
                clinica_id = pd["clinica_id"]
            
            # Extrair telefone do perfil se disponível (alunos e recepcionistas)
            if "telefone" in pd:
                telefone_perfil = pd["telefone"]
        
        return {
            "id": user.id,
            "nome": user.nome,
            "email": user.email,
            "cpf": user.cpf or "",
            "telefone": user.telefone or "",  # Telefone geral do usuário
            "telefone_perfil": telefone_perfil,  # Telefone específico do perfil
            "perfil": user.perfil.value,
            "ativo": user.ativo,
            "clinica_id": clinica_id,
        }


async def list_clinicas() -> list[dict]:
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Clinica).order_by(Clinica.id))
        return [{"id": c.id, "codigo": c.codigo, "nome": c.nome} for c in res.scalars().all()]


async def create_user(nome: str, email: str, senha: str, perfil: str, cpf: str, clinica_id: Optional[int], telefone: Optional[str] = None, extras: dict | None = None) -> dict:
    if not _is_valid_cpf(cpf):
        raise ValueError(ERR_CPF_FORMAT)
    
    # Normalizar CPF (remover pontos e hífens)
    cpf_normalizado = _normalize_cpf(cpf)
    
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
        if (await session.execute(select(UsuarioSistema).where(UsuarioSistema.cpf == cpf_normalizado))).scalars().first():
            raise ValueError(ERR_CPF_DUP)

        try:
            # Criar o usuário base
            u = UsuarioSistema(
                nome=nome,
                email=email,
                senha_hash=hash_password(senha),
                perfil=per,
                cpf=cpf_normalizado,
                telefone=telefone,  # Incluir telefone geral
            )
            session.add(u)
            await session.flush()  # Para obter o ID
            
            # Criar perfil específico se necessário
            if per == PerfilUsuario.professor:
                perfil_prof = PerfilProfessor(
                    user_id=u.id,
                    especialidade=dados_perfil.get("especialidade"),
                    clinica_id=dados_perfil.get("clinica_id"),
                )
                session.add(perfil_prof)
            elif per == PerfilUsuario.aluno:
                perfil_aluno = PerfilAluno(
                    user_id=u.id,
                    matricula=dados_perfil.get("matricula"),
                    telefone=dados_perfil.get("telefone"),
                    clinica_id=dados_perfil.get("clinica_id"),
                )
                session.add(perfil_aluno)
            elif per == PerfilUsuario.recepcionista:
                perfil_recep = PerfilRecepcionista(
                    user_id=u.id,
                    telefone=dados_perfil.get("telefone")
                )
                session.add(perfil_recep)
            
            await session.commit()
            await session.refresh(u)
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

        # Criar todos os StringVar primeiro
        self.var_nome = tk.StringVar(self)
        self.var_cpf = tk.StringVar(self)
        self.var_email = tk.StringVar(self)
        self.var_perfil = tk.StringVar(self, value="admin")
        self.var_senha = tk.StringVar(self)
        self.var_confirma = tk.StringVar(self)
        self.var_clinica = tk.StringVar(self)

        row = 0
        ttk.Label(self, text="Nome Completo").grid(row=row, column=0, sticky="e", padx=6, pady=4)
        self.entry_nome = ttk.Entry(self, textvariable=self.var_nome, width=32)
        self.entry_nome.grid(row=row, column=1, sticky="w", padx=6, pady=4)
        row += 1

        ttk.Label(self, text="CPF").grid(row=row, column=0, sticky="e", padx=6, pady=4)
        self.entry_cpf = ttk.Entry(self, textvariable=self.var_cpf, width=32)
        self.entry_cpf.grid(row=row, column=1, sticky="w", padx=6, pady=4)
        self.entry_cpf.grid(row=row, column=1, sticky="w", padx=6, pady=4)
        self.err_cpf = ttk.Label(self, text="", foreground="red")
        self.err_cpf.grid(row=row, column=2, sticky="w")
        row += 1

        ttk.Label(self, text="Email").grid(row=row, column=0, sticky="e", padx=6, pady=4)
        self.entry_email = ttk.Entry(self, textvariable=self.var_email, width=32)
        self.entry_email.grid(row=row, column=1, sticky="w", padx=6, pady=4)
        self.err_email = ttk.Label(self, text="", foreground="red")
        self.err_email.grid(row=row, column=2, sticky="w")
        row += 1

        ttk.Label(self, text="Telefone (opcional)").grid(row=row, column=0, sticky="e", padx=6, pady=4)
        self.var_telefone = tk.StringVar(self)
        self.entry_telefone = ttk.Entry(self, textvariable=self.var_telefone, width=32)
        self.entry_telefone.grid(row=row, column=1, sticky="w", padx=6, pady=4)
        row += 1

        ttk.Label(self, text="Perfil").grid(row=row, column=0, sticky="e", padx=6, pady=4)
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
        self.entry_senha = ttk.Entry(self, textvariable=self.var_senha, show="*", width=32)
        self.entry_senha.grid(row=row, column=1, sticky="w", padx=6, pady=4)
        row += 1

        ttk.Label(self, text="Confirmar Senha").grid(row=row, column=0, sticky="e", padx=6, pady=4)
        self.entry_confirma = ttk.Entry(self, textvariable=self.var_confirma, show="*", width=32)
        self.entry_confirma.grid(row=row, column=1, sticky="w", padx=6, pady=4)
        row += 1

        self.lbl_clin = ttk.Label(self, text="Clínica (Aluno/Prof)")
        self.cmb_clin = ttk.Combobox(self, textvariable=self.var_clinica, state="readonly", width=29)
        
        # Preparar opções do combobox de clínicas
        clinicas_options = [""]  # Opção vazia
        if clinicas:
            for clinica in clinicas:
                option = f"{clinica['id']} - {clinica['nome']}"
                clinicas_options.append(option)
        self.cmb_clin.config(values=clinicas_options)
        
        self.lbl_clin.grid(row=row, column=0, sticky="e", padx=6, pady=4)
        self.cmb_clin.grid(row=row, column=1, sticky="w", padx=6, pady=4)
        row += 1

        btns = ttk.Frame(self)
        btns.grid(row=row, column=0, columnspan=2, pady=8)
        ttk.Button(btns, text="Cancelar", command=self.destroy).grid(row=0, column=0, padx=4)
        ttk.Button(btns, text="Salvar Usuário", command=self.on_save).grid(row=0, column=1, padx=4)
        row += 1

        # Label de erro geral
        self.err_general = ttk.Label(self, text="", foreground="red", wraplength=400)
        self.err_general.grid(row=row, column=0, columnspan=3, sticky="w", padx=6, pady=4)
        row += 1

        if clinicas and len(clinicas) == 1:
            # Se há apenas uma clínica, selecioná-la automaticamente
            self.var_clinica.set(f"{clinicas[0]['id']} - {clinicas[0]['nome']}")
        if initial:
            self.var_nome.set(initial.get("nome", ""))
            self.var_email.set(initial.get("email", ""))
            self.var_cpf.set(initial.get("cpf", ""))
            self.var_perfil.set(initial.get("perfil", self.var_perfil.get()))
            cid = initial.get("clinica_id")
            if cid is not None and clinicas:
                # Encontrar a clínica correspondente
                for clinica in clinicas:
                    if clinica['id'] == cid:
                        self.var_clinica.set(f"{clinica['id']} - {clinica['nome']}")
                        break

        self.on_perfil_change(self.var_perfil.get())
        self.grab_set()
        self.transient(master)

    def on_perfil_change(self, value: str):
        need = value in ("aluno", "professor")
        state = "readonly" if need else "disabled"
        self.cmb_clin.configure(state=state)
        self.lbl_clin.configure(state="normal" if need else "disabled")

    def _clear_errors(self):
        if hasattr(self, "err_email"):
            self.err_email.config(text="")
        if hasattr(self, "err_cpf"):
            self.err_cpf.config(text="")
        if hasattr(self, "err_general"):
            self.err_general.config(text="")

    def get_clinica_id_from_selection(self, selection: str) -> Optional[int]:
        """Extrai o ID da clínica a partir da seleção do combobox"""
        if not selection or not selection.strip():
            return None
        try:
            return int(selection.split(" - ")[0])
        except (ValueError, IndexError):
            return None

    def _collect_form_data(self) -> dict:
        clinica_id = self.get_clinica_id_from_selection(self.var_clinica.get())
        telefone = self.var_telefone.get().strip() if hasattr(self, 'var_telefone') else ""
        data = {
            "nome": self.var_nome.get().strip(),
            "cpf": self.var_cpf.get().strip(),
            "email": self.var_email.get().strip(),
            "telefone": telefone if telefone else None,
            "perfil": self.var_perfil.get(),
            "senha": self.var_senha.get(),
            "confirma": self.var_confirma.get(),
            "clinica_id": clinica_id,
        }
        return data

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
            print(f"Dados coletados: {data}")  # Debug
            
            self._validate_form(data)
            
            if callable(self._on_submit):
                try:
                    print("Chamando função de submissão...")  # Debug
                    created_obj = self._on_submit({k: v for k, v in data.items() if k != "confirma"})
                    created: Optional[dict] = created_obj if isinstance(created_obj, dict) else None
                    self.result = created or {k: v for k, v in data.items() if k != "confirma"}
                    print(f"Usuário criado com sucesso: {self.result}")  # Debug
                    self.destroy()
                    return
                except Exception as ex:
                    print(f"Erro na submissão: {ex}")  # Debug
                    self._apply_error_message(str(ex))
                    return
            else:
                self.result = {k: v for k, v in data.items() if k != "confirma"}
                self.destroy()
        except Exception as e:
            print(f"Erro na validação: {e}")  # Debug
            if hasattr(self, "err_general"):
                self.err_general.config(text=str(e))
            else:
                messagebox.showerror("Validação", str(e), parent=self)


class UsersApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("CliniSys - Gerenciamento de Usuários")
        self.geometry("800x600")
        self.resizable(True, True)
        
        # Variáveis de estado
        self.users_data = []
        self.clinicas_data = []  # Lista de clínicas disponíveis
        self.selected_user = None
        self.edit_mode = False  # Controla se está no modo de edição
        
        # Criar interface principal
        self._create_main_interface()
        
        # Inicializar
        self.after(50, self.bootstrap)

    def _create_main_interface(self):
        """Cria a interface principal minimalista"""
        # Container principal
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(title_frame, text="Gerenciamento de Usuários", font=("Arial", 16, "bold")).pack()
        
        # Botões principais
        self.buttons_frame = ttk.Frame(main_frame)
        self.buttons_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.btn_show_users = ttk.Button(self.buttons_frame, text="📋 Mostrar Lista de Usuários", 
                                        command=self.toggle_users_list)
        self.btn_show_users.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_new_user = ttk.Button(self.buttons_frame, text="➕ Novo Usuário", 
                                      command=self.cmd_novo)
        self.btn_new_user.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_refresh = ttk.Button(self.buttons_frame, text="🔄 Atualizar", 
                                     command=self.cmd_listar)
        self.btn_refresh.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_my_profile = ttk.Button(self.buttons_frame, text="👤 Meu Perfil", 
                                        command=self.cmd_my_profile)
        self.btn_my_profile.pack(side=tk.LEFT)
        
        # Container para lista de usuários (inicialmente oculto)
        self.users_container = ttk.LabelFrame(main_frame, text="Lista de Usuários")
        self.users_container.pack_forget()  # Inicialmente oculto
        
        # Frame para filtros
        filters_frame = ttk.Frame(self.users_container)
        filters_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(filters_frame, text="Filtrar por Perfil:").pack(side=tk.LEFT)
        self.var_filtro_perfil = tk.StringVar(value="todos")
        self.cmb_filtro = ttk.Combobox(filters_frame, textvariable=self.var_filtro_perfil, 
                                      values=["todos", "admin", "professor", "aluno", "recepcionista"],
                                      state="readonly", width=15)
        self.cmb_filtro.pack(side=tk.LEFT, padx=(5, 10))
        self.cmb_filtro.set("todos")  # Garantir valor inicial
        
        self.var_filtro_ativos = tk.BooleanVar(value=True)
        ttk.Checkbutton(filters_frame, text="Apenas ativos", 
                       variable=self.var_filtro_ativos).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(filters_frame, text="Aplicar Filtros", 
                  command=self.apply_filters).pack(side=tk.LEFT)
        
        # Lista de usuários
        list_frame = ttk.Frame(self.users_container)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.listbox = tk.Listbox(list_frame, height=8)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        
        # Container para detalhes do usuário (inicialmente oculto)
        self.details_container = ttk.LabelFrame(main_frame, text="Detalhes do Usuário")
        self.details_container.pack_forget()  # Inicialmente oculto
        
        # Variáveis para os campos
        self.var_id = tk.StringVar()
        self.var_nome = tk.StringVar()
        self.var_email = tk.StringVar()
        self.var_cpf = tk.StringVar()
        self.var_perfil = tk.StringVar()
        self.var_clinica = tk.StringVar()
        self.var_nova_senha = tk.StringVar()
        
        # Campos específicos do perfil (inicializados como ocultos)
        self.profile_fields = {}
        
        self._create_details_form()
        
        # Estado da interface
        self.users_list_visible = False
        self.details_visible = False

    def _create_profile_specific_fields(self, parent, start_row):
        """Cria campos específicos do perfil que são mostrados/ocultos conforme necessário"""
        # Campos do professor
        self.profile_fields['professor'] = {}
        self.profile_fields['professor']['especialidade_label'] = ttk.Label(parent, text="Especialidade:")
        self.profile_fields['professor']['especialidade_var'] = tk.StringVar()
        self.profile_fields['professor']['especialidade_entry'] = ttk.Entry(
            parent, textvariable=self.profile_fields['professor']['especialidade_var'], 
            state="readonly", width=30
        )
        
        # Campos do recepcionista
        self.profile_fields['recepcionista'] = {}
        self.profile_fields['recepcionista']['telefone_label'] = ttk.Label(parent, text="Telefone/Ramal:")
        self.profile_fields['recepcionista']['telefone_var'] = tk.StringVar()
        self.profile_fields['recepcionista']['telefone_entry'] = ttk.Entry(
            parent, textvariable=self.profile_fields['recepcionista']['telefone_var'], 
            state="readonly", width=30
        )
        
        # Campos do aluno
        self.profile_fields['aluno'] = {}
        self.profile_fields['aluno']['matricula_label'] = ttk.Label(parent, text="Matrícula:")
        self.profile_fields['aluno']['matricula_var'] = tk.StringVar()
        self.profile_fields['aluno']['matricula_entry'] = ttk.Entry(
            parent, textvariable=self.profile_fields['aluno']['matricula_var'], 
            state="readonly", width=30
        )
        
        self.profile_fields['aluno']['telefone_label'] = ttk.Label(parent, text="Telefone Acadêmico:")
        self.profile_fields['aluno']['telefone_var'] = tk.StringVar()
        self.profile_fields['aluno']['telefone_entry'] = ttk.Entry(
            parent, textvariable=self.profile_fields['aluno']['telefone_var'], 
            state="readonly", width=30
        )
        
        # Armazenar informações de posicionamento
        self.profile_start_row = start_row

    def _show_profile_fields(self, perfil):
        """Mostra os campos específicos do perfil selecionado"""
        # Esconder todos os campos primeiro
        for profile_type, fields in self.profile_fields.items():
            for widget_name, widget in fields.items():
                if hasattr(widget, 'grid_remove'):
                    widget.grid_remove()
        
        # Mostrar campos do perfil atual
        if perfil in self.profile_fields:
            row = self.profile_start_row
            fields = self.profile_fields[perfil]
            
            if perfil == 'professor':
                fields['especialidade_label'].grid(row=row, column=0, sticky="e", padx=5, pady=5)
                fields['especialidade_entry'].grid(row=row, column=1, sticky="w", padx=5)
            elif perfil == 'recepcionista':
                fields['telefone_label'].grid(row=row, column=0, sticky="e", padx=5, pady=5)
                fields['telefone_entry'].grid(row=row, column=1, sticky="w", padx=5)
            elif perfil == 'aluno':
                fields['matricula_label'].grid(row=row, column=0, sticky="e", padx=5, pady=5)
                fields['matricula_entry'].grid(row=row, column=1, sticky="w", padx=5)
                row += 1
                fields['telefone_label'].grid(row=row, column=0, sticky="e", padx=5, pady=5)
                fields['telefone_entry'].grid(row=row, column=1, sticky="w", padx=5)

    def _create_details_form(self):
        """Cria o formulário de detalhes do usuário"""
        details_frame = ttk.Frame(self.details_container)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Campos de informação (inicialmente read-only)
        row = 0
        ttk.Label(details_frame, text="ID:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        self.entry_id = ttk.Entry(details_frame, textvariable=self.var_id, state="readonly", width=30)
        self.entry_id.grid(row=row, column=1, sticky="w", padx=5)
        row += 1
        
        ttk.Label(details_frame, text="Nome:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        self.entry_nome = ttk.Entry(details_frame, textvariable=self.var_nome, state="readonly", width=30)
        self.entry_nome.grid(row=row, column=1, sticky="w", padx=5)
        row += 1
        
        ttk.Label(details_frame, text="Email:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        self.entry_email = ttk.Entry(details_frame, textvariable=self.var_email, state="readonly", width=30)
        self.entry_email.grid(row=row, column=1, sticky="w", padx=5)
        row += 1
        
        ttk.Label(details_frame, text="CPF:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        self.entry_cpf = ttk.Entry(details_frame, textvariable=self.var_cpf, state="readonly", width=30)
        self.entry_cpf.grid(row=row, column=1, sticky="w", padx=5)
        row += 1
        
        ttk.Label(details_frame, text="Telefone:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        self.var_telefone = tk.StringVar()
        self.entry_telefone = ttk.Entry(details_frame, textvariable=self.var_telefone, state="readonly", width=30)
        self.entry_telefone.grid(row=row, column=1, sticky="w", padx=5)
        row += 1
        
        ttk.Label(details_frame, text="Perfil:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        self.cmb_perfil = ttk.Combobox(details_frame, textvariable=self.var_perfil,
                                      values=["admin", "professor", "aluno", "recepcionista"],
                                      state="readonly", width=27)
        self.cmb_perfil.grid(row=row, column=1, sticky="w", padx=5)
        row += 1
        
        ttk.Label(details_frame, text="Clínica:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        self.cmb_clinica = ttk.Combobox(details_frame, textvariable=self.var_clinica,
                                       state="readonly", width=27)
        self.cmb_clinica.grid(row=row, column=1, sticky="w", padx=5)
        row += 1
        
        # Campos específicos do perfil (condicionais)
        self._create_profile_specific_fields(details_frame, row)
        row += 3  # Reservar espaço para campos do perfil
        
        ttk.Label(details_frame, text="Nova Senha:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        self.entry_nova_senha = ttk.Entry(details_frame, textvariable=self.var_nova_senha, show="*", state="readonly", width=30)
        self.entry_nova_senha.grid(row=row, column=1, sticky="w", padx=5)
        row += 1
        
        # Botões de ação
        actions_frame = ttk.Frame(details_frame)
        actions_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        # Primeira linha de botões
        row1_frame = ttk.Frame(actions_frame)
        row1_frame.pack(pady=(0, 5))
        
        self.btn_editar = ttk.Button(row1_frame, text="✏️ Editar Dados", 
                                   command=self.toggle_edit_mode)
        self.btn_editar.pack(side=tk.LEFT, padx=5)
        
        self.btn_salvar = ttk.Button(row1_frame, text="💾 Salvar Alterações", 
                                   command=self.cmd_atualizar, state="disabled")
        self.btn_salvar.pack(side=tk.LEFT, padx=5)
        
        self.btn_cancelar = ttk.Button(row1_frame, text="❌ Cancelar", 
                                     command=self.cancel_edit_mode, state="disabled")
        self.btn_cancelar.pack(side=tk.LEFT, padx=5)
        
        # Segunda linha de botões
        row2_frame = ttk.Frame(actions_frame)
        row2_frame.pack()
        
        ttk.Button(row2_frame, text="🔑 Alterar Senha", 
                  command=self.cmd_alterar_senha).pack(side=tk.LEFT, padx=5)
        ttk.Button(row2_frame, text="✅ Ativar", 
                  command=lambda: self.cmd_set_ativo(True)).pack(side=tk.LEFT, padx=5)
        ttk.Button(row2_frame, text="❌ Desativar", 
                  command=lambda: self.cmd_set_ativo(False)).pack(side=tk.LEFT, padx=5)
        ttk.Button(row2_frame, text="🗑️ Remover", 
                  command=self.cmd_remover).pack(side=tk.LEFT, padx=5)

    def toggle_users_list(self):
        """Mostra/oculta a lista de usuários"""
        if self.users_list_visible:
            self.users_container.pack_forget()
            self.btn_show_users.config(text="📋 Mostrar Lista de Usuários")
            self.users_list_visible = False
            # Ocultar detalhes também se lista for ocultada
            if self.details_visible:
                self.details_container.pack_forget()
                self.details_visible = False
        else:
            self.users_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            self.btn_show_users.config(text="📋 Ocultar Lista de Usuários")
            self.users_list_visible = True
            # Carregar usuários se ainda não carregou
            if not self.users_data:
                self.cmd_listar()

    def toggle_edit_mode(self):
        """Alterna entre modo visualização e edição"""
        self.edit_mode = not self.edit_mode
        self.update_edit_mode()

    def cancel_edit_mode(self):
        """Cancela edição e restaura valores originais"""
        if self.selected_user:
            self.load_user_data(self.selected_user['id'])
        self.edit_mode = False
        self.update_edit_mode()

    def update_edit_mode(self):
        """Atualiza o estado dos campos baseado no modo de edição"""
        state = "normal" if self.edit_mode else "readonly"
        
        # Atualizar estado dos campos editáveis
        self.entry_nome.config(state=state)
        self.entry_email.config(state=state)
        self.entry_cpf.config(state=state)
        self.entry_telefone.config(state=state)
        self.cmb_perfil.config(state=state if state == "normal" else "readonly")
        self.cmb_clinica.config(state=state if state == "normal" else "readonly")
        self.entry_nova_senha.config(state=state)
        
        # Atualizar estado dos campos específicos do perfil
        perfil = self.var_perfil.get()
        if perfil in self.profile_fields:
            for field_name, widget in self.profile_fields[perfil].items():
                if 'entry' in field_name and hasattr(widget, 'config'):
                    widget.config(state=state)
        
        # Atualizar estado dos botões
        if self.edit_mode:
            self.btn_editar.config(state="disabled")
            self.btn_salvar.config(state="normal")
            self.btn_cancelar.config(state="normal")
        else:
            self.btn_editar.config(state="normal")
            self.btn_salvar.config(state="disabled")
            self.btn_cancelar.config(state="disabled")

    def show_user_details(self):
        """Mostra os detalhes do usuário selecionado"""
        if not self.details_visible:
            self.details_container.pack(fill=tk.BOTH, expand=True)
            self.details_visible = True
        # Sempre inicia no modo visualização
        self.edit_mode = False
        self.update_edit_mode()

    def load_user_data(self, user_id):
        """Carrega os dados do usuário nos campos"""
        try:
            user_data = self.run_async(get_user_detail(user_id))
            if user_data:
                # Temporariamente mudar estado para normal para permitir atualização
                self.entry_id.config(state="normal")
                self.entry_nome.config(state="normal")
                self.entry_email.config(state="normal")
                self.entry_cpf.config(state="normal")
                self.entry_telefone.config(state="normal")
                self.cmb_perfil.config(state="normal")
                self.cmb_clinica.config(state="normal")
                self.entry_nova_senha.config(state="normal")
                
                # Limpar campos primeiro
                self.entry_id.delete(0, tk.END)
                self.entry_nome.delete(0, tk.END)
                self.entry_email.delete(0, tk.END)
                self.entry_cpf.delete(0, tk.END)
                self.entry_telefone.delete(0, tk.END)
                self.entry_nova_senha.delete(0, tk.END)
                
                # Inserir novos valores
                self.entry_id.insert(0, str(user_data.get('id', '')))
                self.entry_nome.insert(0, user_data.get('nome', ''))
                self.entry_email.insert(0, user_data.get('email', ''))
                self.entry_cpf.insert(0, user_data.get('cpf', ''))
                self.entry_telefone.insert(0, user_data.get('telefone', ''))
                self.cmb_perfil.set(user_data.get('perfil', 'admin'))
                
                # Definir clínica usando a nova função
                self.set_clinica_selection(user_data.get('clinica_id'))
                
                # Mostrar campos específicos do perfil
                perfil = user_data.get('perfil', 'admin')
                self._show_profile_fields(perfil)
                
                # Carregar dados específicos do perfil
                self._load_profile_data(user_id, perfil)
                
                # Atualizar StringVar também
                self.var_id.set(str(user_data.get('id', '')))
                self.var_nome.set(user_data.get('nome', ''))
                self.var_email.set(user_data.get('email', ''))
                self.var_cpf.set(user_data.get('cpf', ''))
                self.var_telefone.set(user_data.get('telefone', ''))
                self.var_perfil.set(user_data.get('perfil', 'admin'))
                self.var_nova_senha.set('')
                
                self.selected_user = user_data
                self.show_user_details()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dados do usuário: {str(e)}")

    def _load_profile_data(self, user_id, perfil):
        """Carrega dados específicos do perfil do usuário"""
        try:
            user_data = self.run_async(get_user_detail(user_id))
            
            if perfil == 'professor' and 'professor' in self.profile_fields:
                # Buscar especialidade via serviço
                profile_data = self.run_async(self._get_profile_data_async(user_id))
                especialidade = profile_data.get('especialidade', '') if profile_data else ''
                self.profile_fields['professor']['especialidade_var'].set(especialidade)
                
            elif perfil == 'recepcionista' and 'recepcionista' in self.profile_fields:
                # Buscar telefone/ramal do perfil
                telefone_perfil = user_data.get('telefone_perfil', '')
                self.profile_fields['recepcionista']['telefone_var'].set(telefone_perfil or '')
                
            elif perfil == 'aluno' and 'aluno' in self.profile_fields:
                # Buscar dados do aluno
                profile_data = self.run_async(self._get_profile_data_async(user_id))
                if profile_data:
                    matricula = profile_data.get('matricula', '')
                    telefone_academico = profile_data.get('telefone', '')
                    self.profile_fields['aluno']['matricula_var'].set(matricula)
                    self.profile_fields['aluno']['telefone_var'].set(telefone_academico or '')
                    
        except Exception as e:
            print(f"Erro ao carregar dados do perfil: {e}")

    async def _get_profile_data_async(self, user_id):
        """Função async para buscar dados do perfil"""
        async with AsyncSessionLocal() as session:
            user = await session.get(UsuarioSistema, user_id)
            if user:
                return await svc_get_profile_data(session, user)
            return None

    def apply_filters(self):
        """Aplica os filtros na lista de usuários"""
        self.cmd_listar()

    def run_async(self, coro):
        """Run async code in a blocking way (simple MVP)."""
        return asyncio.run(coro)

    def bootstrap(self):
        try:
            self.run_async(init_db_and_seed())
            self.load_clinicas()  # Carregar clínicas após inicializar DB
        except Exception as e:
            messagebox.showerror("Erro ao iniciar", str(e))

    def on_select(self, _evt=None):
        """Quando um usuário é selecionado na lista"""
        idxs = self.listbox.curselection()
        if not idxs:
            return
        
        data = self.listbox.get(idxs[0])
        # formato: "[id] nome (perfil) - ativo"
        try:
            uid = int(data.split("]", 1)[0].lstrip("["))
            self.load_user_data(uid)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao selecionar usuário: {str(e)}")

    def load_clinicas(self):
        """Carrega as clínicas disponíveis e atualiza o combobox"""
        try:
            self.clinicas_data = self.run_async(list_clinicas())
            # Preparar lista para o combobox (formato: "ID - Nome")
            clinicas_options = [""]  # Opção vazia para "Nenhuma clínica"
            for clinica in self.clinicas_data:
                option = f"{clinica['id']} - {clinica['nome']}"
                clinicas_options.append(option)
            
            # Atualizar combobox
            self.cmb_clinica.config(values=clinicas_options)
        except Exception as e:
            print(f"Erro ao carregar clínicas: {e}")
            self.clinicas_data = []
            self.cmb_clinica.config(values=[""])

    def get_clinica_id_from_selection(self, selection: str) -> Optional[int]:
        """Extrai o ID da clínica a partir da seleção do combobox"""
        if not selection or not selection.strip():
            return None
        try:
            return int(selection.split(" - ")[0])
        except (ValueError, IndexError):
            return None

    def set_clinica_selection(self, clinica_id: Optional[int]):
        """Define a seleção do combobox baseado no ID da clínica"""
        if clinica_id is None:
            self.var_clinica.set("")
            return
        
        # Procurar a opção correspondente
        for clinica in self.clinicas_data:
            if clinica['id'] == clinica_id:
                selection = f"{clinica['id']} - {clinica['nome']}"
                self.var_clinica.set(selection)
                return
        
        # Se não encontrou, limpar seleção
        self.var_clinica.set("")

    def cmd_listar(self):
        """Lista os usuários aplicando filtros"""
        try:
            users = self.run_async(list_users())
            
            # Debug dos filtros - verificar tanto StringVar quanto widget
            perfil_var = self.var_filtro_perfil.get()
            perfil_widget = self.cmb_filtro.get()
            print(f"Filtro StringVar: '{perfil_var}'")
            print(f"Filtro Widget: '{perfil_widget}'")
            print(f"Total usuários antes: {len(users)}")
            
            # Usar valor do widget se StringVar estiver vazio
            perfil = perfil_widget if perfil_widget else perfil_var
            print(f"Filtro usado: '{perfil}'")
            
            # Aplicar filtros
            if perfil and perfil != "todos":
                users_antes = len(users)
                users = [u for u in users if u.get("perfil") == perfil]
                print(f"Após filtro de perfil '{perfil}': {len(users)} usuários")
                for u in users:
                    print(f"  - {u['nome']} ({u['perfil']})")
                
            if self.var_filtro_ativos.get():
                users = [u for u in users if u.get("ativo")]
                print(f"Após filtro de ativos: {len(users)} usuários")
            
            # Armazenar dados e atualizar lista
            self.users_data = users
            self.listbox.delete(0, tk.END)
            for u in users:
                label = f"[{u['id']}] {u['nome']} ({u['perfil']}) - {'ativo' if u['ativo'] else 'inativo'}"
                self.listbox.insert(tk.END, label)
                
        except Exception as e:
            messagebox.showerror("Erro ao listar", str(e))

    def _submit_create(self, data: dict):
        return self.run_async(create_user(
            data["nome"], data["email"], data["senha"], data["perfil"], data["cpf"], data["clinica_id"], data.get("telefone"), None
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

    def cmd_my_profile(self):
        """Abre a tela de perfil do usuário atual"""
        # Por simplicidade, assumindo que o usuário logado é o ID 1 (admin)
        # Em uma implementação real, você teria o ID do usuário logado
        dialog = UserProfileDialog(self, user_id=1)
        self.wait_window(dialog)
        
        if dialog.result:
            messagebox.showinfo("Sucesso", "Perfil atualizado com sucesso!")

    def cmd_atualizar(self):
        try:
            if not self.var_id.get().strip().isdigit():
                messagebox.showwarning("Seleção necessária", "Selecione um usuário da lista")
                return
            uid = int(self.var_id.get())
            
            # Capturar dados originais
            dados_originais = self.selected_user if self.selected_user else {}
            print(f"Dados originais: {dados_originais}")
            
            # Debug: verificar estado dos widgets e valores
            print(f"Estado dos Entry widgets:")
            print(f"  entry_nome state: {self.entry_nome.cget('state')}")
            print(f"  entry_email state: {self.entry_email.cget('state')}")
            print(f"  entry_cpf state: {self.entry_cpf.cget('state')}")
            print(f"  cmb_perfil state: {self.cmb_perfil.cget('state')}")
            
            nome = self.var_nome.get().strip() or None
            email = self.var_email.get().strip() or None
            cpf = self.var_cpf.get().strip() or None
            perfil = self.var_perfil.get().strip() or None
            clin_raw = self.var_clinica.get().strip()
            clinica_id = int(clin_raw) if clin_raw else None
            
            # Debug: verificar valores das StringVars
            print(f"Valores das StringVars:")
            print(f"  var_nome: '{self.var_nome.get()}'")
            print(f"  var_email: '{self.var_email.get()}'")
            print(f"  var_cpf: '{self.var_cpf.get()}'")
            print(f"  var_perfil: '{self.var_perfil.get()}'")
            
            # Ler diretamente dos widgets (StringVars não sincronizam após readonly->normal)
            try:
                nome = self.entry_nome.get().strip() or None
                email = self.entry_email.get().strip() or None
                cpf = self.entry_cpf.get().strip() or None
                perfil = self.cmb_perfil.get().strip() or None
                clinica_id = self.get_clinica_id_from_selection(self.cmb_clinica.get())
                nova_senha = self.entry_nova_senha.get().strip()
                
                print(f"Valores corretos (lidos dos widgets):")
                print(f"  entry_nome.get(): '{nome}'")
                print(f"  entry_email.get(): '{email}'")
                print(f"  entry_cpf.get(): '{cpf}'")
                print(f"  cmb_perfil.get(): '{perfil}'")
                print(f"  clinica_id: {clinica_id}")
                print(f"  entry_nova_senha.get(): '{'***' if nova_senha else '(vazia)'}'")
            except Exception as e:
                print(f"Erro ao ler widgets diretamente: {e}")
                return
            
            print(f"Atualizando usuário {uid}:")
            print(f"  Nome: '{dados_originais.get('nome', '')}' -> '{nome}'")
            print(f"  Email: '{dados_originais.get('email', '')}' -> '{email}'")
            print(f"  CPF: '{dados_originais.get('cpf', '')}' -> '{cpf}'")
            print(f"  Perfil: '{dados_originais.get('perfil', '')}' -> '{perfil}'")
            print(f"  Clinica ID: {dados_originais.get('clinica_id', '')} -> {clinica_id}")
            
            # Verificar se houve mudanças (incluindo senha)
            print(f"  Nova Senha: {'***' if nova_senha else '(vazia)'}")
            
            mudancas = []
            if nome != dados_originais.get('nome'):
                mudancas.append('nome')
            if email != dados_originais.get('email'):
                mudancas.append('email')
            if cpf != dados_originais.get('cpf'):
                mudancas.append('cpf')
            if perfil != dados_originais.get('perfil'):
                mudancas.append('perfil')
            if clinica_id != dados_originais.get('clinica_id'):
                mudancas.append('clinica_id')
            if nova_senha:  # Se foi fornecida uma nova senha
                mudancas.append('senha')
                
            print(f"Campos que mudaram: {mudancas}")
            
            if not mudancas:
                print("Nenhuma mudança detectada!")
                messagebox.showinfo("Info", "Nenhuma alteração foi feita.")
                return
            
            # Atualizar no banco
            self.run_async(update_user(uid, nome=nome, email=email, cpf=cpf, perfil=perfil, clinica_id=clinica_id))
            
            # Atualizar senha separadamente se fornecida
            if nova_senha:
                print("Atualizando senha...")
                self.run_async(change_password(uid, nova_senha))
            print("Atualização no banco concluída")
            
            # Limpar campo de senha após atualização
            if nova_senha:
                self.var_nova_senha.set("")
                self.entry_nova_senha.delete(0, tk.END)
                print("Campo de senha limpo")
            
            # Sair do modo edição
            self.edit_mode = False
            self.update_edit_mode()
            print("Modo edição desabilitado")
            
            # Recarregar dados do usuário atual
            self.load_user_data(uid)
            print("Dados do usuário recarregados")
            
            # Atualizar lista para refletir mudanças
            self.cmd_listar()
            print("Lista atualizada")
            
            # Reselecionar o usuário atualizado na lista
            for i in range(self.listbox.size()):
                if self.listbox.get(i).startswith(f"[{uid}]"):
                    self.listbox.selection_clear(0, tk.END)
                    self.listbox.selection_set(i)
                    self.listbox.see(i)
                    print(f"Usuário {uid} reselecionado na posição {i}")
                    break
            
            messagebox.showinfo("Sucesso", f"Usuário atualizado com sucesso!\nCampos alterados: {', '.join(mudancas)}")
            
        except Exception as e:
            print(f"Erro em cmd_atualizar: {e}")
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
