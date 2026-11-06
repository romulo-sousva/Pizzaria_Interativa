import sqlite3
import os
import tkinter as tk
from tkinter import ttk, messagebox

# ==========================================
# 1. CAMADA DE BANCO DE DADOS (SQLite)
# ==========================================
DB_NAME = "pizzaria.db"

def inicializar_banco():
    """Cria as tabelas com suporte a estoque e preços por tamanho (P, M, G)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Tabela de Produtos (Sabores únicos)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT NOT NULL, -- 'Pizza' ou 'Adicional'
            preco_p REAL,
            preco_m REAL,
            preco_g REAL NOT NULL
        )
    ''')

    # Tabela de Estoque discriminada por Tamanho
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            tamanho TEXT NOT NULL,   -- 'P', 'M', 'G' ou '-' para Adicionais
            quantidade INTEGER NOT NULL,
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    ''')

    # Tabela de Pedidos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_cliente TEXT NOT NULL,
            endereco_entrega TEXT NOT NULL,
            forma_pagamento TEXT NOT NULL,
            subtotal REAL NOT NULL,
            desconto REAL NOT NULL,
            total_final REAL NOT NULL,
            data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Carga Inicial de Catálogo e Estoque por Tamanho
    cursor.execute("SELECT COUNT(*) FROM produtos")
    if cursor.fetchone()[0] == 0:
        produtos_iniciais = [
            # Pizzas: (Nome, Categoria, Preço P, Preço M, Preço G, Qtd P, Qtd M, Qtd G)
            ("Calabresa", "Pizza", 30.00, 38.00, 48.00, 10, 15, 8),
            ("Mussarela", "Pizza", 25.00, 32.00, 42.00, 8, 12, 5),
            ("Frango c/ Catupiry", "Pizza", 35.00, 42.00, 52.00, 5, 8, 0), # G Esgotado
            ("Quatro Queijos", "Pizza", 36.00, 44.00, 54.00, 6, 6, 4),
            ("Portuguesa", "Pizza", 34.00, 40.00, 50.00, 0, 0, 0),         # Totalmente Esgotado
        ]

        for nome, cat, p_p, p_m, p_g, q_p, q_m, q_g in produtos_iniciais:
            cursor.execute("INSERT INTO produtos (nome, categoria, preco_p, preco_m, preco_g) VALUES (?, ?, ?, ?, ?)",
                           (nome, cat, p_p, p_m, p_g))
            p_id = cursor.lastrowid
            
            cursor.execute("INSERT INTO estoque (produto_id, tamanho, quantidade) VALUES (?, ?, ?)", (p_id, 'P', q_p))
            cursor.execute("INSERT INTO estoque (produto_id, tamanho, quantidade) VALUES (?, ?, ?)", (p_id, 'M', q_m))
            cursor.execute("INSERT INTO estoque (produto_id, tamanho, quantidade) VALUES (?, ?, ?)", (p_id, 'G', q_g))

        # Adicionais (Tamanho '-')
        adicionais_iniciais = [
            ("Borda Recheada Catupiry", "Adicional", 8.00, 20),
            ("Borda Recheada Cheddar", "Adicional", 8.00, 15),
            ("Extra Queijo", "Adicional", 5.00, 25),
            ("Refrigerante 2L", "Adicional", 10.00, 30)
        ]

        for nome, cat, preco, qtd in adicionais_iniciais:
            cursor.execute("INSERT INTO produtos (nome, categoria, preco_p, preco_m, preco_g) VALUES (?, ?, ?, ?, ?)",
                           (nome, cat, None, None, preco))
            p_id = cursor.lastrowid
            cursor.execute("INSERT INTO estoque (produto_id, tamanho, quantidade) VALUES (?, ?, ?)", (p_id, '-', qtd))

    conn.commit()
    conn.close()

def buscar_catalogo():
    """Retorna os produtos e um dicionário com o estoque de cada tamanho."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.id, p.nome, p.categoria, p.preco_p, p.preco_m, p.preco_g
        FROM produtos p
    ''')
    produtos = cursor.fetchall()
    
    lista_completa = []
    for prod in produtos:
        p_id = prod[0]
        cursor.execute("SELECT tamanho, quantidade FROM estoque WHERE produto_id = ?", (p_id,))
        estoques = dict(cursor.fetchall())
        lista_completa.append((prod[0], prod[1], prod[2], prod[3], prod[4], prod[5], estoques))
        
    conn.close()
    return lista_completa

def reabastecer_estoque_banco(produto_id, tamanho, quantidade_adicional):
    """Adiciona estoque ao tamanho específico do produto."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE estoque 
        SET quantidade = quantidade + ? 
        WHERE produto_id = ? AND tamanho = ?
    ''', (quantidade_adicional, produto_id, tamanho))
    conn.commit()
    conn.close()

