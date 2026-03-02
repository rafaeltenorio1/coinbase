import customtkinter as ctk
import sys
import argparse
from node import NoDaRede

# --- CONFIGURAÇÃO DO VISUAL ---
# Define o estilo da janela: "Dark" (Escuro), "Light" (Claro) ou "System"
ctk.set_appearance_mode("Dark")  
# Define a cor principal dos botões e destaques
ctk.set_default_color_theme("blue")  

class BlockchainGUI(ctk.CTk):
    """ Classe principal que constrói a Interface Gráfica """
    
    def __init__(self, meu_no):
        super().__init__()
        
        self.meu_no = meu_no # Guardamos o nó para poder chamar as funções dele
        
        # Configuração da Janela
        self.title(f"Coinbase Edu - Nó em {meu_no.host}:{meu_no.porta}")
        self.geometry("800x500") # Largura x Altura
        
        # Divide a janela em 2 colunas: Menu lateral (esquerda) e Conteúdo (direita)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # ==========================================
        # 1. MENU LATERAL (ESQUERDA)
        # ==========================================
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1) # Empurra o texto de baixo para o fim
        
        # Título do Menu
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Blockchain", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))
        
        # Botões de Navegação
        self.btn_saldo = ctk.CTkButton(self.sidebar_frame, text="💰 Ver Saldo", command=self.mostrar_frame_saldo)
        self.btn_saldo.grid(row=1, column=0, padx=20, pady=10)
        
        self.btn_blocos = ctk.CTkButton(self.sidebar_frame, text="🧱 Ver Corrente", command=self.mostrar_frame_blocos)
        self.btn_blocos.grid(row=2, column=0, padx=20, pady=10)
        
        self.btn_enviar = ctk.CTkButton(self.sidebar_frame, text="💸 Enviar Moedas", command=self.mostrar_frame_enviar)
        self.btn_enviar.grid(row=3, column=0, padx=20, pady=10)
        
        # Botão de Mineração com cor diferente (Verde)
        self.btn_minerar = ctk.CTkButton(self.sidebar_frame, text="⛏️ Ligar Mineração", fg_color="green", hover_color="darkgreen", command=self.alternar_mineracao)
        self.btn_minerar.grid(row=4, column=0, padx=20, pady=10)
        
        # Indicação de onde o nosso nó está a correr
        self.status_label = ctk.CTkLabel(self.sidebar_frame, text=f"📍 {meu_no.host}:{meu_no.porta}", text_color="gray")
        self.status_label.grid(row=6, column=0, padx=20, pady=20)
        
        # ==========================================
        # 2. ÁREA PRINCIPAL (DIREITA)
        # ==========================================
        self.main_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        # Inicia a aplicação mostrando o ecrã de saldo
        self.mostrar_frame_saldo()

    def limpar_ecra_principal(self):
        """ Função utilitária que apaga tudo do ecrã principal antes de desenhar o novo menu """
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    # --- FUNÇÕES DE CADA ECRÃ ---

    def mostrar_frame_saldo(self):
        self.limpar_ecra_principal()
        
        titulo = ctk.CTkLabel(self.main_frame, text="Consultar Saldo", font=ctk.CTkFont(size=28, weight="bold"))
        titulo.pack(pady=30)
        
        self.entrada_endereco = ctk.CTkEntry(self.main_frame, placeholder_text="Endereço (ex: localhost:5000)", width=350, height=40)
        self.entrada_endereco.pack(pady=10)
        # Facilita a apresentação preenchendo automaticamente o endereço deste nó
        self.entrada_endereco.insert(0, f"{self.meu_no.host}:{self.meu_no.porta}")
        
        btn_consultar = ctk.CTkButton(self.main_frame, text="Verificar", command=self.atualizar_saldo, height=40)
        btn_consultar.pack(pady=20)
        
        self.lbl_resultado_saldo = ctk.CTkLabel(self.main_frame, text="Saldo: -- moedas", font=ctk.CTkFont(size=24))
        self.lbl_resultado_saldo.pack(pady=30)

    def atualizar_saldo(self):
        """ Executa a lógica de ir à blockchain buscar o saldo """
        endereco = self.entrada_endereco.get()
        if endereco:
            saldo = self.meu_no.blockchain.consultar_saldo(endereco)
            self.lbl_resultado_saldo.configure(text=f"💰 {saldo} moedas")

    def mostrar_frame_blocos(self):
        self.limpar_ecra_principal()
        
        titulo = ctk.CTkLabel(self.main_frame, text="Corrente de Blocos", font=ctk.CTkFont(size=28, weight="bold"))
        titulo.pack(pady=10)
        
        # Uma caixa de texto com barra de rolagem (scroll)
        caixa_texto = ctk.CTkTextbox(self.main_frame, width=500, height=350, font=ctk.CTkFont(family="Consolas", size=14))
        caixa_texto.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Constrói o texto que vai aparecer na caixa
        texto = f"Total de Blocos: {len(self.meu_no.blockchain.corrente)}\n{'='*50}\n\n"
        for bloco in reversed(self.meu_no.blockchain.corrente): # Mostra o mais recente primeiro
            texto += f"📦 Bloco #{bloco.indice}\n"
            texto += f"Hash: {bloco.hash}\n"
            texto += f"Anterior: {bloco.hash_anterior}\n"
            texto += f"Qtd. Transações: {len(bloco.transacoes)}\n"
            texto += f"{'-'*50}\n\n"
            
        caixa_texto.insert("0.0", texto) # Insere o texto
        caixa_texto.configure(state="disabled") # Impede o utilizador de apagar/escrever na caixa

    def mostrar_frame_enviar(self):
        self.limpar_ecra_principal()
        
        titulo = ctk.CTkLabel(self.main_frame, text="Enviar Moedas", font=ctk.CTkFont(size=28, weight="bold"))
        titulo.pack(pady=30)
        
        self.entrada_destino = ctk.CTkEntry(self.main_frame, placeholder_text="Destinatário (host:porta)", width=350, height=40)
        self.entrada_destino.pack(pady=10)
        
        self.entrada_valor = ctk.CTkEntry(self.main_frame, placeholder_text="Quantia a enviar", width=350, height=40)
        self.entrada_valor.pack(pady=10)
        
        btn_enviar_tx = ctk.CTkButton(self.main_frame, text="Enviar Transação", command=self.executar_transacao, height=40)
        btn_enviar_tx.pack(pady=30)
        
        self.lbl_status_tx = ctk.CTkLabel(self.main_frame, text="", font=ctk.CTkFont(size=16))
        self.lbl_status_tx.pack()

    def executar_transacao(self):
        """ Executa a lógica de enviar dinheiro e avisa a interface """
        destino = self.entrada_destino.get()
        valor_str = self.entrada_valor.get()
        
        try:
            valor = float(valor_str)
            meu_endereco = f"{self.meu_no.host}:{self.meu_no.porta}"
            
            sucesso = self.meu_no.nova_transacao(meu_endereco, destino, valor)
            if sucesso:
                self.lbl_status_tx.configure(text="✅ Transação colocada na fila de espera!", text_color="green")
                self.meu_no.espalhar_mensagem('NEW_TRANSACTION', sucesso.formatar_para_dict())
                # Limpa as caixas de texto
                self.entrada_destino.delete(0, 'end')
                self.entrada_valor.delete(0, 'end')
            else:
                self.lbl_status_tx.configure(text="❌ Falha: Saldo insuficiente ou endereço inválido.", text_color="red")
        except ValueError:
            self.lbl_status_tx.configure(text="❌ Erro: A quantia tem de ser um número.", text_color="red")

    def alternar_mineracao(self):
        """ Liga ou desliga a mineração, e muda a cor do botão """
        if self.meu_no.minerando:
            self.meu_no.minerando = False
            self.btn_minerar.configure(text="⛏️ Ligar Mineração", fg_color="green", hover_color="darkgreen")
        else:
            self.meu_no.iniciar_mineracao()
            self.btn_minerar.configure(text="🛑 Parar Mineração", fg_color="red", hover_color="darkred")

    def on_closing(self):
        """ O que acontece quando o utilizador clica no X da janela """
        print("\nA encerrar o nó de forma segura...")
        self.meu_no.parar()
        self.destroy() # Destrói a janela
        sys.exit(0)


