import socket
import threading
import json
import time
from blockchain import RedeBlockchain
from transaction import Transacao
from block import Bloco

class NoDaRede:
    def __init__(self, host, porta, nos_iniciais=None):
        self.host = host
        self.porta = porta
        self.vizinhos = set()  # Conjunto de tuplas (host, porta)
        
        if nos_iniciais:
            self.vizinhos.update(nos_iniciais)
            
        self.ativo = False
        self.minerando = False
        self.tarefa_mineracao = None
        self.socket_servidor = None
        self.trava_seguranca = threading.RLock() # Para evitar conflitos de escrita na rede
        self.blockchain = RedeBlockchain()

    def iniciar(self):
        """ Liga o servidor do nó e conecta-se aos vizinhos. """
        self.ativo = True
        self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_servidor.bind((self.host, self.porta))
        self.socket_servidor.listen(5)
        print(f"📡 Estação ligada em {self.host}:{self.porta}")

        # Thread para ficar sempre a ouvir novas ligações
        ouvinte = threading.Thread(target=self._escutar_conexoes, daemon=True)
        ouvinte.start()

        # Tentar sincronizar com quem já está na rede
        self.espalhar_mensagem('PEDIR_CORRENTE', {'porta': self.porta})

    def iniciar_mineracao(self):
        """ Ativa o processo de mineração em segundo plano. """
        if self.minerando:
            print("⛏️  A mineração já está a decorrer.")
            return

        self.minerando = True
        self.tarefa_mineracao = threading.Thread(target=self._ciclo_mineracao, daemon=True)
        self.tarefa_mineracao.start()
        print("⛏️  Mineração iniciada com sucesso!")

    def _ciclo_mineracao(self):
        """ Loop contínuo que tenta criar blocos. """
        while self.minerando and self.ativo:
            time.sleep(1) # Pequena pausa para não fritar o processador

            # Prepara as transações (incluindo a recompensa do minerador)
            transacoes_para_bloco = list(self.blockchain.transacoes_pendentes)
            meu_id = f"{self.host}:{self.porta}"
            recompensa = Transacao("sistema", meu_id, self.blockchain.recompensa_mineracao)
            transacoes_para_bloco.insert(0, recompensa)

            ultimo = self.blockchain.obter_ultimo_bloco()
            novo = Bloco(ultimo.indice + 1, ultimo.hash, transacoes_para_bloco)

            print(f"⚙️  Tentando minerar bloco {novo.indice}...")
            novo.minerar(self.blockchain.dificuldade)

            # Verifica se alguém foi mais rápido enquanto minerávamos
            with self.trava_seguranca:
                if ultimo.hash != self.blockchain.obter_ultimo_bloco().hash:
                    print("🔄 A rede atualizou primeiro. Reiniciando tentativa...")
                    continue
                resultado = self.blockchain.adicionar_bloco(novo)
                if resultado:
                    print(f"💎 Sucesso! Bloco {novo.indice} criado.")
                    self.espalhar_mensagem('NOVO_BLOCO', novo.formatar_para_dict())

    def _escutar_conexoes(self):
        """ Fica à espera que outros nós enviem dados. """
        while self.ativo:
            try:
                conexao, endereco = self.socket_servidor.accept()
                threading.Thread(target=self._gerir_cliente, args=(conexao, endereco), daemon=True).start()
            except:
                break

    def _gerir_cliente(self, conexao, endereco):
        """ Processa as mensagens recebidas de um vizinho. """
        with conexao:
            try:
                # Lê o tamanho da mensagem (primeiros 4 bytes)
                cabecalho = conexao.recv(4)
                if not cabecalho: return
                tamanho = int.from_bytes(cabecalho, 'big')
                
                # Lê o corpo da mensagem JSON
                corpo = conexao.recv(tamanho).decode('utf-8')
                mensagem = json.loads(corpo)
                self._processar_protocolo(mensagem, endereco)
            except Exception as e:
                print(f"⚠️ Erro ao receber dados de {endereco}: {e}")

    def _processar_protocolo(self, msg, endereco):
        """ Decide o que fazer com base no tipo de mensagem. """
        tipo = msg.get('type')
        dados = msg.get('payload')

        if tipo == 'PEDIR_CORRENTE':
            print(f"📤 Enviando minha corrente para {endereco[0]}:{dados.get('porta')}")
            corrente_data = [b.formatar_para_dict() for b in self.blockchain.corrente]
            self.enviar_direto(endereco[0], dados.get('porta'), 'RESPOSTA_CORRENTE', corrente_data)
            
            # Aproveita para adicionar quem pediu aos vizinhos conhecidos
            self.vizinhos.add((endereco[0], dados.get('porta')))

        elif tipo == 'RESPOSTA_CORRENTE':
            nova_corrente = [Bloco.restaurar_de_dict(b) for b in dados]
            with self.trava_seguranca:
                if self.blockchain.replace_chain(nova_corrente):
                    print("✅ Minha corrente foi atualizada pela rede.")

        elif tipo == 'NOVO_BLOCO':
            bloco_recebido = Bloco.restaurar_de_dict(dados)
            with self.trava_seguranca:
                if self.blockchain.adicionar_bloco(bloco_recebido):
                    print(f"📦 Novo bloco {bloco_recebido.indice} recebido e aceite!")
                    self.espalhar_mensagem('NOVO_BLOCO', dados)

    def enviar_direto(self, host, porta, tipo, conteudo):
        """ Envia uma mensagem para um nó específico. """
        try:
            pacote = json.dumps({"type": tipo, "payload": conteudo}).encode('utf-8')
            cabecalho = len(pacote).to_bytes(4, 'big')
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)
                s.connect((host, porta))
                s.sendall(cabecalho + pacote)
        except:
            pass # Nó offline

    def espalhar_mensagem(self, tipo, conteudo):
        """ Envia a mesma informação para todos os vizinhos conhecidos. """
        for v_host, v_porta in list(self.vizinhos):
            if (v_host, v_porta) != (self.host, self.porta):
                threading.Thread(target=self.enviar_direto, args=(v_host, v_porta, tipo, conteudo)).start()

    def parar(self):
        self.ativo = False
        self.minerando = False
        if self.socket_servidor:
            self.socket_servidor.close()
    
    def nova_transacao(self, remetente, destino, valor):
        """ 
        Cria uma nova transação a partir deste nó, adiciona-a à 
        blockchain local e espalha-a para os vizinhos. 
        """
        # Criamos o objeto de transação usando a nossa classe personalizada
        tx = self.blockchain.nova_transacao(remetente, destino, valor)
        
        if tx:
            print(f"✅ Transação {tx.id[:8]} criada com sucesso!")
            # Espalhamos a transação para que outros nós a vejam e minerem
            self.espalhar_mensagem('NOVA_TRANSACAO', tx.formatar_para_dict())
            return tx
        else:
            print("❌ Falha ao criar transação (verifique o saldo ou os dados).")
            return None