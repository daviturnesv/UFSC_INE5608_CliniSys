"""
Tela de perfil do usuário - permite que cada usuário edite suas próprias informações
"""
from __future__ import annotations

import asyncio
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from src.backend.db.database import AsyncSessionLocal
from src.backend.models.usuario import UsuarioSistema
from src.backend.controllers.usuario_service import (
    get_profile_data as svc_get_profile_data,
    validate_password_policy,
)
from src.backend.core.security import hash_password, verify_password
from sqlalchemy import select, update


async def get_user_profile(user_id: int) -> dict:
    """Busca dados do perfil do usuário logado"""
    async with AsyncSessionLocal() as session:
        user = await session.get(UsuarioSistema, user_id)
        if not user:
            raise ValueError("Usuário não encontrado")
        
        # Buscar dados específicos do perfil
        profile_data = await svc_get_profile_data(session, user)
        
        return {
            "id": user.id,
            "nome": user.nome,
            "email": user.email,
            "telefone": user.telefone or "",
            "perfil": user.perfil.value,
            "profile_data": profile_data or {},
        }


async def update_user_profile(user_id: int, nome: str, email: str, telefone: Optional[str], 
                             senha_atual: Optional[str], nova_senha: Optional[str]) -> None:
    """Atualiza o perfil do usuário"""
    async with AsyncSessionLocal() as session:
        user = await session.get(UsuarioSistema, user_id)
        if not user:
            raise ValueError("Usuário não encontrado")
        
        # Validar senha atual se nova senha foi fornecida
        if nova_senha:
            if not senha_atual:
                raise ValueError("Senha atual é obrigatória para alterar a senha")
            if not verify_password(senha_atual, user.senha_hash):
                raise ValueError("Senha atual incorreta")
            validate_password_policy(nova_senha)
            user.senha_hash = hash_password(nova_senha)
        
        # Atualizar dados básicos
        user.nome = nome
        user.email = email
        user.telefone = telefone if telefone else None
        
        await session.commit()


