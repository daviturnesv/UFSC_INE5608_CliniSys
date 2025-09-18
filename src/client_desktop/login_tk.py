"""
Tela de Login para o Sistema CliniSys-Escola
"""

from __future__ import annotations

import asyncio
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any

from src.backend.db.database import AsyncSessionLocal
from src.backend.controllers.usuario_service import authenticate_user
from src.backend.models.usuario import UsuarioSistema, PerfilUsuario


class LoginDialog(tk.Toplevel):
    """Dialog de login para autenticação de usuários"""
    
    def __init__(self, master: tk.Tk, on_login_success=None):
        super().__init__(master)
        self.title("CliniSys-Escola - Login")
        self.resizable(False, False)
        self.result: Optional[Dict[str, Any]] = None
        self._on_login_success = on_login_success
        self.user_data: Optional[Dict[str, Any]] = None
        
        # Centralizar a janela
        self.geometry("450x400")
        self.transient(master)
        self.grab_set()
        
        # Garantir que a janela apareça na frente
        self.lift()
        self.attributes('-topmost', True)
        self.after_idle(lambda: self.attributes('-topmost', False))
        
        self._create_widgets()
        self._center_window()
        
        # Focar no campo email
        self.entry_email.focus()
        
        # Bind Enter para fazer login
        self.bind('<Return>', lambda e: self.on_login())
    
    def _create_widgets(self):
        """Cria os widgets da tela de login"""
        # Frame principal
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Logo/Título
        title_label = ttk.Label(
            main_frame, 
            text="CliniSys-Escola", 
            font=("Arial", 18, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        subtitle_label = ttk.Label(
            main_frame, 
            text="Sistema de Gestão para Clínica Escola", 
            font=("Arial", 10)
        )
        subtitle_label.pack(pady=(0, 10))
        
        # Informações de credenciais padrão
        info_frame = ttk.LabelFrame(main_frame, text="Credenciais Padrão", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        info_label = ttk.Label(
            info_frame,
            text="Email: admin@exemplo.com\nSenha: admin123",
            font=("Arial", 9),
            foreground="blue"
        )
        info_label.pack()
        
        # Frame do formulário
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.X, pady=20)
        
        # Email
        ttk.Label(form_frame, text="Email:").pack(anchor="w", pady=(0, 5))
        self.var_email = tk.StringVar(value="admin@exemplo.com")  # Pré-preencher
        self.entry_email = ttk.Entry(form_frame, textvariable=self.var_email, width=40)
        self.entry_email.pack(fill=tk.X, pady=(0, 15))
        
        # Senha
        ttk.Label(form_frame, text="Senha:").pack(anchor="w", pady=(0, 5))
        self.var_senha = tk.StringVar(value="admin123")  # Pré-preencher
        self.entry_senha = ttk.Entry(form_frame, textvariable=self.var_senha, show="*", width=40)
        self.entry_senha.pack(fill=tk.X, pady=(0, 20))
        
        # Botões
        btn_frame = ttk.Frame(form_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            btn_frame, 
            text="Cancelar", 
            command=self.destroy
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            btn_frame, 
            text="Entrar", 
            command=self.on_login
        ).pack(side=tk.LEFT)
        
        # Label de erro
        self.lbl_erro = ttk.Label(
            main_frame, 
            text="", 
            foreground="red", 
            wraplength=360,
            font=("Arial", 9)
        )
        self.lbl_erro.pack(pady=(20, 0))
        
        # Informações padrão (pode ser removido em produção)
        info_frame = ttk.LabelFrame(main_frame, text="Credenciais Padrão", padding="10")
        info_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Label(
            info_frame, 
            text="Admin: admin@exemplo.com / admin123", 
            font=("Arial", 8)
        ).pack()
    
    def _center_window(self):
        """Centraliza a janela na tela"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def on_login(self):
        """Processa o login do usuário"""
        self.lbl_erro.config(text="")
        
        email = self.var_email.get().strip()
        senha = self.var_senha.get()
        
        # Validações básicas
        if not email:
            self.lbl_erro.config(text="Email é obrigatório")
            self.entry_email.focus()
            return
        
        if not senha:
            self.lbl_erro.config(text="Senha é obrigatória")
            self.entry_senha.focus()
            return
        
        # Tentar autenticar
        try:
            self.lbl_erro.config(text="Autenticando...")
            self.update()
            
            user = asyncio.run(self._authenticate_user(email, senha))
            
            if user:
                self.user_data = {
                    "id": user.id,
                    "nome": user.nome,
                    "email": user.email,
                    "perfil": user.perfil.value,
                    "ativo": user.ativo
                }
                
                if self._on_login_success:
                    self._on_login_success(self.user_data)
                
                self.result = self.user_data
                self.destroy()
            else:
                self.lbl_erro.config(text="Email ou senha incorretos")
                self.entry_senha.delete(0, tk.END)
                self.entry_email.focus()
                
        except Exception as e:
            self.lbl_erro.config(text=f"Erro ao autenticar: {str(e)}")
            self.entry_senha.delete(0, tk.END)
    
    async def _authenticate_user(self, email: str, senha: str) -> Optional[UsuarioSistema]:
        """Autentica o usuário no banco de dados"""
        async with AsyncSessionLocal() as session:
            user = await authenticate_user(session, email, senha)
            
            if user and not user.ativo:
                raise ValueError("Usuário inativo. Contate o administrador.")
            
            return user


class LoginApp(tk.Tk):
    """Aplicação principal de login"""
    
    def __init__(self):
        super().__init__()
        self.title("CliniSys-Escola")
        self.geometry("1x1")  # Janela mínima invisível
        self.withdraw()  # Esconder a janela principal
        
        self.user_data: Optional[Dict[str, Any]] = None
        self.authenticated = False
        
        self._show_login()
    
    def _show_login(self):
        """Mostra o dialog de login"""
        login_dialog = LoginDialog(self, on_login_success=self._on_login_success)
        
        # Aguarda o fechamento do dialog
        self.wait_window(login_dialog)
        
        if not self.authenticated:
            self.destroy()  # Fecha a aplicação se não autenticou
    
    def _on_login_success(self, user_data: Dict[str, Any]):
        """Callback executado quando o login é bem-sucedido"""
        self.user_data = user_data
        self.authenticated = True
        
        # Pode adicionar lógica adicional aqui
        print(f"Login bem-sucedido: {user_data['nome']} ({user_data['perfil']})")


def show_login_dialog(master: Optional[tk.Tk] = None) -> Optional[Dict[str, Any]]:
    """
    Função utilitária para mostrar dialog de login
    
    Returns:
        Dict com dados do usuário se login bem-sucedido, None caso contrário
    """
    print("Criando dialog de login...")
    
    # Criar uma nova janela principal para o login ao invés de Toplevel
    print("Criando janela Tkinter...")
    login_window = tk.Tk()
    print("Janela criada, configurando...")
    
    login_window.title("CliniSys-Escola - Login")
    login_window.geometry("450x400")
    login_window.resizable(False, False)
    
    print("Configurando posicionamento...")
    # Centralizar a janela
    login_window.update_idletasks()
    width = login_window.winfo_width()
    height = login_window.winfo_height()
    x = (login_window.winfo_screenwidth() // 2) - (width // 2)
    y = (login_window.winfo_screenheight() // 2) - (height // 2)
    login_window.geometry(f'{width}x{height}+{x}+{y}')
    
    print("Configurando atributos de janela...")
    # Garantir que a janela apareça na frente
    login_window.lift()
    login_window.attributes('-topmost', True)
    login_window.after_idle(lambda: login_window.attributes('-topmost', False))
    
    result = None
    
    def on_login_success(user_data):
        nonlocal result
        print(f"Login success callback: {user_data}")
        result = user_data
        login_window.quit()
        login_window.destroy()
    
    def on_cancel():
        nonlocal result
        print("Cancel callback")
        result = None
        login_window.quit()
        login_window.destroy()
    
    print("Criando conteúdo da janela...")
    # Criar o conteúdo da janela de login
    _create_login_content(login_window, on_login_success, on_cancel)
    
    print("Aguardando dialog de login...")
    try:
        print("Iniciando mainloop...")
        login_window.mainloop()
        print("Mainloop finalizado...")
    except Exception as e:
        print(f"Erro no login dialog: {e}")
        result = None
    
    print(f"Dialog finalizado, resultado: {result}")
    return result


def _create_login_content(window, on_success_callback, on_cancel_callback):
    """Cria o conteúdo da janela de login"""
    # Frame principal
    main_frame = ttk.Frame(window, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Logo/Título
    title_label = ttk.Label(
        main_frame, 
        text="CliniSys-Escola", 
        font=("Arial", 18, "bold")
    )
    title_label.pack(pady=(0, 10))
    
    subtitle_label = ttk.Label(
        main_frame, 
        text="Sistema de Gestão para Clínica Escola", 
        font=("Arial", 10)
    )
    subtitle_label.pack(pady=(0, 10))
    
    # Informações de credenciais padrão
    info_frame = ttk.LabelFrame(main_frame, text="Credenciais Padrão", padding="10")
    info_frame.pack(fill=tk.X, pady=(0, 20))
    
    info_label = ttk.Label(
        info_frame,
        text="Email: admin@exemplo.com\nSenha: admin123",
        font=("Arial", 9),
        foreground="blue"
    )
    info_label.pack()
    
    # Frame do formulário
    form_frame = ttk.Frame(main_frame)
    form_frame.pack(fill=tk.X, pady=20)
    
    # Email
    ttk.Label(form_frame, text="Email:").pack(anchor="w", pady=(0, 5))
    var_email = tk.StringVar(value="admin@exemplo.com")  # Pré-preencher
    entry_email = ttk.Entry(form_frame, textvariable=var_email, width=40)
    entry_email.pack(fill=tk.X, pady=(0, 15))
    
    # Senha
    ttk.Label(form_frame, text="Senha:").pack(anchor="w", pady=(0, 5))
    var_senha = tk.StringVar(value="admin123")  # Pré-preencher
    entry_senha = ttk.Entry(form_frame, textvariable=var_senha, show="*", width=40)
    entry_senha.pack(fill=tk.X, pady=(0, 20))
    
    # Label para mensagens de erro
    error_label = ttk.Label(form_frame, text="", foreground="red")
    error_label.pack(pady=(0, 10))
    
    def authenticate_login():
        """Autentica o login do usuário (versão síncrona)"""
        email = var_email.get().strip()
        senha = var_senha.get().strip()
        
        if not email or not senha:
            error_label.config(text="Email e senha são obrigatórios")
            return
        
        error_label.config(text="Autenticando...")
        window.update()
        
        try:
            # Usar as credenciais padrão por enquanto para teste
            if email == "admin@exemplo.com" and senha == "admin123":
                user_data = {
                    'id': 1,
                    'nome': 'Administrador',
                    'email': 'admin@exemplo.com',
                    'perfil': 'admin',
                    'ativo': True
                }
                on_success_callback(user_data)
            else:
                error_label.config(text="Email ou senha inválidos")
        except Exception as e:
            error_label.config(text=f"Erro na autenticação: {str(e)}")
    
    def on_login():
        """Executa o login"""
        authenticate_login()
    
    def on_cancel_click():
        """Cancela o login"""
        on_cancel_callback()
    
    # Botões
    button_frame = ttk.Frame(form_frame)
    button_frame.pack(fill=tk.X, pady=10)
    
    ttk.Button(
        button_frame, 
        text="Entrar", 
        command=on_login
    ).pack(side=tk.LEFT, padx=(0, 10))
    
    ttk.Button(
        button_frame, 
        text="Cancelar", 
        command=on_cancel_click
    ).pack(side=tk.LEFT)
    
    # Focar no campo email
    entry_email.focus()
    
    # Bind Enter para fazer login
    window.bind('<Return>', lambda e: on_login())


if __name__ == "__main__":
    # Teste da tela de login
    app = LoginApp()
    if app.authenticated:
        print("Login realizado com sucesso!")
        print(f"Usuário: {app.user_data}")
    else:
        print("Login cancelado ou falhou")
    
    app.mainloop()
