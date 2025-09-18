"""
CliniSys-Escola - Aplicação Desktop Integrada
Sistema completo para gerenciamento de clínica escola
"""

from __future__ import annotations

import asyncio
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from typing import Dict, Any

# Adiciona o diretório raiz ao path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.client_desktop.uc_admin_users_tk import UsersApp, init_db_and_seed
from src.client_desktop.pacientes_tk import PacientesTab
from src.client_desktop.login_tk import show_login_dialog


class CliniSysApp(tk.Tk):
    """Aplicação principal do CliniSys-Escola"""
    
    def __init__(self, user_data: Dict[str, Any]):
        super().__init__()
        
        self.title("CliniSys-Escola - Sistema de Gestão")
        self.geometry("1200x700")
        self.state('zoomed')  # Maximizar no Windows
        
        # Dados do usuário logado
        self.current_user = user_data
        self.title(f"CliniSys-Escola - {user_data['nome']} ({user_data['perfil'].title()})")
        
        self._create_menu()
        self._create_main_interface()
        self._update_interface_for_user()
    
    def _create_menu(self):
        """Cria a barra de menu baseada no perfil do usuário"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # Menu Arquivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Logout", command=self._logout)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.quit)
        
        # Menu Administração (apenas para admin)
        if self.current_user and self.current_user['perfil'] == 'admin':
            admin_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Administração", menu=admin_menu)
            admin_menu.add_command(label="Gerenciar Usuários", command=self._open_users_window)
        
        # Menu Pacientes (admin e recepcionista)
        if self.current_user and self.current_user['perfil'] in ['admin', 'recepcionista']:
            pacientes_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Pacientes", menu=pacientes_menu)
            pacientes_menu.add_command(label="Gerenciar Pacientes", command=self._focus_pacientes_tab)
        
        # Menu Atendimento (todos exceto admin)
        if self.current_user and self.current_user['perfil'] in ['professor', 'aluno', 'recepcionista']:
            atend_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Atendimento", menu=atend_menu)
            atend_menu.add_command(label="Fila de Atendimento", command=self._show_fila_atendimento)
        
        # Menu Relatórios (admin e professor)
        if self.current_user and self.current_user['perfil'] in ['admin', 'professor']:
            rel_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Relatórios", menu=rel_menu)
            rel_menu.add_command(label="Relatórios Gerenciais", command=self._show_relatorios)
        
        # Menu Ajuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        help_menu.add_command(label="Sobre", command=self._show_about)
    
    def _logout(self):
        """Faz logout e fecha a aplicação"""
        if messagebox.askyesno("Logout", "Deseja realmente sair do sistema?", parent=self):
            self.destroy()
    
    def _create_main_interface(self):
        """Cria a interface principal com abas"""
        # Frame principal
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Título
        title_label = ttk.Label(main_frame, text="CliniSys-Escola", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        subtitle_label = ttk.Label(main_frame, text="Sistema de Gestão para Clínica Escola", font=("Arial", 10))
        subtitle_label.pack(pady=(0, 20))
        
        # Notebook para abas
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # Aba Dashboard
        self._create_dashboard_tab()
        
        # Aba Pacientes
        self.pacientes_tab = PacientesTab(self.notebook)
        self.notebook.add(self.pacientes_tab, text="Pacientes")
        
        # Status bar
        self.status_bar = ttk.Label(main_frame, text="Pronto", relief="sunken", anchor="w")
        self.status_bar.pack(side="bottom", fill="x", pady=(10, 0))
    
    def _create_dashboard_tab(self):
        """Cria a aba de dashboard"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")
        
        # Título do dashboard
        ttk.Label(dashboard_frame, text="Painel de Controle", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Frame para cards de estatísticas
        stats_frame = ttk.Frame(dashboard_frame)
        stats_frame.pack(fill="x", padx=20, pady=10)
        
        # Cards de estatísticas
        self._create_stat_card(stats_frame, "Pacientes\nCadastrados", "0", 0, 0)
        self._create_stat_card(stats_frame, "Aguardando\nTriagem", "0", 0, 1)
        self._create_stat_card(stats_frame, "Em\nAtendimento", "0", 0, 2)
        self._create_stat_card(stats_frame, "Atendimentos\nHoje", "0", 0, 3)
        
        # Frame para ações rápidas
        actions_frame = ttk.LabelFrame(dashboard_frame, text="Ações Rápidas")
        actions_frame.pack(fill="x", padx=20, pady=20)
        
        # Botões de ações rápidas
        buttons_frame = ttk.Frame(actions_frame)
        buttons_frame.pack(padx=10, pady=10)
        
        ttk.Button(buttons_frame, text="Novo Paciente", command=self._new_patient, width=15).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(buttons_frame, text="Buscar Paciente", command=self._search_patient, width=15).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(buttons_frame, text="Gerenciar Usuários", command=self._open_users_window, width=15).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Button(buttons_frame, text="Fila Triagem", command=self._show_not_implemented, width=15).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(buttons_frame, text="Agendar Consulta", command=self._show_not_implemented, width=15).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(buttons_frame, text="Relatórios", command=self._show_not_implemented, width=15).grid(row=1, column=2, padx=5, pady=5)
        
        # Área de notificações
        notifications_frame = ttk.LabelFrame(dashboard_frame, text="Notificações")
        notifications_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Text widget para notificações
        self.notifications_text = tk.Text(notifications_frame, height=8, wrap="word", state="disabled")
        self.notifications_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Scrollbar para notificações
        notifications_scrollbar = ttk.Scrollbar(notifications_frame, orient="vertical", command=self.notifications_text.yview)
        self.notifications_text.configure(yscrollcommand=notifications_scrollbar.set)
        notifications_scrollbar.pack(side="right", fill="y")
        
        # Adicionar notificação inicial
        self._add_notification("Sistema iniciado com sucesso!")
        self._add_notification("Banco de dados conectado.")
    
    def _update_interface_for_user(self):
        """Atualiza interface baseada no perfil do usuário"""
        if not self.current_user:
            return
        
        # Personalizar dashboard baseado no perfil
        user_profile = self.current_user['perfil']
        
        if user_profile == 'admin':
            self._add_notification(f"Bem-vindo, Administrador {self.current_user['nome']}!")
        elif user_profile == 'recepcionista':
            self._add_notification(f"Bem-vinda, {self.current_user['nome']}! Gerenciamento de pacientes disponível.")
        elif user_profile == 'professor':
            self._add_notification(f"Bem-vindo, Prof. {self.current_user['nome']}! Acesso a atendimentos e relatórios.")
        elif user_profile == 'aluno':
            self._add_notification(f"Bem-vindo, {self.current_user['nome']}! Acesso a atendimentos disponível.")
    
    def _focus_pacientes_tab(self):
        """Foca na aba de pacientes"""
        if hasattr(self, 'notebook') and hasattr(self, 'pacientes_tab'):
            self.notebook.select(self.pacientes_tab)
        else:
            messagebox.showinfo("Info", "Aba de pacientes não disponível", parent=self)
    
    def _show_fila_atendimento(self):
        """Mostra a fila de atendimento"""
        messagebox.showinfo("Em desenvolvimento", "Funcionalidade da fila de atendimento em desenvolvimento", parent=self)
    
    def _show_relatorios(self):
        """Mostra os relatórios"""
        messagebox.showinfo("Em desenvolvimento", "Funcionalidade de relatórios em desenvolvimento", parent=self)
    
    def _show_about(self):
        """Mostra informações sobre o sistema"""
        about_text = """CliniSys-Escola v1.0
        
Sistema de Gestão para Clínica Escola
Desenvolvido para disciplina INE5608 - UFSC

Funcionalidades:
• Gestão de usuários e perfis
• Cadastro e gerenciamento de pacientes  
• Controle de filas de atendimento
• Sistema de autenticação
• Relatórios gerenciais

© 2025 - Projeto Acadêmico"""
        
        messagebox.showinfo("Sobre o CliniSys-Escola", about_text, parent=self)
    
    def _create_stat_card(self, parent, title, value, row, col):
        """Cria um card de estatística"""
        card_frame = ttk.LabelFrame(parent, text=title)
        card_frame.grid(row=row, column=col, padx=10, pady=5, sticky="ew")
        
        value_label = ttk.Label(card_frame, text=value, font=("Arial", 20, "bold"))
        value_label.pack(pady=10)
        
        # Configurar peso das colunas
        parent.columnconfigure(col, weight=1)
    
    def _add_notification(self, message):
        """Adiciona uma notificação"""
        self.notifications_text.config(state="normal")
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.notifications_text.insert("end", f"[{timestamp}] {message}\n")
        self.notifications_text.config(state="disabled")
        self.notifications_text.see("end")
    
    def _open_users_window(self):
        """Abre janela de gerenciamento de usuários"""
        try:
            users_window = UsersApp()
            users_window.mainloop()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir gerenciador de usuários:\n{str(e)}")
    
    def _new_patient(self):
        """Novo paciente - foca na aba de pacientes"""
        self.notebook.select(self.pacientes_tab)
        self.pacientes_tab._novo_paciente()
    
    def _search_patient(self):
        """Buscar paciente - foca na aba de pacientes"""
        self.notebook.select(self.pacientes_tab)
        # Foca no campo de busca
        self.pacientes_tab.var_busca.set("")
        self.after(100, lambda: self.focus_search_entry())
    
    def focus_search_entry(self):
        """Foca no campo de busca de pacientes"""
        # Encontra o entry de busca e foca nele
        for widget in self.pacientes_tab.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Entry) and child.cget('textvariable') == str(self.pacientes_tab.var_busca):
                        child.focus()
                        break
    
    def _show_not_implemented(self):
        """Mostra mensagem de funcionalidade não implementada"""
        messagebox.showinfo("Funcionalidade", "Esta funcionalidade será implementada em versões futuras.")
    



def main():
    """Função principal"""
    try:
        # Inicializar banco de dados primeiro
        print("Inicializando banco de dados...")
        asyncio.run(init_database())
        
        # Mostrar tela de login
        print("Iniciando processo de login...")
        user_data = show_login_dialog(None)
        
        if not user_data:
            print("Login cancelado ou falhou")
            return
        
        print(f"Login bem-sucedido: {user_data.get('nome')} ({user_data.get('perfil')})")
        
        # Criar e executar aplicação principal
        app = CliniSysApp(user_data)
        app.mainloop()
        
    except Exception as e:
        print(f"Erro fatal: {e}")
        import traceback
        traceback.print_exc()


async def init_database():
    """Inicializa o banco de dados"""
    try:
        await init_db_and_seed()
        print("Banco de dados inicializado com sucesso")
    except Exception as e:
        print(f"Erro na inicialização do banco: {str(e)}")
        raise


if __name__ == "__main__":
    main()
