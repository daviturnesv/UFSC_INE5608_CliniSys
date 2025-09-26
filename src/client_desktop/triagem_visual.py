"""
Sistema de Triagem Visual - Interface seguindo padrões hospitalares
Baseado no Protocolo Manchester de Classificação de Risco
"""
import asyncio
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import List, Optional, Dict, Any
import json

from src.backend.db.database import AsyncSessionLocal
from src.backend.models.triagem import RegistroTriagem, PrioridadeTriagem, SituacaoTriagem
from src.backend.models.paciente import Paciente
from src.backend.controllers.triagem_service import (
    listar_fila_triagem,
    obter_pacientes_aguardando_triagem,
    criar_registro_triagem,
    iniciar_triagem,
    concluir_triagem,
    cancelar_triagem,
    obter_estatisticas_triagem
)


class TriagemVisualApp(tk.Toplevel):
    """Interface principal do sistema de triagem visual"""
    
    # Configurações de cores para prioridades (Protocolo Manchester)
    CORES_PRIORIDADE = {
        PrioridadeTriagem.EMERGENCIA: {"bg": "#DC2626", "fg": "white", "desc": "EMERGÊNCIA"},
        PrioridadeTriagem.MUITO_URGENTE: {"bg": "#EA580C", "fg": "white", "desc": "MUITO URGENTE"},
        PrioridadeTriagem.URGENTE: {"bg": "#EAB308", "fg": "black", "desc": "URGENTE"},
        PrioridadeTriagem.POUCO_URGENTE: {"bg": "#16A34A", "fg": "white", "desc": "POUCO URGENTE"},
        PrioridadeTriagem.NAO_URGENTE: {"bg": "#2563EB", "fg": "white", "desc": "NÃO URGENTE"}
    }
    
    def __init__(self, parent, user_data: Dict[str, Any]):
        super().__init__(parent)
        
        self.user_data = user_data
        self.registros_triagem: List[RegistroTriagem] = []
        self.pacientes_sem_triagem: List[Paciente] = []
        self.registro_selecionado: Optional[RegistroTriagem] = None
        
        self.title("CliniSys - Sistema de Triagem Visual")
        self.geometry("1400x800")
        self.state('zoomed')  # Maximizar no Windows
        
        # Configurar layout
        self._setup_interface()
        self._carregar_dados_iniciais()
        
        # Auto-refresh a cada 30 segundos
        self._agendar_refresh()
    
    def _setup_interface(self):
        """Configura a interface principal"""
        
        # Frame principal
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título e estatísticas
        self._criar_header(main_frame)
        
        # Painel principal dividido
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Painel esquerdo - Fila de triagem
        self._criar_painel_fila(paned_window)
        
        # Painel direito - Ações e detalhes
        self._criar_painel_acoes(paned_window)
        
    def _criar_header(self, parent):
        """Cria o cabeçalho com título e estatísticas"""
        
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Título
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=tk.LEFT)
        
        title_label = ttk.Label(title_frame, text="🏥 SISTEMA DE TRIAGEM", 
                               font=("Arial", 16, "bold"))
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = ttk.Label(title_frame, 
                                  text=f"Usuário: {self.user_data.get('nome', 'N/A')} ({self.user_data.get('perfil', 'N/A')})",
                                  font=("Arial", 10))
        subtitle_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # Botões de ação
        actions_frame = ttk.Frame(header_frame)
        actions_frame.pack(side=tk.RIGHT)
        
        ttk.Button(actions_frame, text="🔄 Atualizar", 
                  command=self._atualizar_dados).pack(side=tk.LEFT, padx=5)
        
        if self.user_data.get('perfil') == 'admin':
            ttk.Button(actions_frame, text="📊 Estatísticas", 
                      command=self._mostrar_estatisticas).pack(side=tk.LEFT, padx=5)
        
        # Painel de estatísticas rápidas
        stats_frame = ttk.LabelFrame(parent, text="Estatísticas em Tempo Real")
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        stats_inner = ttk.Frame(stats_frame)
        stats_inner.pack(fill=tk.X, padx=10, pady=5)
        
        # Labels de estatísticas
        self.stats_labels = {}
        stats_configs = [
            ("aguardando", "Aguardando Triagem", "#6B7280"),
            ("em_andamento", "Em Andamento", "#EAB308"),
            ("emergencia", "Casos de Emergência", "#DC2626"),
            ("total", "Total na Fila", "#374151")
        ]
        
        for i, (key, text, color) in enumerate(stats_configs):
            frame = ttk.Frame(stats_inner)
            frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10)
            
            value_label = ttk.Label(frame, text="0", font=("Arial", 24, "bold"),
                                   foreground=color)
            value_label.pack()
            
            desc_label = ttk.Label(frame, text=text, font=("Arial", 9))
            desc_label.pack()
            
            self.stats_labels[key] = value_label
    
    def _criar_painel_fila(self, parent):
        """Cria o painel da fila de triagem"""
        
        fila_frame = ttk.LabelFrame(parent, text="📋 Fila de Triagem")
        parent.add(fila_frame, weight=2)
        
        # Subtabs para diferentes visões
        notebook = ttk.Notebook(fila_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Aba 1: Pacientes aguardando triagem inicial
        self._criar_aba_aguardando_triagem(notebook)
        
        # Aba 2: Triagens em andamento
        self._criar_aba_triagem_andamento(notebook)
        
        # Aba 3: Fila priorizada (triados aguardando consulta)
        self._criar_aba_fila_priorizada(notebook)
    
    def _criar_aba_aguardando_triagem(self, notebook):
        """Aba para pacientes que ainda não passaram por triagem"""
        
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="⏳ Aguardando Triagem")
        
        # Lista de pacientes
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview
        columns = ("nome", "cpf", "idade", "chegada")
        self.tree_aguardando = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # Cabeçalhos
        self.tree_aguardando.heading("nome", text="Nome do Paciente")
        self.tree_aguardando.heading("cpf", text="CPF")
        self.tree_aguardando.heading("idade", text="Idade")
        self.tree_aguardando.heading("chegada", text="Chegada")
        
        # Larguras
        self.tree_aguardando.column("nome", width=250)
        self.tree_aguardando.column("cpf", width=120)
        self.tree_aguardando.column("idade", width=80)
        self.tree_aguardando.column("chegada", width=150)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_aguardando.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree_aguardando.xview)
        self.tree_aguardando.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Grid layout
        self.tree_aguardando.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Botões de ação
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="🔍 Iniciar Triagem", 
                  command=self._iniciar_triagem_selecionada).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="➕ Adicionar à Fila", 
                  command=self._adicionar_paciente_fila).pack(side=tk.LEFT, padx=5)
        
        # Binding para seleção
        self.tree_aguardando.bind("<<TreeviewSelect>>", self._on_select_aguardando)
    
    def _criar_aba_triagem_andamento(self, notebook):
        """Aba para triagens em andamento"""
        
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="🔄 Em Andamento")
        
        # Lista de triagens em andamento
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("paciente", "aluno", "inicio", "tempo", "situacao")
        self.tree_andamento = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
        
        # Cabeçalhos
        self.tree_andamento.heading("paciente", text="Paciente")
        self.tree_andamento.heading("aluno", text="Aluno Responsável")
        self.tree_andamento.heading("inicio", text="Início")
        self.tree_andamento.heading("tempo", text="Tempo Decorrido")
        self.tree_andamento.heading("situacao", text="Situação")
        
        # Larguras
        self.tree_andamento.column("paciente", width=200)
        self.tree_andamento.column("aluno", width=180)
        self.tree_andamento.column("inicio", width=120)
        self.tree_andamento.column("tempo", width=100)
        self.tree_andamento.column("situacao", width=150)
        
        # Scrollbar
        scroll_and = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_andamento.yview)
        self.tree_andamento.configure(yscrollcommand=scroll_and.set)
        
        self.tree_andamento.grid(row=0, column=0, sticky="nsew")
        scroll_and.grid(row=0, column=1, sticky="ns")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Botões
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="✅ Concluir Triagem", 
                  command=self._abrir_formulario_conclusao).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="❌ Cancelar", 
                  command=self._cancelar_triagem).pack(side=tk.LEFT, padx=5)
    
    def _criar_aba_fila_priorizada(self, notebook):
        """Aba para fila priorizada (já triados, aguardando consulta)"""
        
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="🎯 Fila Priorizada")
        
        # Lista priorizada com cores
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("prioridade", "paciente", "queixa", "triado_em", "tempo_espera")
        self.tree_priorizada = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # Cabeçalhos
        self.tree_priorizada.heading("prioridade", text="Prioridade")
        self.tree_priorizada.heading("paciente", text="Paciente")
        self.tree_priorizada.heading("queixa", text="Queixa Principal")
        self.tree_priorizada.heading("triado_em", text="Triado em")
        self.tree_priorizada.heading("tempo_espera", text="Tempo de Espera")
        
        # Larguras
        self.tree_priorizada.column("prioridade", width=120)
        self.tree_priorizada.column("paciente", width=200)
        self.tree_priorizada.column("queixa", width=250)
        self.tree_priorizada.column("triado_em", width=120)
        self.tree_priorizada.column("tempo_espera", width=120)
        
        # Scrollbar
        scroll_prior = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_priorizada.yview)
        self.tree_priorizada.configure(yscrollcommand=scroll_prior.set)
        
        self.tree_priorizada.grid(row=0, column=0, sticky="nsew")
        scroll_prior.grid(row=0, column=1, sticky="ns")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Configurar cores por prioridade (tags)
        self._configurar_cores_tree()
    
    def _configurar_cores_tree(self):
        """Configura as cores do TreeView baseado nas prioridades"""
        for prioridade, config in self.CORES_PRIORIDADE.items():
            tag_name = f"prioridade_{prioridade.value}"
            self.tree_priorizada.tag_configure(tag_name, 
                                             background=config["bg"], 
                                             foreground=config["fg"])
    
    def _criar_painel_acoes(self, parent):
        """Cria o painel de ações e detalhes"""
        
        acoes_frame = ttk.LabelFrame(parent, text="⚡ Ações e Detalhes")
        parent.add(acoes_frame, weight=1)
        
        # Seção de informações do paciente selecionado
        info_frame = ttk.LabelFrame(acoes_frame, text="Informações do Paciente")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.info_labels = {}
        info_items = [
            ("nome", "Nome:"),
            ("cpf", "CPF:"),
            ("idade", "Idade:"),
            ("telefone", "Telefone:"),
            ("status", "Status:")
        ]
        
        for i, (key, label) in enumerate(info_items):
            row_frame = ttk.Frame(info_frame)
            row_frame.pack(fill=tk.X, padx=5, pady=2)
            
            ttk.Label(row_frame, text=label, font=("Arial", 9, "bold")).pack(side=tk.LEFT)
            label_info = ttk.Label(row_frame, text="", font=("Arial", 9))
            label_info.pack(side=tk.LEFT, padx=(10, 0))
            self.info_labels[key] = label_info
        
        # Seção de protocolo Manchester
        protocol_frame = ttk.LabelFrame(acoes_frame, text="🏥 Protocolo Manchester")
        protocol_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Botões de prioridade
        priority_frame = ttk.Frame(protocol_frame)
        priority_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(priority_frame, text="Selecione a Classificação de Risco:", 
                 font=("Arial", 10, "bold")).pack(pady=(0, 10))
        
        self.selected_priority = tk.StringVar()
        
        for prioridade, config in self.CORES_PRIORIDADE.items():
            btn = tk.Radiobutton(priority_frame, 
                                text=f"  {config['desc']}  ",
                                variable=self.selected_priority,
                                value=prioridade.value,
                                bg=config["bg"],
                                fg=config["fg"],
                                selectcolor=config["bg"],
                                font=("Arial", 10, "bold"),
                                relief=tk.RAISED,
                                bd=2)
            btn.pack(fill=tk.X, pady=2)
        
        # Campos de triagem
        campos_frame = ttk.LabelFrame(acoes_frame, text="Dados da Triagem")
        campos_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Queixa principal
        ttk.Label(campos_frame, text="Queixa Principal:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.queixa_text = tk.Text(campos_frame, height=3, wrap=tk.WORD)
        self.queixa_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Necessidades identificadas
        ttk.Label(campos_frame, text="Necessidades Identificadas:").pack(anchor=tk.W, padx=5)
        self.necessidades_text = tk.Text(campos_frame, height=3, wrap=tk.WORD)
        self.necessidades_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Observações
        ttk.Label(campos_frame, text="Observações:").pack(anchor=tk.W, padx=5)
        self.observacoes_text = tk.Text(campos_frame, height=3, wrap=tk.WORD)
        self.observacoes_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Botões de ação finais
        final_actions = ttk.Frame(acoes_frame)
        final_actions.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(final_actions, text="✅ Concluir Triagem", 
                  command=self._concluir_triagem_atual).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(final_actions, text="💾 Salvar Rascunho", 
                  command=self._salvar_rascunho).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(final_actions, text="🚫 Cancelar", 
                  command=self._cancelar_triagem_atual).pack(side=tk.LEFT, padx=5)
    
    def _carregar_dados_iniciais(self):
        """Carrega os dados iniciais"""
        # Executar em thread separada para evitar travamento
        import threading
        def carregar():
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                loop.run_until_complete(self._carregar_dados_async())
                loop.close()
            except Exception as e:
                print(f"Erro ao carregar dados: {e}")
                self.after(0, lambda: print(f"Erro: {str(e)}"))
        
        # Agendar execução após UI estar pronta
        self.after(100, lambda: threading.Thread(target=carregar, daemon=True).start())
    
    async def _carregar_dados_async(self):
        """Carrega dados do banco de forma assíncrona"""
        try:
            async with AsyncSessionLocal() as session:
                # Carregar pacientes aguardando triagem
                self.pacientes_sem_triagem = await obter_pacientes_aguardando_triagem(session)
                
                # Carregar registros de triagem
                self.registros_triagem = await listar_fila_triagem(session, incluir_concluidas=False)
                
                # Carregar estatísticas
                stats = await obter_estatisticas_triagem(session)
                
            # Atualizar interface na thread principal
            self.after(0, lambda: self._atualizar_interface(stats))
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", f"Erro ao carregar dados: {e}"))
    
    def _atualizar_interface(self, stats: dict):
        """Atualiza a interface com os dados carregados"""
        
        # Atualizar estatísticas
        self.stats_labels["aguardando"].config(text=str(stats.get("aguardando_triagem", 0)))
        self.stats_labels["em_andamento"].config(text=str(stats.get("triagem_em_andamento", 0)))
        self.stats_labels["emergencia"].config(text=str(stats.get("casos_emergencia", 0)))
        self.stats_labels["total"].config(text=str(stats.get("total_pendente", 0)))
        
        # Atualizar listas
        self._atualizar_tree_aguardando()
        self._atualizar_tree_andamento()
        self._atualizar_tree_priorizada()
    
    def _atualizar_tree_aguardando(self):
        """Atualiza a árvore de pacientes aguardando triagem"""
        
        # Limpar
        for item in self.tree_aguardando.get_children():
            self.tree_aguardando.delete(item)
        
        # Adicionar pacientes
        for paciente in self.pacientes_sem_triagem:
            idade = self._calcular_idade(paciente.dataNascimento)
            chegada = paciente.created_at.strftime("%d/%m %H:%M") if paciente.created_at else "N/A"
            
            self.tree_aguardando.insert("", tk.END, values=(
                paciente.nome,
                paciente.cpf,
                f"{idade} anos",
                chegada
            ), tags=(str(paciente.id),))
    
    def _atualizar_tree_andamento(self):
        """Atualiza a árvore de triagens em andamento"""
        
        # Limpar
        for item in self.tree_andamento.get_children():
            self.tree_andamento.delete(item)
        
        # Filtrar registros em andamento
        em_andamento = [r for r in self.registros_triagem if r.situacao == SituacaoTriagem.EM_ANDAMENTO]
        
        for registro in em_andamento:
            paciente_nome = registro.paciente.nome if registro.paciente else "N/A"
            aluno_nome = "Carregando..." if registro.aluno_id else "N/A"
            inicio = registro.triagem_iniciada_em.strftime("%H:%M") if registro.triagem_iniciada_em else "N/A"
            
            # Calcular tempo decorrido
            if registro.triagem_iniciada_em:
                tempo_decorrido = datetime.now() - registro.triagem_iniciada_em.replace(tzinfo=None)
                tempo_str = f"{int(tempo_decorrido.total_seconds() // 60)} min"
            else:
                tempo_str = "N/A"
            
            self.tree_andamento.insert("", tk.END, values=(
                paciente_nome,
                aluno_nome,
                inicio,
                tempo_str,
                "Em Andamento"
            ), tags=(str(registro.id),))
    
    def _atualizar_tree_priorizada(self):
        """Atualiza a árvore de fila priorizada"""
        
        # Limpar
        for item in self.tree_priorizada.get_children():
            self.tree_priorizada.delete(item)
        
        # Filtrar registros concluídos (triados)
        triados = [r for r in self.registros_triagem if r.situacao == SituacaoTriagem.CONCLUIDA]
        
        # Ordenar por prioridade
        triados.sort(key=lambda r: (r.prioridade.value if r.prioridade else "zzz", r.triagem_concluida_em))
        
        for registro in triados:
            if not registro.paciente:
                continue
                
            paciente_nome = registro.paciente.nome
            queixa = registro.queixa_principal[:50] + "..." if registro.queixa_principal and len(registro.queixa_principal) > 50 else (registro.queixa_principal or "Não informado")
            triado_em = registro.triagem_concluida_em.strftime("%H:%M") if registro.triagem_concluida_em else "N/A"
            
            # Calcular tempo de espera
            if registro.triagem_concluida_em:
                tempo_espera = datetime.now() - registro.triagem_concluida_em.replace(tzinfo=None)
                espera_str = f"{int(tempo_espera.total_seconds() // 60)} min"
            else:
                espera_str = "N/A"
            
            # Determinar prioridade para cor
            prioridade_desc = registro.descricao_prioridade if registro.prioridade else "Sem Prioridade"
            tag = f"prioridade_{registro.prioridade.value}" if registro.prioridade else ""
            
            item = self.tree_priorizada.insert("", tk.END, values=(
                prioridade_desc,
                paciente_nome,
                queixa,
                triado_em,
                espera_str
            ), tags=(tag,))
    
    def _calcular_idade(self, data_nascimento):
        """Calcula idade baseada na data de nascimento"""
        try:
            hoje = datetime.now().date()
            idade = hoje.year - data_nascimento.year
            if hoje.month < data_nascimento.month or (hoje.month == data_nascimento.month and hoje.day < data_nascimento.day):
                idade -= 1
            return idade
        except:
            return 0
    
    def _atualizar_dados(self):
        """Atualiza todos os dados"""
        self._carregar_dados_iniciais()
    
    def _agendar_refresh(self):
        """Agenda refresh automático"""
        self.after(30000, self._agendar_refresh)  # 30 segundos
        self._atualizar_dados()
    
    def _on_select_aguardando(self, event):
        """Callback para seleção na lista de aguardando triagem"""
        selection = self.tree_aguardando.selection()
        if selection:
            item = self.tree_aguardando.item(selection[0])
            tags = item.get("tags", [])
            if tags:
                paciente_id = int(tags[0])
                paciente = next((p for p in self.pacientes_sem_triagem if p.id == paciente_id), None)
                if paciente:
                    self._mostrar_info_paciente(paciente)
    
    def _mostrar_info_paciente(self, paciente: Paciente):
        """Mostra informações do paciente selecionado"""
        self.info_labels["nome"].config(text=paciente.nome)
        self.info_labels["cpf"].config(text=paciente.cpf)
        self.info_labels["idade"].config(text=f"{self._calcular_idade(paciente.dataNascimento)} anos")
        self.info_labels["telefone"].config(text=paciente.telefone or "Não informado")
        self.info_labels["status"].config(text=paciente.statusAtendimento)
    
    def _iniciar_triagem_selecionada(self):
        """Inicia triagem para o paciente selecionado"""
        selection = self.tree_aguardando.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um paciente para iniciar a triagem.")
            return
        
        item = self.tree_aguardando.item(selection[0])
        tags = item.get("tags", [])
        if not tags:
            return
        
        paciente_id = int(tags[0])
        
        # Executar em thread separada
        import threading
        def iniciar_triagem():
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                loop.run_until_complete(self._iniciar_triagem_async(paciente_id))
                loop.close()
            except Exception as e:
                print(f"Erro ao iniciar triagem: {e}")
                self.after(0, lambda: messagebox.showerror("Erro", f"Erro ao iniciar triagem: {str(e)}"))
        
        threading.Thread(target=iniciar_triagem, daemon=True).start()
    
    async def _iniciar_triagem_async(self, paciente_id: int):
        """Inicia triagem de forma assíncrona"""
        try:
            async with AsyncSessionLocal() as session:
                # Criar ou obter registro de triagem
                registro = await criar_registro_triagem(session, paciente_id)
                
                # Iniciar triagem
                if registro.situacao == SituacaoTriagem.AGUARDANDO:
                    aluno_id = self.user_data.get("id")
                    if not aluno_id:
                        raise ValueError("ID do usuário não encontrado")
                    
                    await iniciar_triagem(session, registro.id, aluno_id)
            
            # Atualizar interface
            self.after(0, lambda: self._atualizar_dados())
            self.after(0, lambda: messagebox.showinfo("Sucesso", "Triagem iniciada com sucesso!"))
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", f"Erro ao iniciar triagem: {e}"))
    
    def _concluir_triagem_atual(self):
        """Conclui a triagem atual"""
        if not self.selected_priority.get():
            messagebox.showwarning("Aviso", "Selecione uma prioridade para concluir a triagem.")
            return
        
        # Aqui você implementaria a lógica para concluir a triagem
        # Por simplicidade, vou mostrar uma mensagem
        messagebox.showinfo("Em Desenvolvimento", "Funcionalidade de conclusão será implementada.")
    
    def _salvar_rascunho(self):
        """Salva rascunho da triagem"""
        messagebox.showinfo("Info", "Rascunho salvo (funcionalidade em desenvolvimento).")
    
    def _cancelar_triagem_atual(self):
        """Cancela a triagem atual"""
        if messagebox.askyesno("Confirmar", "Deseja cancelar a triagem atual?"):
            # Limpar campos
            self.selected_priority.set("")
            self.queixa_text.delete("1.0", tk.END)
            self.necessidades_text.delete("1.0", tk.END)
            self.observacoes_text.delete("1.0", tk.END)
            
            # Limpar informações do paciente
            for label in self.info_labels.values():
                label.config(text="")
    
    def _adicionar_paciente_fila(self):
        """Adiciona um novo paciente à fila de triagem"""
        messagebox.showinfo("Em Desenvolvimento", "Funcionalidade em desenvolvimento.")
    
    def _abrir_formulario_conclusao(self):
        """Abre formulário de conclusão de triagem"""
        messagebox.showinfo("Em Desenvolvimento", "Formulário de conclusão em desenvolvimento.")
    
    def _cancelar_triagem(self):
        """Cancela uma triagem em andamento"""
        messagebox.showinfo("Em Desenvolvimento", "Funcionalidade em desenvolvimento.")
    
    def _mostrar_estatisticas(self):
        """Mostra estatísticas detalhadas"""
        messagebox.showinfo("Em Desenvolvimento", "Estatísticas detalhadas em desenvolvimento.")


def abrir_triagem_visual(parent, user_data: Dict[str, Any]):
    """Função para abrir o sistema de triagem visual"""
    try:
        app = TriagemVisualApp(parent, user_data)
        return app
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir sistema de triagem: {e}")
        return None