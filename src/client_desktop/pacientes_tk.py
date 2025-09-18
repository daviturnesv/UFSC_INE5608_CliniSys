from __future__ import annotations

import asyncio
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List
from datetime import date

from src.backend.db.database import AsyncSessionLocal
from src.backend.models.paciente import Paciente
from src.backend.models.fila import FilaAtendimento, TipoAtendimento, StatusFila
from src.backend.controllers.paciente_service import (
    create_patient,
    search_patients,
    get_patient_by_id,
    update_patient,
    delete_patient,
    list_all_patients
)
from src.backend.controllers.fila_service import (
    add_to_queue,
    get_waiting_queue,
    get_queue_by_type
)
from src.backend.views.paciente_view import PacienteCreate, PacienteUpdate
from sqlalchemy.exc import IntegrityError
import re


class PacienteDialog(tk.Toplevel):
    """Dialog para criar/editar pacientes"""
    
    def __init__(self, master: tk.Tk | tk.Toplevel, paciente: Optional[dict] = None, on_submit=None):
        super().__init__(master)
        self.title("Paciente" if not paciente else f"Editar Paciente - {paciente['nome']}")
        self.resizable(False, False)
        self.result: Optional[dict] = None
        self._on_submit = on_submit
        self.paciente = paciente
        
        self._create_widgets()
        self._load_data()
        
        self.grab_set()
        self.transient(master)
    
    def _create_widgets(self):
        """Cria os widgets do dialog"""
        row = 0
        
        # Nome
        ttk.Label(self, text="Nome Completo*").grid(row=row, column=0, sticky="e", padx=6, pady=4)
        self.var_nome = tk.StringVar()
        ttk.Entry(self, textvariable=self.var_nome, width=40).grid(row=row, column=1, sticky="w", padx=6, pady=4)
        row += 1
        
        # CPF
        ttk.Label(self, text="CPF*").grid(row=row, column=0, sticky="e", padx=6, pady=4)
        self.var_cpf = tk.StringVar()
        entry_cpf = ttk.Entry(self, textvariable=self.var_cpf, width=20)
        entry_cpf.grid(row=row, column=1, sticky="w", padx=6, pady=4)
        
        # Se estiver editando, desabilita CPF
        if self.paciente:
            entry_cpf.configure(state="disabled")
        row += 1
        
        # Data Nascimento
        ttk.Label(self, text="Data Nascimento*").grid(row=row, column=0, sticky="e", padx=6, pady=4)
        frame_data = ttk.Frame(self)
        frame_data.grid(row=row, column=1, sticky="w", padx=6, pady=4)
        
        self.var_dia = tk.StringVar()
        self.var_mes = tk.StringVar()
        self.var_ano = tk.StringVar()
        
        ttk.Entry(frame_data, textvariable=self.var_dia, width=3).grid(row=0, column=0)
        ttk.Label(frame_data, text="/").grid(row=0, column=1)
        ttk.Entry(frame_data, textvariable=self.var_mes, width=3).grid(row=0, column=2)
        ttk.Label(frame_data, text="/").grid(row=0, column=3)
        ttk.Entry(frame_data, textvariable=self.var_ano, width=5).grid(row=0, column=4)
        
        # Se estiver editando, desabilita data
        if self.paciente:
            for widget in frame_data.winfo_children():
                if isinstance(widget, ttk.Entry):
                    widget.configure(state="disabled")
        row += 1
        
        # Telefone
        ttk.Label(self, text="Telefone").grid(row=row, column=0, sticky="e", padx=6, pady=4)
        self.var_telefone = tk.StringVar()
        ttk.Entry(self, textvariable=self.var_telefone, width=20).grid(row=row, column=1, sticky="w", padx=6, pady=4)
        row += 1
        
        # Status (apenas para edição)
        if self.paciente:
            ttk.Label(self, text="Status").grid(row=row, column=0, sticky="e", padx=6, pady=4)
            self.var_status = tk.StringVar()
            status_values = [
                "Aguardando Triagem",
                "Em Triagem", 
                "Aguardando Consulta",
                "Em Consulta",
                "Atendido",
                "Cancelado"
            ]
            ttk.OptionMenu(self, self.var_status, status_values[0], *status_values).grid(
                row=row, column=1, sticky="w", padx=6, pady=4
            )
            row += 1
        
        # Botões
        frame_btns = ttk.Frame(self)
        frame_btns.grid(row=row, column=0, columnspan=2, pady=12)
        
        ttk.Button(frame_btns, text="Cancelar", command=self.destroy).grid(row=0, column=0, padx=4)
        ttk.Button(frame_btns, text="Salvar", command=self._on_save).grid(row=0, column=1, padx=4)
        
        row += 1
        
        # Label de erro
        self.lbl_erro = ttk.Label(self, text="", foreground="red")
        self.lbl_erro.grid(row=row, column=0, columnspan=2, sticky="w", padx=6)
    
    def _load_data(self):
        """Carrega dados do paciente para edição"""
        if not self.paciente:
            return
        
        self.var_nome.set(self.paciente.get("nome", ""))
        self.var_cpf.set(self.paciente.get("cpf", ""))
        self.var_telefone.set(self.paciente.get("telefone", "") or "")
        
        # Data de nascimento
        data_nasc = self.paciente.get("dataNascimento")
        if data_nasc:
            if isinstance(data_nasc, str):
                # Parse da string de data
                try:
                    ano, mes, dia = data_nasc.split("-")
                    self.var_dia.set(dia)
                    self.var_mes.set(mes)
                    self.var_ano.set(ano)
                except:
                    pass
            elif hasattr(data_nasc, 'day'):
                # Objeto date
                self.var_dia.set(str(data_nasc.day))
                self.var_mes.set(str(data_nasc.month))
                self.var_ano.set(str(data_nasc.year))
        
        if hasattr(self, 'var_status'):
            self.var_status.set(self.paciente.get("statusAtendimento", "Aguardando Triagem"))
    
    def _validate_cpf(self, cpf: str) -> bool:
        """Valida CPF"""
        cpf = re.sub(r'[^0-9]', '', cpf)
        
        if len(cpf) != 11:
            return False
        
        if cpf == cpf[0] * 11:
            return False
        
        # Validação dos dígitos verificadores
        def calc_digit(cpf_partial: str, weights: list[int]) -> int:
            total = sum(int(digit) * weight for digit, weight in zip(cpf_partial, weights))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder
        
        first_digit = calc_digit(cpf[:9], list(range(10, 1, -1)))
        second_digit = calc_digit(cpf[:10], list(range(11, 1, -1)))
        
        return cpf[9] == str(first_digit) and cpf[10] == str(second_digit)
    
    def _on_save(self):
        """Salva o paciente"""
        self.lbl_erro.config(text="")
        
        try:
            # Validações
            nome = self.var_nome.get().strip()
            cpf = re.sub(r'[^0-9]', '', self.var_cpf.get())
            telefone = self.var_telefone.get().strip() or None
            dia = self.var_dia.get().strip()
            mes = self.var_mes.get().strip()
            ano = self.var_ano.get().strip()
            data_nascimento = None
            
            if not nome:
                raise ValueError("Nome é obrigatório")
            
            if not self.paciente:  # Criação - valida CPF e data
                if not cpf or not self._validate_cpf(cpf):
                    raise ValueError("CPF inválido")
                
                if not dia or not mes or not ano:
                    raise ValueError("Data de nascimento é obrigatória")
                
                try:
                    # Validação mais detalhada
                    dia_int = int(dia)
                    mes_int = int(mes)
                    ano_int = int(ano)
                    
                    if dia_int < 1 or dia_int > 31:
                        raise ValueError("Dia deve estar entre 1 e 31")
                    if mes_int < 1 or mes_int > 12:
                        raise ValueError("Mês deve estar entre 1 e 12")
                    if ano_int < 1900 or ano_int > date.today().year:
                        raise ValueError(f"Ano deve estar entre 1900 e {date.today().year}")
                    
                    data_nascimento = date(ano_int, mes_int, dia_int)
                    
                    # Verifica se a data não é no futuro
                    if data_nascimento > date.today():
                        raise ValueError("Data de nascimento não pode ser no futuro")
                        
                except ValueError as ve:
                    if "day is out of range" in str(ve):
                        raise ValueError("Dia inválido para este mês")
                    elif "month must be" in str(ve):
                        raise ValueError("Mês inválido")
                    elif "year" in str(ve):
                        raise ValueError("Ano inválido")
                    else:
                        raise ve
            
            # Executa a operação
            if self.paciente:
                # Atualização
                status = getattr(self, 'var_status', None)
                status_value = status.get() if status else None
                
                result = asyncio.run(self._update_patient(
                    self.paciente['id'],
                    nome,
                    telefone,
                    status_value
                ))
            else:
                # Criação
                if data_nascimento is None:
                    raise ValueError("Data de nascimento é obrigatória")
                result = asyncio.run(self._create_patient(nome, cpf, data_nascimento, telefone))
            
            self.result = result
            
            if self._on_submit:
                self._on_submit(result)
            
            self.destroy()
            
        except Exception as e:
            self.lbl_erro.config(text=str(e))
    
    async def _create_patient(self, nome: str, cpf: str, data_nascimento: date, telefone: Optional[str]) -> dict:
        """Cria novo paciente"""
        async with AsyncSessionLocal() as session:
            patient_data = PacienteCreate(
                nome=nome,
                cpf=cpf,
                dataNascimento=data_nascimento,
                telefone=telefone
            )
            
            paciente = await create_patient(session, patient_data)
            
            return {
                "id": paciente.id,
                "nome": paciente.nome,
                "cpf": paciente.cpf,
                "dataNascimento": paciente.dataNascimento,
                "telefone": paciente.telefone,
                "statusAtendimento": paciente.statusAtendimento
            }
    
    async def _update_patient(self, patient_id: int, nome: str, telefone: Optional[str], status: Optional[str]) -> dict:
        """Atualiza paciente existente"""
        async with AsyncSessionLocal() as session:
            patient_data = PacienteUpdate(
                nome=nome,
                telefone=telefone,
                statusAtendimento=status
            )
            
            paciente = await update_patient(session, patient_id, patient_data)
            
            if not paciente:
                raise ValueError("Paciente não encontrado")
            
            return {
                "id": paciente.id,
                "nome": paciente.nome,
                "cpf": paciente.cpf,
                "dataNascimento": paciente.dataNascimento,
                "telefone": paciente.telefone,
                "statusAtendimento": paciente.statusAtendimento
            }