class UserProfileDialog(tk.Toplevel):
    """Dialog para edição do perfil do usuário"""
    
    def __init__(self, parent, user_id: int):
        super().__init__(parent)
        self.user_id = user_id
        self.user_data = None
        self.result = False
        
        self.title("Meu Perfil")
        self.geometry("500x600")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Centralizar na tela
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (600 // 2)
        self.geometry(f"500x600+{x}+{y}")
        
        self._create_interface()
        self._load_user_data()
    
    def _create_interface(self):
        """Cria a interface do dialog"""
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(title_frame, text="✏️ Editar Meu Perfil", 
                               font=("Arial", 16, "bold"))
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, 
                                  text="Atualize suas informações pessoais",
                                  font=("Arial", 10))
        subtitle_label.pack(pady=(5, 0))
        
        # Formulário
        form_frame = ttk.LabelFrame(main_frame, text="Informações Pessoais", padding="15")
        form_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Variáveis dos campos
        self.var_nome = tk.StringVar()
        self.var_email = tk.StringVar()
        self.var_telefone = tk.StringVar()
        self.var_senha_atual = tk.StringVar()
        self.var_nova_senha = tk.StringVar()
        self.var_confirma_senha = tk.StringVar()
        
        row = 0
        
        # Nome
        ttk.Label(form_frame, text="Nome Completo:").grid(row=row, column=0, sticky="w", pady=(0, 5))
        row += 1
        self.entry_nome = ttk.Entry(form_frame, textvariable=self.var_nome, width=50)
        self.entry_nome.grid(row=row, column=0, sticky="ew", pady=(0, 15))
        row += 1
        
        # Email
        ttk.Label(form_frame, text="Email:").grid(row=row, column=0, sticky="w", pady=(0, 5))
        row += 1
        self.entry_email = ttk.Entry(form_frame, textvariable=self.var_email, width=50)
        self.entry_email.grid(row=row, column=0, sticky="ew", pady=(0, 15))
        row += 1
        
        # Telefone
        ttk.Label(form_frame, text="Telefone (opcional):").grid(row=row, column=0, sticky="w", pady=(0, 5))
        row += 1
        self.entry_telefone = ttk.Entry(form_frame, textvariable=self.var_telefone, width=50)
        self.entry_telefone.grid(row=row, column=0, sticky="ew", pady=(0, 20))
        row += 1
        
        # Seção de mudança de senha
        senha_frame = ttk.LabelFrame(form_frame, text="Alterar Senha (opcional)", padding="10")
        senha_frame.grid(row=row, column=0, sticky="ew", pady=(10, 15))
        form_frame.grid_columnconfigure(0, weight=1)
        row += 1
        
        # Senha atual
        ttk.Label(senha_frame, text="Senha Atual:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.entry_senha_atual = ttk.Entry(senha_frame, textvariable=self.var_senha_atual, 
                                          show="*", width=45)
        self.entry_senha_atual.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        # Nova senha
        ttk.Label(senha_frame, text="Nova Senha:").grid(row=2, column=0, sticky="w", pady=(0, 5))
        self.entry_nova_senha = ttk.Entry(senha_frame, textvariable=self.var_nova_senha, 
                                         show="*", width=45)
        self.entry_nova_senha.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        
        # Confirmar senha
        ttk.Label(senha_frame, text="Confirmar Nova Senha:").grid(row=4, column=0, sticky="w", pady=(0, 5))
        self.entry_confirma_senha = ttk.Entry(senha_frame, textvariable=self.var_confirma_senha, 
                                             show="*", width=45)
        self.entry_confirma_senha.grid(row=5, column=0, sticky="ew")
        
        senha_frame.grid_columnconfigure(0, weight=1)
        
        # Informações sobre política de senha
        info_frame = ttk.Frame(form_frame)
        info_frame.grid(row=row, column=0, sticky="ew", pady=(0, 15))
        row += 1
        
        info_label = ttk.Label(info_frame, 
                              text="💡 A senha deve ter pelo menos 8 caracteres, incluindo letras e números",
                              font=("Arial", 9),
                              foreground="blue")
        info_label.pack()
        
        # Botões
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(buttons_frame, text="❌ Cancelar", 
                  command=self.destroy).pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Button(buttons_frame, text="💾 Salvar Alterações", 
                  command=self._save_profile).pack(side=tk.RIGHT)
        
        # Labels de erro
        self.error_label = ttk.Label(main_frame, text="", foreground="red", 
                                    font=("Arial", 9), wraplength=450)
        self.error_label.pack(pady=(10, 0))
    
    def _load_user_data(self):
        """Carrega os dados do usuário"""
        try:
            self.user_data = asyncio.run(get_user_profile(self.user_id))
            
            self.var_nome.set(self.user_data.get("nome", ""))
            self.var_email.set(self.user_data.get("email", ""))
            self.var_telefone.set(self.user_data.get("telefone", ""))
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dados do usuário: {e}")
            self.destroy()
    
    def _save_profile(self):
        """Salva as alterações do perfil"""
        try:
            # Validar dados
            nome = self.var_nome.get().strip()
            email = self.var_email.get().strip()
            telefone = self.var_telefone.get().strip() or None
            senha_atual = self.var_senha_atual.get().strip()
            nova_senha = self.var_nova_senha.get().strip()
            confirma_senha = self.var_confirma_senha.get().strip()
            
            # Limpar erro anterior
            self.error_label.config(text="")
            
            # Validações básicas
            if not nome:
                raise ValueError("Nome é obrigatório")
            if not email:
                raise ValueError("Email é obrigatório")
            if "@" not in email:
                raise ValueError("Email inválido")
            
            # Validar mudança de senha
            if nova_senha or confirma_senha or senha_atual:
                if not senha_atual:
                    raise ValueError("Senha atual é obrigatória para alterar a senha")
                if not nova_senha:
                    raise ValueError("Nova senha é obrigatória")
                if nova_senha != confirma_senha:
                    raise ValueError("Nova senha e confirmação não coincidem")
            
            # Salvar alterações
            asyncio.run(update_user_profile(
                self.user_id, nome, email, telefone, 
                senha_atual if nova_senha else None, 
                nova_senha if nova_senha else None
            ))
            
            self.result = True
            messagebox.showinfo("Sucesso", "Perfil atualizado com sucesso!")
            self.destroy()
            
        except Exception as e:
            self.error_label.config(text=str(e))


