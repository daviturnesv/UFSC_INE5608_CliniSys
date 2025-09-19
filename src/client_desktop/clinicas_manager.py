#!/usr/bin/env python3
"""
Interface para gerenciamento de clínicas
Permite ao administrador criar, editar e remover clínicas
"""

from __future__ import annotations

import asyncio
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List, Dict, Any

from src.backend.db.database import AsyncSessionLocal
from src.backend.models.clinica import Clinica
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError


class ClinicasApp(tk.Toplevel):
    """Interface para gerenciamento de clínicas"""
    
    def __init__(self, master: tk.Tk):
        super().__init__(master)
        self.title("CliniSys - Gerenciamento de Clínicas")
        self.geometry("800x600")
        self.resizable(True, True)
        
        # Centralizar janela
        self.transient(master)
        
        # Variáveis de controle
        self.clinicas_data: List[Dict[str, Any]] = []
        self.selected_clinica_id: Optional[int] = None
        self.edit_mode = False
        
        # Variáveis dos campos
        self.var_id = tk.StringVar()
        self.var_codigo = tk.StringVar()
        self.var_nome = tk.StringVar()
        
        self._create_widgets()
        self._center_window()
        
        # Carregar dados iniciais
        self.run_async(self._load_clinicas())
    
    def _center_window(self):
        """Centraliza a janela na tela"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Cria os widgets da interface"""
        # Frame principal
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, text="Gerenciamento de Clínicas", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Frame de controles superiores
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill="x", pady=(0, 10))
        
        # Botões de ação
        ttk.Button(controls_frame, text="🔄 Atualizar Lista", 
                  command=self._refresh_list).pack(side="left", padx=(0, 5))
        ttk.Button(controls_frame, text="➕ Nova Clínica", 
                  command=self._new_clinica).pack(side="left", padx=(0, 5))
        
        # Frame principal dividido
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True)
        
        # Frame esquerdo - Lista de clínicas
        left_frame = ttk.LabelFrame(content_frame, text="Lista de Clínicas")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Treeview para lista de clínicas
        columns = ("id", "codigo", "nome")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=15)
        
        # Configurar colunas
        self.tree.heading("id", text="ID")
        self.tree.heading("codigo", text="Código")
        self.tree.heading("nome", text="Nome")
        
        self.tree.column("id", width=50)
        self.tree.column("codigo", width=100)
        self.tree.column("nome", width=200)
        
        # Scrollbar para treeview
        tree_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")
        
        # Bind evento de seleção
        self.tree.bind("<<TreeviewSelect>>", self._on_select_clinica)
        
        # Frame direito - Detalhes da clínica
        right_frame = ttk.LabelFrame(content_frame, text="Detalhes da Clínica")
        right_frame.pack(side="right", fill="y", padx=(10, 0))
        
        # Campos de detalhes
        details_frame = ttk.Frame(right_frame, padding="10")
        details_frame.pack(fill="both", expand=True)
        
        row = 0
        
        # ID (readonly)
        ttk.Label(details_frame, text="ID:").grid(row=row, column=0, sticky="w", pady=2)
        self.entry_id = ttk.Entry(details_frame, textvariable=self.var_id, 
                                 state="readonly", width=30)
        self.entry_id.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1
        
        # Código
        ttk.Label(details_frame, text="Código:").grid(row=row, column=0, sticky="w", pady=2)
        self.entry_codigo = ttk.Entry(details_frame, textvariable=self.var_codigo, 
                                     state="readonly", width=30)
        self.entry_codigo.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1
        
        # Nome
        ttk.Label(details_frame, text="Nome:").grid(row=row, column=0, sticky="w", pady=2)
        self.entry_nome = ttk.Entry(details_frame, textvariable=self.var_nome, 
                                   state="readonly", width=30)
        self.entry_nome.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1
        
        # Frame de botões
        buttons_frame = ttk.Frame(details_frame)
        buttons_frame.grid(row=row, column=0, columnspan=2, pady=20, sticky="ew")
        
        # Botões de ação
        self.btn_edit = ttk.Button(buttons_frame, text="✏️ Editar", 
                                  command=self._toggle_edit_mode)
        self.btn_edit.pack(side="left", padx=(0, 5))
        
        self.btn_save = ttk.Button(buttons_frame, text="💾 Salvar", 
                                  command=self._save_clinica, state="disabled")
        self.btn_save.pack(side="left", padx=(0, 5))
        
        self.btn_cancel = ttk.Button(buttons_frame, text="❌ Cancelar", 
                                    command=self._cancel_edit, state="disabled")
        self.btn_cancel.pack(side="left", padx=(0, 5))
        
        self.btn_delete = ttk.Button(buttons_frame, text="🗑️ Excluir", 
                                    command=self._delete_clinica)
        self.btn_delete.pack(side="left", padx=(0, 5))
    
    def run_async(self, coro):
        """Executa corrotina de forma síncrona"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Se já há um loop rodando, criar uma nova task
                task = loop.create_task(coro)
                return task
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            # Se não há loop, criar um novo
            return asyncio.run(coro)
    
    async def _load_clinicas(self):
        """Carrega lista de clínicas do banco"""
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(Clinica).order_by(Clinica.nome)
                result = await session.execute(stmt)
                clinicas = result.scalars().all()
                
                self.clinicas_data = [
                    {
                        "id": c.id,
                        "codigo": c.codigo,
                        "nome": c.nome
                    }
                    for c in clinicas
                ]
                
                self._update_tree()
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar clínicas: {str(e)}")
    
    def _update_tree(self):
        """Atualiza a árvore com dados das clínicas"""
        # Limpar árvore
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Adicionar clínicas
        for clinica in self.clinicas_data:
            self.tree.insert("", "end", values=(
                clinica["id"],
                clinica["codigo"],
                clinica["nome"]
            ))
    
    def _on_select_clinica(self, event):
        """Evento de seleção de clínica na lista"""
        selection = self.tree.selection()
        if not selection:
            self._clear_details()
            return
        
        item = self.tree.item(selection[0])
        values = item["values"]
        
        if values:
            self.selected_clinica_id = int(values[0])
            self._load_clinica_details(self.selected_clinica_id)
    
    def _load_clinica_details(self, clinica_id: int):
        """Carrega detalhes de uma clínica específica"""
        clinica_data = next((c for c in self.clinicas_data if c["id"] == clinica_id), None)
        
        if clinica_data:
            self.var_id.set(str(clinica_data["id"]))
            self.var_codigo.set(clinica_data["codigo"])
            self.var_nome.set(clinica_data["nome"])
            
            # Habilitar botões
            self.btn_edit.config(state="normal")
            self.btn_delete.config(state="normal")
    
    def _clear_details(self):
        """Limpa os campos de detalhes"""
        self.var_id.set("")
        self.var_codigo.set("")
        self.var_nome.set("")
        self.selected_clinica_id = None
        
        # Desabilitar botões
        self.btn_edit.config(state="disabled")
        self.btn_delete.config(state="disabled")
    
    def _toggle_edit_mode(self):
        """Alterna modo de edição"""
        self.edit_mode = True
        
        # Habilitar campos
        self.entry_codigo.config(state="normal")
        self.entry_nome.config(state="normal")
        
        # Alterar botões
        self.btn_edit.config(state="disabled")
        self.btn_save.config(state="normal")
        self.btn_cancel.config(state="normal")
        self.btn_delete.config(state="disabled")
    
    def _cancel_edit(self):
        """Cancela edição"""
        self.edit_mode = False
        
        # Recarregar dados originais
        if self.selected_clinica_id:
            self._load_clinica_details(self.selected_clinica_id)
        
        # Desabilitar campos
        self.entry_codigo.config(state="readonly")
        self.entry_nome.config(state="readonly")
        
        # Alterar botões
        self.btn_edit.config(state="normal")
        self.btn_save.config(state="disabled")
        self.btn_cancel.config(state="disabled")
        self.btn_delete.config(state="normal")
    
    def _save_clinica(self):
        """Salva alterações da clínica"""
        try:
            codigo = self.var_codigo.get().strip()
            nome = self.var_nome.get().strip()
            
            if not codigo or not nome:
                messagebox.showwarning("Atenção", "Código e nome são obrigatórios")
                return
            
            if self.selected_clinica_id:
                # Atualizar clínica existente
                self.run_async(self._update_clinica(self.selected_clinica_id, codigo, nome))
            else:
                # Nova clínica
                self.run_async(self._create_clinica(codigo, nome))
            
            self._cancel_edit()
            self.run_async(self._load_clinicas())
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar clínica: {str(e)}")
    
    async def _create_clinica(self, codigo: str, nome: str):
        """Cria nova clínica"""
        async with AsyncSessionLocal() as session:
            try:
                clinica = Clinica(codigo=codigo, nome=nome)
                session.add(clinica)
                await session.commit()
                messagebox.showinfo("Sucesso", "Clínica criada com sucesso!")
            except IntegrityError:
                await session.rollback()
                raise ValueError("Código da clínica já existe")
    
    async def _update_clinica(self, clinica_id: int, codigo: str, nome: str):
        """Atualiza clínica existente"""
        async with AsyncSessionLocal() as session:
            try:
                stmt = (
                    update(Clinica)
                    .where(Clinica.id == clinica_id)
                    .values(codigo=codigo, nome=nome)
                )
                result = await session.execute(stmt)
                await session.commit()
                
                if result.rowcount == 0:
                    raise ValueError("Clínica não encontrada")
                
                messagebox.showinfo("Sucesso", "Clínica atualizada com sucesso!")
            except IntegrityError:
                await session.rollback()
                raise ValueError("Código da clínica já existe")
    
    def _delete_clinica(self):
        """Exclui clínica selecionada"""
        if not self.selected_clinica_id:
            return
        
        clinica_nome = self.var_nome.get()
        
        if messagebox.askyesno("Confirmar", 
                              f"Tem certeza que deseja excluir a clínica '{clinica_nome}'?\n\n"
                              "ATENÇÃO: Esta ação não pode ser desfeita e pode afetar "
                              "usuários vinculados a esta clínica."):
            try:
                self.run_async(self._remove_clinica(self.selected_clinica_id))
                self._clear_details()
                self.run_async(self._load_clinicas())
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao excluir clínica: {str(e)}")
    
    async def _remove_clinica(self, clinica_id: int):
        """Remove clínica do banco"""
        async with AsyncSessionLocal() as session:
            try:
                stmt = delete(Clinica).where(Clinica.id == clinica_id)
                result = await session.execute(stmt)
                await session.commit()
                
                if result.rowcount == 0:
                    raise ValueError("Clínica não encontrada")
                
                messagebox.showinfo("Sucesso", "Clínica excluída com sucesso!")
            except IntegrityError:
                await session.rollback()
                raise ValueError("Não é possível excluir: existem usuários vinculados a esta clínica")
    
    def _new_clinica(self):
        """Prepara interface para nova clínica"""
        self._clear_details()
        self.selected_clinica_id = None
        self._toggle_edit_mode()
        self.entry_codigo.focus()
    
    def _refresh_list(self):
        """Atualiza lista de clínicas"""
        self.run_async(self._load_clinicas())


def show_clinicas_manager(master: tk.Tk):
    """Função para mostrar o gerenciador de clínicas"""
    app = ClinicasApp(master)
    return app


if __name__ == "__main__":
    # Teste standalone
    root = tk.Tk()
    root.withdraw()  # Esconder janela principal
    app = ClinicasApp(root)
    app.mainloop()