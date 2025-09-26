"""
Interface Visual para Sistema de Agendamento de Consultas
Baseada em padrões de sistemas clínicos e hospitalares
Implementa RF06 e RF07 do CliniSys-Escola
"""

from __future__ import annotations

import asyncio
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Optional
import calendar
from tkcalendar import DateEntry

# Imports do sistema
from sqlalchemy import select
from ..backend.db.database import AsyncSessionLocal
from ..backend.controllers.agendamento_service import AgendamentoService
from ..backend.models.consulta import Consulta, StatusConsulta, TipoConsulta
from ..backend.models.paciente import Paciente
from ..backend.models.usuario import UsuarioSistema, PerfilUsuario


class AgendamentoVisualApp(tk.Toplevel):
    """
    Aplicação visual para gerenciamento de agendamento de consultas
    Interface baseada em sistemas clínicos padrão do mercado
    """
    
    def __init__(self, parent=None, current_user: Dict[str, Any] = None):
        super().__init__(parent)
        
        self.parent = parent
        self.current_user = current_user or {}
        
        self.title("CliniSys - Agendamento de Consultas")
        self.geometry("1400x800")
        
        # Variáveis de controle
        self.consultas_cache = []
        self.pacientes_cache = {}
        self.horarios_disponiveis = []
        
        self._setup_window()
        self._create_interface()
        self._carregar_dados_iniciais()
    
    def _setup_window(self):
        """Configurações iniciais da janela"""
        self.transient(self.parent)
        self.grab_set() if self.parent else None
        
        # Centralizar janela
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        # Configurar fechamento
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_interface(self):
        """Cria a interface principal"""
        
        # Frame principal com padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Título
        title_label = ttk.Label(
            main_frame, 
            text="🗓️ Sistema de Agendamento de Consultas", 
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Notebook para diferentes funcionalidades
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, columnspan=3, sticky="nsew")
        
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Abas baseadas no perfil do usuário
        self._create_agendamento_tab()
        self._create_minhas_consultas_tab()
        
        if self.current_user.get('perfil') in ['admin', 'professor']:
            self._create_visualizacao_geral_tab()
        
        # Status bar
        self.status_bar = ttk.Label(
            main_frame, 
            text="Pronto", 
            relief="sunken", 
            anchor="w"
        )
        self.status_bar.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10, 0))
    
    def _create_agendamento_tab(self):
        """Aba para novo agendamento"""
        agendamento_frame = ttk.Frame(self.notebook)
        self.notebook.add(agendamento_frame, text="📅 Novo Agendamento")
        
        # Frame principal com scroll
        canvas = tk.Canvas(agendamento_frame)
        scrollbar = ttk.Scrollbar(agendamento_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # === SEÇÃO 1: SELEÇÃO DE PACIENTE ===
        paciente_section = ttk.LabelFrame(scrollable_frame, text="👤 Seleção de Paciente")
        paciente_section.pack(fill="x", padx=10, pady=5)
        
        # Campo de busca de paciente
        ttk.Label(paciente_section, text="Buscar Paciente: *").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        # Combobox com autocomplete para pacientes
        self.paciente_var = tk.StringVar()
        self.paciente_combo = ttk.Combobox(
            paciente_section, 
            textvariable=self.paciente_var,
            width=50,
            state="readonly"
        )
        self.paciente_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.paciente_combo.bind('<<ComboboxSelected>>', self._on_paciente_selected)
        
        # Botão para buscar paciente
        ttk.Button(
            paciente_section,
            text="🔍 Buscar",
            command=self._buscar_pacientes
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # Info do paciente selecionado
        self.paciente_info_var = tk.StringVar(value="Nenhum paciente selecionado")
        ttk.Label(
            paciente_section, 
            textvariable=self.paciente_info_var,
            foreground="blue"
        ).grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        
        paciente_section.grid_columnconfigure(1, weight=1)
        
        # === SEÇÃO 2: DADOS DA CONSULTA ===
        consulta_section = ttk.LabelFrame(scrollable_frame, text="🏥 Dados da Consulta")
        consulta_section.pack(fill="x", padx=10, pady=5)
        
        # Linha 1: Tipo de consulta e data
        ttk.Label(consulta_section, text="Tipo de Consulta: *").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.tipo_consulta_var = tk.StringVar()
        tipo_combo = ttk.Combobox(
            consulta_section,
            textvariable=self.tipo_consulta_var,
            values=self._get_tipos_consulta_disponiveis(),
            state="readonly",
            width=20
        )
        tipo_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(consulta_section, text="Data da Consulta: *").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        
        # DateEntry para seleção de data
        self.data_var = tk.StringVar()
        self.date_entry = DateEntry(
            consulta_section,
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='dd/mm/yyyy',
            mindate=date.today(),
            firstweekday='sunday'
        )
        self.date_entry.grid(row=0, column=3, padx=5, pady=5)
        self.date_entry.bind('<<DateEntrySelected>>', self._on_data_selected)
        
        # Linha 2: Horário
        ttk.Label(consulta_section, text="Horário: *").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        self.horario_var = tk.StringVar()
        self.horario_combo = ttk.Combobox(
            consulta_section,
            textvariable=self.horario_var,
            state="readonly",
            width=15
        )
        self.horario_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(consulta_section, text="Duração (min):").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        
        self.duracao_var = tk.StringVar(value="60")
        duracao_spin = ttk.Spinbox(
            consulta_section,
            from_=30,
            to=120,
            increment=30,
            textvariable=self.duracao_var,
            width=10
        )
        duracao_spin.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        # Botão para atualizar horários disponíveis
        ttk.Button(
            consulta_section,
            text="🔄 Atualizar Horários",
            command=self._carregar_horarios_disponiveis
        ).grid(row=2, column=0, columnspan=2, padx=5, pady=10, sticky="w")
        
        # Status dos horários
        self.horarios_status_var = tk.StringVar(value="Selecione uma data para ver horários disponíveis")
        ttk.Label(
            consulta_section,
            textvariable=self.horarios_status_var,
            foreground="gray"
        ).grid(row=2, column=2, columnspan=2, padx=5, pady=10, sticky="w")
        
        consulta_section.grid_columnconfigure(1, weight=1)
        consulta_section.grid_columnconfigure(3, weight=1)
        
        # === SEÇÃO 3: INFORMAÇÕES COMPLEMENTARES ===
        info_section = ttk.LabelFrame(scrollable_frame, text="📝 Informações Adicionais")
        info_section.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Motivo da consulta
        ttk.Label(info_section, text="Motivo da Consulta:").grid(row=0, column=0, sticky="nw", padx=5, pady=5)
        
        self.motivo_text = tk.Text(info_section, height=3, width=60)
        self.motivo_text.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Observações
        ttk.Label(info_section, text="Observações:").grid(row=1, column=0, sticky="nw", padx=5, pady=5)
        
        self.observacoes_text = tk.Text(info_section, height=3, width=60)
        self.observacoes_text.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        info_section.grid_columnconfigure(1, weight=1)
        
        # === BOTÕES DE AÇÃO ===
        buttons_frame = ttk.Frame(scrollable_frame)
        buttons_frame.pack(fill="x", padx=10, pady=20)
        
        ttk.Button(
            buttons_frame,
            text="✅ Agendar Consulta",
            command=self._agendar_consulta,
            style="Accent.TButton"
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            buttons_frame,
            text="🧹 Limpar Formulário",
            command=self._limpar_formulario
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            buttons_frame,
            text="❌ Fechar",
            command=self._on_closing
        ).pack(side="right")
    
    def _create_minhas_consultas_tab(self):
        """Aba para visualizar consultas do usuário"""
        consultas_frame = ttk.Frame(self.notebook)
        self.notebook.add(consultas_frame, text="📋 Minhas Consultas")
        
        # Filtros
        filtros_frame = ttk.LabelFrame(consultas_frame, text="🔍 Filtros")
        filtros_frame.pack(fill="x", padx=10, pady=5)
        
        # Período
        ttk.Label(filtros_frame, text="Período:").grid(row=0, column=0, padx=5, pady=5)
        
        self.periodo_var = tk.StringVar(value="Próximos 30 dias")
        periodo_combo = ttk.Combobox(
            filtros_frame,
            textvariable=self.periodo_var,
            values=[
                "Hoje",
                "Próximos 7 dias", 
                "Próximos 30 dias",
                "Todos os agendamentos",
                "Período personalizado"
            ],
            state="readonly"
        )
        periodo_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Status
        ttk.Label(filtros_frame, text="Status:").grid(row=0, column=2, padx=5, pady=5)
        
        self.status_filtro_var = tk.StringVar(value="Todos")
        status_combo = ttk.Combobox(
            filtros_frame,
            textvariable=self.status_filtro_var,
            values=[
                "Todos",
                "Agendada",
                "Confirmada", 
                "Em Andamento",
                "Concluída",
                "Cancelada",
                "Falta"
            ],
            state="readonly"
        )
        status_combo.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Button(
            filtros_frame,
            text="🔄 Atualizar Lista",
            command=self._carregar_minhas_consultas
        ).grid(row=0, column=4, padx=10, pady=5)
        
        # Lista de consultas
        lista_frame = ttk.LabelFrame(consultas_frame, text="📅 Lista de Consultas")
        lista_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Treeview para listar consultas
        columns = ("Data", "Horário", "Paciente", "Tipo", "Status", "Ações")
        self.consultas_tree = ttk.Treeview(
            lista_frame, 
            columns=columns, 
            show="headings",
            height=15
        )
        
        # Configurar colunas
        self.consultas_tree.heading("Data", text="Data")
        self.consultas_tree.heading("Horário", text="Horário")
        self.consultas_tree.heading("Paciente", text="Paciente")
        self.consultas_tree.heading("Tipo", text="Tipo")
        self.consultas_tree.heading("Status", text="Status")
        self.consultas_tree.heading("Ações", text="Ações")
        
        # Larguras das colunas
        self.consultas_tree.column("Data", width=100)
        self.consultas_tree.column("Horário", width=100)
        self.consultas_tree.column("Paciente", width=200)
        self.consultas_tree.column("Tipo", width=120)
        self.consultas_tree.column("Status", width=100)
        self.consultas_tree.column("Ações", width=150)
        
        # Scrollbar para a lista
        tree_scroll = ttk.Scrollbar(lista_frame, orient="vertical", command=self.consultas_tree.yview)
        self.consultas_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.consultas_tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        
        # Menu de contexto para ações
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="📝 Ver Detalhes", command=self._ver_detalhes_consulta)
        self.context_menu.add_command(label="✏️ Reagendar", command=self._reagendar_consulta)
        self.context_menu.add_command(label="❌ Cancelar", command=self._cancelar_consulta)
        self.context_menu.add_command(label="⚠️ Registrar Falta", command=self._registrar_falta)
        
        self.consultas_tree.bind("<Button-3>", self._show_context_menu)
        self.consultas_tree.bind("<Double-1>", self._ver_detalhes_consulta)
    
    def _create_visualizacao_geral_tab(self):
        """Aba para visualização geral (admin/professor)"""
        geral_frame = ttk.Frame(self.notebook)
        self.notebook.add(geral_frame, text="👥 Visualização Geral")
        
        ttk.Label(
            geral_frame,
            text="🚧 Funcionalidade em desenvolvimento",
            font=("Arial", 12)
        ).pack(expand=True)
        
        ttk.Label(
            geral_frame,
            text="Esta aba permitirá visualizar todas as consultas da clínica\ne aprovar solicitações de alta/desvinculação.",
            justify="center"
        ).pack(expand=True)
    
    # === MÉTODOS DE DADOS ===
    
    def _carregar_dados_iniciais(self):
        """Carrega dados iniciais da aplicação"""
        self._update_status("Carregando dados iniciais...")
        
        # Executar em thread separada
        import threading
        def carregar():
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                loop.run_until_complete(self._async_carregar_dados_iniciais())
                loop.close()
            except Exception as e:
                print(f"Erro no carregamento: {e}")
                self.after(0, lambda: self._update_status(f"Erro: {str(e)}"))
        
        # Agendar execução após UI estar pronta
        self.after(100, lambda: threading.Thread(target=carregar, daemon=True).start())
    
    async def _async_carregar_dados_iniciais(self):
        """Carrega dados iniciais de forma assíncrona"""
        try:
            await self._buscar_pacientes()
            self._update_status("Dados carregados com sucesso")
        except Exception as e:
            self._update_status(f"Erro: {str(e)}")
    
    def _buscar_pacientes(self):
        """Busca e carrega lista de pacientes de forma não-bloqueante"""
        self._update_status("Buscando pacientes...")
        
        # Executar busca em thread separada
        import threading
        def buscar():
            try:
                import asyncio
                # Criar novo loop para esta thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Executar busca
                loop.run_until_complete(self._async_buscar_pacientes())
                loop.close()
            except Exception as e:
                print(f"Erro na busca: {e}")
                self.after(0, lambda: self._update_status(f"Erro: {str(e)}"))
        
        thread = threading.Thread(target=buscar, daemon=True)
        thread.start()
    
    async def _async_buscar_pacientes(self):
        """Busca pacientes no banco de dados"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Paciente)
                    .order_by(Paciente.nome)
                )
                pacientes = result.scalars().all()
                
                # Filtrar pacientes que podem agendar consultas
                pacientes_validos = []
                for p in pacientes:
                    # Permitir agendamento para vários status
                    if p.statusAtendimento in [
                        "Aguardando Triagem",
                        "Triado - Aguardando Consulta", 
                        "Disponível",
                        "Consulta Agendada",
                        "Em Atendimento",
                        "Finalizado"
                    ]:
                        pacientes_validos.append(p)
                
                # Atualizar cache
                self.pacientes_cache = {p.id: p for p in pacientes_validos}
                
                # Agendar atualização da UI no thread principal
                nomes_pacientes = [f"{p.nome} - CPF: {p.cpf}" for p in pacientes_validos]
                self.after(0, lambda: self._update_pacientes_ui(nomes_pacientes, len(pacientes_validos)))
                
        except Exception as e:
            print(f"Erro detalhado na busca de pacientes: {e}")
            # Agendar atualização de erro na UI
            self.after(0, lambda: (
                self._update_status(f"Erro ao buscar pacientes: {str(e)}"),
                messagebox.showerror("Erro", f"Erro ao buscar pacientes: {str(e)}")
            ))
    
    def _update_pacientes_ui(self, nomes_pacientes, count):
        """Atualiza interface com lista de pacientes (executado no thread principal)"""
        try:
            self.paciente_combo['values'] = nomes_pacientes
            self._update_status(f"{count} pacientes disponíveis para agendamento")
        except Exception as e:
            print(f"Erro ao atualizar UI de pacientes: {e}")
    
    def _carregar_horarios_disponiveis(self):
        """Carrega horários disponíveis para a data selecionada"""
        try:
            data_selecionada = self.date_entry.get_date()
            duracao = int(self.duracao_var.get())
            
            # Executar em thread separada
            import threading
            def carregar_horarios():
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    loop.run_until_complete(self._async_carregar_horarios(data_selecionada, duracao))
                    loop.close()
                except Exception as e:
                    print(f"Erro ao carregar horários: {e}")
                    self.after(0, lambda: self._update_status("Erro ao carregar horários"))
            
            threading.Thread(target=carregar_horarios, daemon=True).start()
            
        except Exception as e:
            self._update_status(f"Erro ao carregar horários: {str(e)}")
    
    async def _async_carregar_horarios(self, data_consulta: date, duracao_minutos: int):
        """Carrega horários disponíveis de forma assíncrona"""
        try:
            async with AsyncSessionLocal() as session:
                horarios = await AgendamentoService.obter_horarios_disponiveis(
                    session, data_consulta, duracao_minutos
                )
                
                # Formatar horários para exibição
                horarios_formatados = [h.strftime("%H:%M") for h in horarios]
                self.horario_combo['values'] = horarios_formatados
                
                if horarios_formatados:
                    self.horarios_status_var.set(f"{len(horarios_formatados)} horários disponíveis")
                    self.horario_combo.current(0)  # Selecionar primeiro horário
                else:
                    self.horarios_status_var.set("Nenhum horário disponível para esta data")
                    self.horario_combo.set("")
                    
        except Exception as e:
            self.horarios_status_var.set("Erro ao carregar horários")
            messagebox.showerror("Erro", f"Erro ao carregar horários: {str(e)}")
    
    def _carregar_minhas_consultas(self):
        """Carrega consultas do usuário atual"""
        if self.current_user.get('perfil') != 'aluno':
            return
            
        # Executar em thread separada
        import threading
        def carregar_consultas():
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                loop.run_until_complete(self._async_carregar_minhas_consultas())
                loop.close()
            except Exception as e:
                print(f"Erro ao carregar consultas: {e}")
                self.after(0, lambda: self._update_status("Erro ao carregar consultas"))
        
        threading.Thread(target=carregar_consultas, daemon=True).start()
    
    async def _async_carregar_minhas_consultas(self):
        """Carrega consultas do usuário de forma assíncrona"""
        try:
            async with AsyncSessionLocal() as session:
                # Definir filtros baseado na seleção
                data_inicio, data_fim = self._calcular_periodo_filtro()
                status_filtro = self._calcular_status_filtro()
                
                consultas = await AgendamentoService.listar_consultas_aluno(
                    session=session,
                    aluno_id=self.current_user['id'],
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    status_filtro=status_filtro
                )
                
                # Limpar lista atual
                for item in self.consultas_tree.get_children():
                    self.consultas_tree.delete(item)
                
                # Carregar consultas na interface
                for consulta in consultas:
                    # Buscar dados do paciente
                    result = await session.execute(
                        select(Paciente).where(Paciente.id == consulta.paciente_id)
                    )
                    paciente = result.scalar_one_or_none()
                    
                    # Adicionar à lista
                    item = self.consultas_tree.insert("", "end", values=(
                        consulta.data_consulta.strftime("%d/%m/%Y"),
                        consulta.hora_inicio.strftime("%H:%M"),
                        paciente.nome if paciente else "N/A",
                        consulta.tipo_consulta.value.replace("_", " ").title(),
                        consulta.status.value.replace("_", " ").title(),
                        "Clique direito para ações"
                    ), tags=(str(consulta.id),))
                
                self._update_status(f"{len(consultas)} consultas encontradas")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar consultas: {str(e)}")
    
    # === MÉTODOS DE INTERFACE ===
    
    def _get_tipos_consulta_disponiveis(self) -> List[str]:
        """Retorna tipos de consulta disponíveis baseado no perfil do usuário"""
        tipos_base = [
            "Clínica I",
            "Clínica II", 
            "Clínica III",
            "Retorno"
        ]
        
        # Admin e professores podem agendar triagem
        if self.current_user.get('perfil') in ['admin', 'professor']:
            tipos_base.insert(0, "Triagem")
        
        return tipos_base
    
    def _on_paciente_selected(self, event=None):
        """Callback quando paciente é selecionado"""
        selecao = self.paciente_var.get()
        if not selecao:
            return
        
        # Extrair CPF da seleção
        try:
            cpf = selecao.split("CPF: ")[1]
            paciente = next((p for p in self.pacientes_cache.values() if p.cpf == cpf), None)
            
            if paciente:
                info_text = f"📋 Paciente: {paciente.nome}\n📞 Telefone: {paciente.telefone or 'N/A'}\n⚡ Status: {paciente.statusAtendimento}"
                self.paciente_info_var.set(info_text)
        except:
            self.paciente_info_var.set("Erro ao carregar informações do paciente")
    
    def _on_data_selected(self, event=None):
        """Callback quando data é selecionada"""
        data_selecionada = self.date_entry.get_date()
        
        # Validar se é dia útil
        if data_selecionada.weekday() not in [0, 1, 2, 3, 4]:  # Segunda a sexta
            messagebox.showwarning(
                "Aviso",
                "Consultas só podem ser agendadas de segunda a sexta-feira."
            )
            self.date_entry.set_date(date.today())
            return
        
        # Limpar horários
        self.horario_combo.set("")
        self.horarios_status_var.set("Clique em 'Atualizar Horários' para carregar horários disponíveis")
    
    def _agendar_consulta(self):
        """Agenda nova consulta"""
        # Validar campos obrigatórios
        if not self._validar_formulario():
            return
        
        # Executar em thread separada
        import threading
        def agendar():
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                loop.run_until_complete(self._async_agendar_consulta())
                loop.close()
            except Exception as e:
                print(f"Erro ao agendar consulta: {e}")
                self.after(0, lambda: self._update_status("Erro ao agendar consulta"))
        
        threading.Thread(target=agendar, daemon=True).start()
    
    async def _async_agendar_consulta(self):
        """Agenda consulta de forma assíncrona"""
        try:
            # Extrair dados do formulário
            cpf_paciente = self.paciente_var.get().split("CPF: ")[1]
            paciente = next((p for p in self.pacientes_cache.values() if p.cpf == cpf_paciente), None)
            
            if not paciente:
                raise ValueError("Paciente não encontrado")
            
            # Converter tipos
            data_consulta = self.date_entry.get_date()
            hora_inicio = time.fromisoformat(self.horario_var.get())
            
            # Mapear tipos de consulta corretamente
            tipo_str = self.tipo_consulta_var.get()
            tipo_map = {
                "Clínica I": "clinica_i",
                "Clínica II": "clinica_ii", 
                "Clínica III": "clinica_iii",
                "Triagem": "triagem",
                "Retorno": "retorno"
            }
            
            if tipo_str not in tipo_map:
                raise ValueError(f"Tipo de consulta inválido: {tipo_str}")
            
            tipo_consulta = TipoConsulta(tipo_map[tipo_str])
            duracao_minutos = int(self.duracao_var.get())
            
            motivo = self.motivo_text.get("1.0", "end-1c").strip()
            observacoes = self.observacoes_text.get("1.0", "end-1c").strip()
            
            # Criar consulta
            async with AsyncSessionLocal() as session:
                consulta = await AgendamentoService.criar_consulta(
                    session=session,
                    paciente_id=paciente.id,
                    aluno_id=self.current_user['id'],
                    data_consulta=data_consulta,
                    hora_inicio=hora_inicio,
                    tipo_consulta=tipo_consulta,
                    duracao_minutos=duracao_minutos,
                    motivo_consulta=motivo,
                    observacoes=observacoes,
                    criado_por=self.current_user['id']
                )
                
                await session.commit()
                
                messagebox.showinfo(
                    "Sucesso",
                    f"Consulta agendada com sucesso!\n\n"
                    f"📅 Data: {data_consulta.strftime('%d/%m/%Y')}\n"
                    f"🕒 Horário: {hora_inicio.strftime('%H:%M')}\n"
                    f"👤 Paciente: {paciente.nome}"
                )
                
                # Limpar formulário
                self._limpar_formulario()
                
                # Atualizar listas
                self._carregar_minhas_consultas()
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao agendar consulta:\n{str(e)}")
    
    def _validar_formulario(self) -> bool:
        """Valida campos obrigatórios do formulário"""
        erros = []
        
        if not self.paciente_var.get():
            erros.append("• Selecione um paciente")
        
        if not self.tipo_consulta_var.get():
            erros.append("• Selecione o tipo de consulta")
        
        if not self.horario_var.get():
            erros.append("• Selecione um horário")
        
        try:
            duracao = int(self.duracao_var.get())
            if duracao < 30 or duracao > 120:
                erros.append("• Duração deve estar entre 30 e 120 minutos")
        except:
            erros.append("• Duração inválida")
        
        if erros:
            messagebox.showerror(
                "Campos Obrigatórios",
                "Por favor, preencha os seguintes campos:\n\n" + "\n".join(erros)
            )
            return False
        
        return True
    
    def _limpar_formulario(self):
        """Limpa todos os campos do formulário"""
        self.paciente_var.set("")
        self.paciente_info_var.set("Nenhum paciente selecionado")
        self.tipo_consulta_var.set("")
        self.date_entry.set_date(date.today())
        self.horario_var.set("")
        self.duracao_var.set("60")
        self.motivo_text.delete("1.0", "end")
        self.observacoes_text.delete("1.0", "end")
        self.horarios_status_var.set("Selecione uma data para ver horários disponíveis")
    
    # === MÉTODOS DE AÇÕES DA LISTA ===
    
    def _show_context_menu(self, event):
        """Mostra menu de contexto"""
        item = self.consultas_tree.identify_row(event.y)
        if item:
            self.consultas_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _ver_detalhes_consulta(self):
        """Mostra detalhes da consulta selecionada"""
        selection = self.consultas_tree.selection()
        if not selection:
            return
        
        messagebox.showinfo("Detalhes", "🚧 Funcionalidade em desenvolvimento")
    
    def _reagendar_consulta(self):
        """Reagenda consulta selecionada"""
        messagebox.showinfo("Reagendamento", "🚧 Funcionalidade em desenvolvimento")
    
    def _cancelar_consulta(self):
        """Cancela consulta selecionada"""
        messagebox.showinfo("Cancelamento", "🚧 Funcionalidade em desenvolvimento")
    
    def _registrar_falta(self):
        """Registra falta do paciente"""
        messagebox.showinfo("Registro de Falta", "🚧 Funcionalidade em desenvolvimento")
    
    # === MÉTODOS AUXILIARES ===
    
    def _calcular_periodo_filtro(self) -> tuple[date, date]:
        """Calcula período baseado no filtro selecionado"""
        hoje = date.today()
        periodo = self.periodo_var.get()
        
        if periodo == "Hoje":
            return hoje, hoje
        elif periodo == "Próximos 7 dias":
            return hoje, hoje + timedelta(days=7)
        elif periodo == "Próximos 30 dias":
            return hoje, hoje + timedelta(days=30)
        else:
            return None, None  # Todos os agendamentos
    
    def _calcular_status_filtro(self) -> List[StatusConsulta]:
        """Calcula filtro de status"""
        status_sel = self.status_filtro_var.get()
        
        if status_sel == "Todos":
            return None
        
        # Mapear string para enum
        mapeamento = {
            "Agendada": StatusConsulta.agendada,
            "Confirmada": StatusConsulta.confirmada,
            "Em Andamento": StatusConsulta.em_andamento,
            "Concluída": StatusConsulta.concluida,
            "Cancelada": StatusConsulta.cancelada,
            "Falta": StatusConsulta.falta
        }
        
        return [mapeamento.get(status_sel)] if status_sel in mapeamento else None
    
    def _update_status(self, message: str):
        """Atualiza barra de status"""
        self.status_bar.config(text=message)
        self.update_idletasks()
    
    def _on_closing(self):
        """Callback para fechamento da janela"""
        self.destroy()


# Função principal para abrir a aplicação
def abrir_agendamento_consultas(parent=None, current_user: Dict[str, Any] = None):
    """
    Abre aplicação de agendamento de consultas
    
    Args:
        parent: Janela pai (opcional)
        current_user: Dados do usuário logado
        
    Returns:
        Instância da aplicação criada
    """
    try:
        app = AgendamentoVisualApp(parent, current_user)
        return app
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir sistema de agendamento:\n{str(e)}")
        return None


if __name__ == "__main__":
    # Teste da aplicação
    user_test = {
        'id': 1,
        'nome': 'Aluno Teste',
        'perfil': 'aluno'
    }
    
    root = tk.Tk()
    root.withdraw()  # Ocultar janela principal
    
    app = abrir_agendamento_consultas(None, user_test)
    if app:
        app.mainloop()