class UserProfileApp(tk.Tk):
    """Aplicativo standalone para perfil do usuário"""
    
    def __init__(self, user_id: int = 1):  # Padrão: admin
        super().__init__()
        self.user_id = user_id
        
        self.title("CliniSys - Meu Perfil")
        self.geometry("600x700")
        self.resizable(True, True)
        
        # Centralizar na tela
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"600x700+{x}+{y}")
        
        self._create_interface()
        self._load_user_data()
    
    def _create_interface(self):
        """Cria a interface principal"""
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Cabeçalho
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        title_label = ttk.Label(header_frame, text="👤 Meu Perfil", 
                               font=("Arial", 24, "bold"))
        title_label.pack()
        
        self.subtitle_label = ttk.Label(header_frame, text="Carregando...", 
                                       font=("Arial", 12))
        self.subtitle_label.pack(pady=(10, 0))
        
        # Card do perfil
        profile_frame = ttk.LabelFrame(main_frame, text="Informações do Perfil", padding="20")
        profile_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Informações do usuário (read-only)
        info_frame = ttk.Frame(profile_frame)
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Grid para as informações
        self.info_labels = {}
        
        row = 0
        for label, key in [("Nome:", "nome"), ("Email:", "email"), 
                          ("Telefone:", "telefone"), ("Perfil:", "perfil")]:
            ttk.Label(info_frame, text=label, font=("Arial", 10, "bold")).grid(
                row=row, column=0, sticky="w", padx=(0, 10), pady=5)
            self.info_labels[key] = ttk.Label(info_frame, text="", font=("Arial", 10))
            self.info_labels[key].grid(row=row, column=1, sticky="w", pady=5)
            row += 1
        
        # Botão para editar
        edit_frame = ttk.Frame(profile_frame)
        edit_frame.pack(fill=tk.X)
        
        ttk.Button(edit_frame, text="✏️ Editar Perfil", 
                  command=self._open_edit_dialog).pack(pady=10)
        
        # Informações adicionais
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill=tk.X)
        
        footer_label = ttk.Label(footer_frame, 
                                text="💡 Para alterar informações específicas do seu perfil (especialidade, matrícula, etc.),\ncontate o administrador do sistema.",
                                font=("Arial", 9),
                                foreground="gray",
                                justify=tk.CENTER)
        footer_label.pack()
    
    def _load_user_data(self):
        """Carrega e exibe os dados do usuário"""
        try:
            self.user_data = asyncio.run(get_user_profile(self.user_id))
            
            # Atualizar subtitle
            self.subtitle_label.config(text=f"Bem-vindo(a), {self.user_data.get('nome', 'Usuário')}!")
            
            # Atualizar informações
            self.info_labels["nome"].config(text=self.user_data.get("nome", "N/A"))
            self.info_labels["email"].config(text=self.user_data.get("email", "N/A"))
            self.info_labels["telefone"].config(text=self.user_data.get("telefone", "Não informado"))
            
            perfil = self.user_data.get("perfil", "N/A")
            perfil_map = {
                "admin": "Administrador",
                "professor": "Professor",
                "aluno": "Aluno",
                "recepcionista": "Recepcionista"
            }
            self.info_labels["perfil"].config(text=perfil_map.get(perfil, perfil))
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dados do usuário: {e}")
    
    def _open_edit_dialog(self):
        """Abre o dialog de edição"""
        dialog = UserProfileDialog(self, self.user_id)
        self.wait_window(dialog)
        
        if dialog.result:
            # Recarregar dados após edição
            self._load_user_data()


if __name__ == "__main__":
    # Para teste, usar ID do admin
    app = UserProfileApp(user_id=1)
    app.mainloop()