def atualizar_estoque_banco(itens_carrinho):
    """Decrementa do banco o estoque do tamanho exato vendido."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for item in itens_carrinho:
        p_id = item['id']
        tamanho = item['tamanho']
        qtd_comprada = item['quantidade']
        cursor.execute('''
            UPDATE estoque 
            SET quantidade = quantidade - ? 
            WHERE produto_id = ? AND tamanho = ?
        ''', (qtd_comprada, p_id, tamanho))
    conn.commit()
    conn.close()

def salvar_pedido_banco(nome_cliente, endereco, forma_pgto, subtotal, desconto, total):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO pedidos (nome_cliente, endereco_entrega, forma_pagamento, subtotal, desconto, total_final)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (nome_cliente, endereco, forma_pgto, subtotal, desconto, total))
    pedido_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return pedido_id

# ==========================================
# 2. CAMADA DE NEGÓCIO E REGRAS (Backend)
# ==========================================
class BackendPizzaria:
    def __init__(self):
        self.carrinho = []

    def adicionar_ao_carrinho(self, produto, tamanho, qtd_desejada):
        p_id, nome, categoria, preco_p, preco_m, preco_g, estoques_dict = produto

        if categoria == "Pizza":
            estoque_disponivel = estoques_dict.get(tamanho, 0)
            if tamanho == 'P': preco_unitario = preco_p
            elif tamanho == 'M': preco_unitario = preco_m
            else: preco_unitario = preco_g
        else:
            tamanho = '-'
            estoque_disponivel = estoques_dict.get('-', 0)
            preco_unitario = preco_g

        if estoque_disponivel <= 0:
            return False, f"O produto '{nome}' no tamanho [{tamanho}] está ESGOTADO!"

        qtd_no_carrinho = sum(item['quantidade'] for item in self.carrinho if item['id'] == p_id and item['tamanho'] == tamanho)

        if (qtd_no_carrinho + qtd_desejada) > estoque_disponivel:
            return False, f"Estoque insuficiente para '{nome}' [{tamanho}]. Disponível: {estoque_disponivel - qtd_no_carrinho}"

        for item in self.carrinho:
            if item['id'] == p_id and item['tamanho'] == tamanho:
                item['quantidade'] += qtd_desejada
                return True, "Quantidade atualizada no carrinho!"

        self.carrinho.append({
            'id': p_id,
            'nome': nome,
            'categoria': categoria,
            'tamanho': tamanho,
            'preco_unitario': preco_unitario,
            'quantidade': qtd_desejada
        })
        return True, f"'{nome} [{tamanho}]' adicionado ao carrinho!"

    def remover_do_carrinho(self, index_item):
        if 0 <= index_item < len(self.carrinho):
            item = self.carrinho.pop(index_item)
            return True, f"'{item['nome']}' removido do carrinho."
        return False, "Item inválido para remoção."

    def calcular_totais(self):
        subtotal = sum(item['preco_unitario'] * item['quantidade'] for item in self.carrinho)
        qtd_pizzas = sum(item['quantidade'] for item in self.carrinho if item['categoria'] == 'Pizza')
        desconto = (subtotal * 0.05) if qtd_pizzas >= 2 else 0.0
        total_final = subtotal - desconto
        return subtotal, desconto, total_final, qtd_pizzas

    def limpar_carrinho(self):
        self.carrinho.clear()

# ==========================================
# 3. INTERFACE GRÁFICA (Frontend Tkinter)
# ==========================================
class AplicacaoPizzaria:
    def __init__(self, root):
        self.root = root
        self.root.title("Pizzaria Interativa - Atualização Dinâmica de Preço e Estoque")
        self.root.geometry("1060x720")
        self.root.configure(bg="#f5f5f5")

        self.backend = BackendPizzaria()
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.criar_widgets()
        self.carregar_catalogo_ui()

    def criar_widgets(self):
        frame_cabecalho = tk.Frame(self.root, bg="#c0392b", height=60)
        frame_cabecalho.pack(fill="x", side="top")

        lbl_titulo = tk.Label(frame_cabecalho, text="🍕 PIZZARIA INTERATIVA - GESTÃO DE PEDIDOS", font=("Arial", 16, "bold"), fg="white", bg="#c0392b")
        lbl_titulo.pack(pady=15)

        frame_corpo = tk.Frame(self.root, bg="#f5f5f5")
        frame_corpo.pack(fill="both", expand=True, padx=15, pady=15)

        # --- ESQUERDA: CATÁLOGO ---
        frame_esquerda = tk.LabelFrame(frame_corpo, text=" Catálogo e Estoque ", font=("Arial", 11, "bold"), bg="#ffffff", padx=10, pady=10)
        frame_esquerda.pack(side="left", fill="both", expand=True, padx=(0, 10))

        colunas = ("id", "nome", "cat", "preco_dinamico", "estoque_tam")
        self.tree_catalogo = ttk.Treeview(frame_esquerda, columns=colunas, show="headings", height=12)
        self.tree_catalogo.heading("id", text="ID")
        self.tree_catalogo.heading("nome", text="Produto")
        self.tree_catalogo.heading("cat", text="Categoria")
        self.tree_catalogo.heading("preco_dinamico", text="Preço Unit. (R$)")
        self.tree_catalogo.heading("estoque_tam", text="Estoque p/ Tam.")

        self.tree_catalogo.column("id", width=35, anchor="center")
        self.tree_catalogo.column("nome", width=160, anchor="w")
        self.tree_catalogo.column("cat", width=90, anchor="center")
        self.tree_catalogo.column("preco_dinamico", width=120, anchor="e")
        self.tree_catalogo.column("estoque_tam", width=130, anchor="center")

        self.tree_catalogo.tag_configure("esgotado", background="#ffcccc", foreground="#900c3f")
        self.tree_catalogo.pack(fill="both", expand=True, pady=5)
        self.tree_catalogo.bind("<<TreeviewSelect>>", self.on_produto_select)

        # Painel Adicionar ao Carrinho (Com Seleção de Tamanho Reativa)
        frame_add = tk.LabelFrame(frame_esquerda, text=" Adicionar ao Carrinho ", font=("Arial", 9, "bold"), bg="#ffffff", fg="#2c3e50", padx=5, pady=5)
        frame_add.pack(fill="x", pady=(5, 5))

        tk.Label(frame_add, text="Tamanho:", font=("Arial", 9, "bold"), bg="#ffffff").pack(side="left", padx=(5, 2))
        self.cmb_tamanho = ttk.Combobox(frame_add, values=["P", "M", "G"], state="readonly", width=5, font=("Arial", 9))
        self.cmb_tamanho.current(2) # Padrão G
        self.cmb_tamanho.pack(side="left", padx=(0, 10))
        # Evento de mudança no Combobox para atualizar dynamicamente a tabela
        self.cmb_tamanho.bind("<<ComboboxSelected>>", lambda e: self.carregar_catalogo_ui())

        tk.Label(frame_add, text="Qtd:", font=("Arial", 9, "bold"), bg="#ffffff").pack(side="left", padx=(5, 2))
        self.spn_qtd = tk.Spinbox(frame_add, from_=1, to=10, width=4, font=("Arial", 9))
        self.spn_qtd.pack(side="left", padx=(0, 10))

        btn_add = tk.Button(frame_add, text="🛒 Adicionar Item", font=("Arial", 9, "bold"), bg="#27ae60", fg="white", relief="flat", command=self.adicionar_item_click)
        btn_add.pack(side="left", padx=5)

        # Painel Reposição de Estoque por Tamanho
        frame_reabastecer = tk.LabelFrame(frame_esquerda, text=" Reposição de Estoque ", font=("Arial", 9, "bold"), bg="#ffffff", fg="#d35400", padx=5, pady=5)
        frame_reabastecer.pack(fill="x", pady=(5, 0))

        tk.Label(frame_reabastecer, text="Tam:", font=("Arial", 9, "bold"), bg="#ffffff").pack(side="left", padx=(5, 2))
        self.cmb_tam_reabastecer = ttk.Combobox(frame_reabastecer, values=["P", "M", "G"], state="readonly", width=4, font=("Arial", 9))
        self.cmb_tam_reabastecer.current(2)
        self.cmb_tam_reabastecer.pack(side="left", padx=(0, 5))

        tk.Label(frame_reabastecer, text="+Qtd:", font=("Arial", 9, "bold"), bg="#ffffff").pack(side="left", padx=(5, 2))
        self.spn_qtd_estoque = tk.Spinbox(frame_reabastecer, from_=1, to=100, width=4, font=("Arial", 9))
        self.spn_qtd_estoque.pack(side="left", padx=(0, 5))

        btn_reabastecer = tk.Button(frame_reabastecer, text="➕ Reabastecer", font=("Arial", 9, "bold"), bg="#e67e22", fg="white", relief="flat", command=self.reabastecer_estoque_click)
        btn_reabastecer.pack(side="left", padx=5)

        # --- DIREITA: CARRINHO E CHECKOUT ---
        frame_direita = tk.Frame(frame_corpo, bg="#f5f5f5", width=430)
        frame_direita.pack(side="right", fill="both", expand=True)

        box_carrinho = tk.LabelFrame(frame_direita, text=" Carrinho de Compras ", font=("Arial", 11, "bold"), bg="#ffffff", padx=10, pady=10)
        box_carrinho.pack(fill="both", expand=True, pady=(0, 10))

        self.lst_carrinho = tk.Listbox(box_carrinho, font=("Courier", 9), selectmode="single", height=8)
        self.lst_carrinho.pack(fill="both", expand=True)

        btn_remover = tk.Button(box_carrinho, text="❌ Remover Item Selecionado", font=("Arial", 9), bg="#e74c3c", fg="white", command=self.remover_item_click)
        btn_remover.pack(anchor="e", pady=5)

        self.lbl_fidelidade_aviso = tk.Label(box_carrinho, text="💡 Adicione 2+ pizzas para ganhar 5% de Desconto!", font=("Arial", 9, "italic"), fg="#d35400", bg="#ffffff")
        self.lbl_fidelidade_aviso.pack(anchor="w", pady=2)

        self.lbl_resumo_valores = tk.Label(box_carrinho, text="Subtotal: R$ 0.00 | Desconto: R$ 0.00 | Total: R$ 0.00", font=("Arial", 10, "bold"), fg="#2c3e50", bg="#ffffff")
        self.lbl_resumo_valores.pack(anchor="w", pady=5)

        box_checkout = tk.LabelFrame(frame_direita, text=" Dados de Entrega e Pagamento ", font=("Arial", 11, "bold"), bg="#ffffff", padx=10, pady=10)
        box_checkout.pack(fill="x")

        tk.Label(box_checkout, text="Nome do Cliente:", bg="#ffffff", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", pady=2)
        self.ent_nome = tk.Entry(box_checkout, width=32, font=("Arial", 9))
        self.ent_nome.grid(row=0, column=1, sticky="w", pady=2)

        tk.Label(box_checkout, text="Endereço Entrega:", bg="#ffffff", font=("Arial", 9, "bold")).grid(row=1, column=0, sticky="w", pady=2)
        self.ent_endereco = tk.Entry(box_checkout, width=32, font=("Arial", 9))
        self.ent_endereco.grid(row=1, column=1, sticky="w", pady=2)

        tk.Label(box_checkout, text="Forma Pagamento:", bg="#ffffff", font=("Arial", 9, "bold")).grid(row=2, column=0, sticky="w", pady=2)
        self.cmb_pagamento = ttk.Combobox(box_checkout, values=["PIX", "Cartão de Crédito/Débito", "Boleto"], state="readonly", width=29)
        self.cmb_pagamento.current(0)
        self.cmb_pagamento.grid(row=2, column=1, sticky="w", pady=2)

        btn_finalizar = tk.Button(box_checkout, text="✅ FINALIZAR E CONFIRMAR PEDIDO", font=("Arial", 11, "bold"), bg="#27ae60", fg="white", height=2, command=self.finalizar_pedido_click)
        btn_finalizar.grid(row=3, column=0, columnspan=2, sticky="we", pady=10)

    # --- FUNÇÕES DE ATUALIZAÇÃO DINÂMICA ---
    def carregar_catalogo_ui(self):
        tamanho_sel = self.cmb_tamanho.get()

        for i in self.tree_catalogo.get_children():
            self.tree_catalogo.delete(i)

        self.produtos_db = buscar_catalogo()
        for p in self.produtos_db:
            # p = (id, nome, categoria, preco_p, preco_m, preco_g, estoques_dict)
            cat = p[2]
            est_dict = p[6]

            if cat == "Pizza":
                tam_atual = tamanho_sel
                if tam_atual == 'P': preco_exibido = p[3]
                elif tam_atual == 'M': preco_exibido = p[4]
                else: preco_exibido = p[5]
                
                qtd_est = est_dict.get(tam_atual, 0)
                txt_est = f"⚠️ ESGOTADO [{tam_atual}]" if qtd_est == 0 else f"{qtd_est} un [{tam_atual}]"
            else:
                tam_atual = '-'
                preco_exibido = p[5]
                qtd_est = est_dict.get('-', 0)
                txt_est = f"⚠️ ESGOTADO" if qtd_est == 0 else f"{qtd_est} un"

            tag_aplicada = ("esgotado",) if qtd_est == 0 else ()

            self.tree_catalogo.insert("", "end", values=(p[0], p[1], cat, f"{preco_exibido:.2f}", txt_est), tags=tag_aplicada)

    def on_produto_select(self, event):
        selecionado = self.tree_catalogo.selection()
        if not selecionado: return

        item_id = self.tree_catalogo.item(selecionado[0])['values'][0]
        produto = next(p for p in self.produtos_db if p[0] == item_id)

        if produto[2] == "Adicional":
            self.cmb_tamanho.config(state="disabled")
            self.cmb_tam_reabastecer.config(state="disabled")
        else:
            self.cmb_tamanho.config(state="readonly")
            self.cmb_tam_reabastecer.config(state="readonly")

    def reabastecer_estoque_click(self):
        selecionado = self.tree_catalogo.selection()
        if not selecionado:
            messagebox.showwarning("Atenção", "Selecione um produto do catálogo para reabastecer!")
            return

        item = self.tree_catalogo.item(selecionado[0])['values']
        produto_id = item[0]
        nome_produto = item[1]
        categoria = item[2]

        tamanho = "-" if categoria == "Adicional" else self.cmb_tam_reabastecer.get()

        try:
            qtd_adicionar = int(self.spn_qtd_estoque.get())
            if qtd_adicionar <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Valor Inválido", "Digite uma quantidade válida maior que zero!")
            return

        reabastecer_estoque_banco(produto_id, tamanho, qtd_adicionar)
        messagebox.showinfo("Estoque Atualizado", f"Adicionadas {qtd_adicionar} unidades ao estoque [{tamanho}] de '{nome_produto}'!")
        self.carregar_catalogo_ui()

    def adicionar_item_click(self):
        selecionado = self.tree_catalogo.selection()
        if not selecionado:
            messagebox.showwarning("Atenção", "Selecione um produto do catálogo!")
            return

        item_id = self.tree_catalogo.item(selecionado[0])['values'][0]
        produto = next(p for p in self.produtos_db if p[0] == item_id)
        tamanho = self.cmb_tamanho.get()
        qtd = int(self.spn_qtd.get())

        sucesso, msg = self.backend.adicionar_ao_carrinho(produto, tamanho, qtd)
        if not sucesso:
            messagebox.showerror("Alerta de Estoque", msg)
        else:
            self.atualizar_carrinho_ui()
            self.carregar_catalogo_ui()

    def remover_item_click(self):
        selecionado = self.lst_carrinho.curselection()
        if not selecionado:
            messagebox.showwarning("Atenção", "Selecione um item no carrinho para remover!")
            return

        idx = selecionado[0]
        _, msg = self.backend.remover_do_carrinho(idx)
        self.atualizar_carrinho_ui()

    def atualizar_carrinho_ui(self):
        self.lst_carrinho.delete(0, tk.END)
        for item in self.backend.carrinho:
            linha = f"{item['quantidade']}x {item['nome']} [{item['tamanho']}] - R$ {item['preco_unitario']*item['quantidade']:.2f}"
            self.lst_carrinho.insert(tk.END, linha)

        subtotal, desconto, total, qtd_pizzas = self.backend.calcular_totais()

        if qtd_pizzas >= 2:
            self.lbl_fidelidade_aviso.config(text="🎉 Desconto de Fidelidade de 5% APLICADO!", fg="#27ae60")
        else:
            self.lbl_fidelidade_aviso.config(text="💡 Adicione 2+ pizzas para ganhar 5% de Desconto!", fg="#d35400")

        self.lbl_resumo_valores.config(text=f"Subtotal: R$ {subtotal:.2f} | Desc. (5%): R$ {desconto:.2f} | Total: R$ {total:.2f}")

    def finalizar_pedido_click(self):
        if not self.backend.carrinho:
            messagebox.showwarning("Carrinho Vazio", "Adicione itens ao carrinho para finalizar o pedido!")
            return

        nome = self.ent_nome.get().strip()
        endereco = self.ent_endereco.get().strip()
        forma_pgto = self.cmb_pagamento.get()

        if not nome or not endereco:
            messagebox.showerror("Campos Obrigatórios", "Por favor, preencha o Nome e o Endereço de Entrega do cliente!")
            return

        subtotal, desconto, total_final, _ = self.backend.calcular_totais()

        pedido_id = salvar_pedido_banco(nome, endereco, forma_pgto, subtotal, desconto, total_final)
        atualizar_estoque_banco(self.backend.carrinho)

        resumo_msg = (
            f"✅ PEDIDO #{pedido_id} CONFIRMADO COM SUCESSO!\n\n"
            f"Cliente: {nome}\n"
            f"Endereço: {endereco}\n"
            f"Forma de Pagamento: {forma_pgto}\n"
            f"-----------------------------------\n"
            f"Subtotal: R$ {subtotal:.2f}\n"
            f"Desconto Fidelidade (5%): R$ {desconto:.2f}\n"
            f"TOTAL A PAGAR: R$ {total_final:.2f}\n\n"
            f"O estoque discriminado por tamanho foi atualizado no banco de dados!"
        )

        messagebox.showinfo("Pedido Finalizado", resumo_msg)

        self.backend.limpar_carrinho()
        self.atualizar_carrinho_ui()
        self.ent_nome.delete(0, tk.END)
        self.ent_endereco.delete(0, tk.END)
        self.carregar_catalogo_ui()

# ==========================================
# PONTO DE ENTRADA DO SISTEMA
# ==========================================
if __name__ == "__main__":
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        
    inicializar_banco()
    root = tk.Tk()
    app = AplicacaoPizzaria(root)
    root.mainloop()