class PacientesTab(ttk.Frame):
    """Tab para gerenciamento de pacientes"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.pacientes: List[dict] = []
        
        self._create_widgets()
        self._load_pacientes()
    
    def _create_widgets(self):
        """Cria os widgets da tab"""
        # Frame superior com botões e busca
        frame_top = ttk.Frame(self)
        frame_top.pack(fill="x", padx=8, pady=4)
        
        # Botões
        ttk.Button(frame_top, text="Novo Paciente", command=self._novo_paciente).pack(side="left", padx=2)
        ttk.Button(frame_top, text="Editar", command=self._editar_paciente).pack(side="left", padx=2)
        ttk.Button(frame_top, text="Excluir", command=self._excluir_paciente).pack(side="left", padx=2)
        ttk.Button(frame_top, text="Atualizar", command=self._load_pacientes).pack(side="left", padx=2)
        
        ttk.Separator(frame_top, orient="vertical").pack(side="left", fill="y", padx=8)
        
        # Busca
        ttk.Label(frame_top, text="Buscar:").pack(side="left", padx=2)
        self.var_busca = tk.StringVar()
        entry_busca = ttk.Entry(frame_top, textvariable=self.var_busca, width=20)
        entry_busca.pack(side="left", padx=2)
        entry_busca.bind("<Return>", lambda e: self._buscar_pacientes())
        ttk.Button(frame_top, text="Buscar", command=self._buscar_pacientes).pack(side="left", padx=2)
        ttk.Button(frame_top, text="Limpar", command=self._limpar_busca).pack(side="left", padx=2)
        
        # Treeview para listar pacientes
        frame_tree = ttk.Frame(self)
        frame_tree.pack(fill="both", expand=True, padx=8, pady=4)
        
        # Colunas
        columns = ("ID", "Nome", "CPF", "Telefone", "Data Nasc.", "Status")
        self.tree = ttk.Treeview(frame_tree, columns=columns, show="headings", height=15)
        
        # Configurar colunas
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nome", text="Nome")
        self.tree.heading("CPF", text="CPF")
        self.tree.heading("Telefone", text="Telefone")
        self.tree.heading("Data Nasc.", text="Data Nasc.")
        self.tree.heading("Status", text="Status")
        
        self.tree.column("ID", width=50)
        self.tree.column("Nome", width=200)
        self.tree.column("CPF", width=120)
        self.tree.column("Telefone", width=120)
        self.tree.column("Data Nasc.", width=100)
        self.tree.column("Status", width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame_tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind duplo clique para editar
        self.tree.bind("<Double-1>", lambda e: self._editar_paciente())
    
    def _load_pacientes(self):
        """Carrega lista de pacientes"""
        try:
            self.pacientes = asyncio.run(self._fetch_pacientes())
            self._update_tree()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar pacientes: {str(e)}")
    
    async def _fetch_pacientes(self) -> List[dict]:
        """Busca pacientes no banco"""
        async with AsyncSessionLocal() as session:
            pacientes = await list_all_patients(session, limit=1000)
            
            result = []
            for p in pacientes:
                result.append({
                    "id": p.id,
                    "nome": p.nome,
                    "cpf": p.cpf,
                    "telefone": p.telefone,
                    "dataNascimento": p.dataNascimento,
                    "statusAtendimento": p.statusAtendimento
                })
            
            return result
    
    def _buscar_pacientes(self):
        """Busca pacientes por termo"""
        termo = self.var_busca.get().strip()
        if not termo:
            self._load_pacientes()
            return
        
        try:
            self.pacientes = asyncio.run(self._fetch_search_pacientes(termo))
            self._update_tree()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro na busca: {str(e)}")
    
    async def _fetch_search_pacientes(self, termo: str) -> List[dict]:
        """Busca pacientes por termo"""
        async with AsyncSessionLocal() as session:
            pacientes = await search_patients(session, termo, limit=1000)
            
            result = []
            for p in pacientes:
                result.append({
                    "id": p.id,
                    "nome": p.nome,
                    "cpf": p.cpf,
                    "telefone": p.telefone,
                    "dataNascimento": p.dataNascimento,
                    "statusAtendimento": p.statusAtendimento
                })
            
            return result
    
    def _limpar_busca(self):
        """Limpa busca e recarrega todos"""
        self.var_busca.set("")
        self._load_pacientes()
    
    def _update_tree(self):
        """Atualiza a TreeView"""
        # Limpa itens existentes
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Adiciona pacientes
        for paciente in self.pacientes:
            data_nasc = paciente["dataNascimento"]
            if hasattr(data_nasc, 'strftime'):
                data_str = data_nasc.strftime("%d/%m/%Y")
            else:
                data_str = str(data_nasc)
            
            self.tree.insert("", "end", values=(
                paciente["id"],
                paciente["nome"],
                paciente["cpf"],
                paciente["telefone"] or "",
                data_str,
                paciente["statusAtendimento"]
            ))
    
    def _get_selected_paciente(self) -> Optional[dict]:
        """Retorna paciente selecionado"""
        selection = self.tree.selection()
        if not selection:
            return None
        
        item = self.tree.item(selection[0])
        paciente_id = int(item["values"][0])
        
        for paciente in self.pacientes:
            if paciente["id"] == paciente_id:
                return paciente
        
        return None
    
    def _novo_paciente(self):
        """Abre dialog para novo paciente"""
        dialog = PacienteDialog(self.winfo_toplevel(), on_submit=self._on_paciente_saved)
    
    def _editar_paciente(self):
        """Abre dialog para editar paciente"""
        paciente = self._get_selected_paciente()
        if not paciente:
            messagebox.showwarning("Atenção", "Selecione um paciente para editar")
            return
        
        dialog = PacienteDialog(self.winfo_toplevel(), paciente=paciente, on_submit=self._on_paciente_saved)
    
    def _excluir_paciente(self):
        """Exclui paciente selecionado"""
        paciente = self._get_selected_paciente()
        if not paciente:
            messagebox.showwarning("Atenção", "Selecione um paciente para excluir")
            return
        
        if not messagebox.askyesno("Confirmar", f"Excluir paciente {paciente['nome']}?"):
            return
        
        try:
            asyncio.run(self._delete_paciente(paciente["id"]))
            messagebox.showinfo("Sucesso", "Paciente excluído com sucesso")
            self._load_pacientes()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir paciente: {str(e)}")
    
    async def _delete_paciente(self, paciente_id: int):
        """Exclui paciente do banco"""
        async with AsyncSessionLocal() as session:
            success = await delete_patient(session, paciente_id)
            if not success:
                raise ValueError("Paciente não encontrado")
    
    def _on_paciente_saved(self, paciente: dict):
        """Callback quando paciente é salvo"""
        messagebox.showinfo("Sucesso", f"Paciente {paciente['nome']} salvo com sucesso!")
        self._load_pacientes()


# Função para testar a interface isoladamente
def main_pacientes():
    """Função principal para testar interface de pacientes"""
    import asyncio
    from src.backend.db.database import engine, Base
    
    async def init_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    asyncio.run(init_db())
    
    root = tk.Tk()
    root.title("Gerenciar Pacientes - CliniSys")
    root.geometry("1000x600")
    
    tab = PacientesTab(root)
    tab.pack(fill="both", expand=True)
    
    root.mainloop()


if __name__ == "__main__":
    main_pacientes()