# ==========================================
# LÓGICA DE INICIALIZAÇÃO (Substitui o main.py)
# ==========================================

def processar_vizinhos(texto_vizinhos):
    """ Função que já tinhas no main.py, mantivemos igual """
    if not texto_vizinhos:
        return set()
    lista_final = set()
    try:
        for p in texto_vizinhos.split(','):
            host, porta = p.split(':')
            lista_final.add((host, int(porta)))
    except ValueError:
        print("❌ Formato inválido! Usa: localhost:5000,localhost:5001")
        sys.exit(1)
    return lista_final

def iniciar_app():
    parser = argparse.ArgumentParser(description="Lançar a Blockchain com Interface Gráfica")
    parser.add_argument("--ip", default="localhost", help="IP para o servidor")
    parser.add_argument("--porta", type=int, required=True, help="Porta para escutar")
    parser.add_argument("--conectar", help="Lista de vizinhos iniciais")
    
    args = parser.parse_args()

    # 1. Iniciar o Nó (backend)
    vizinhos_iniciais = processar_vizinhos(args.conectar)
    meu_no = NoDaRede(args.ip, args.porta, vizinhos_iniciais)
    meu_no.iniciar()

    # 2. Iniciar a Interface (frontend)
    app = BlockchainGUI(meu_no)
    
    # Previne que o programa fique pendurado quando fechamos a janela
    app.protocol("WM_DELETE_WINDOW", app.on_closing) 
    
    # Inicia o ciclo de vida da janela (isto fica a correr até fechares o programa)
    app.mainloop()

if __name__ == "__main__":
    iniciar_app()