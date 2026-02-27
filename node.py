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
        self.espalhar_mensagem('REQUEST_CHAIN', {})

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
            time.sleep(1)

            transacoes_para_bloco = list(self.blockchain.transacoes_pendentes)
            meu_id = f"{self.host}:{self.porta}"
            recompensa = Transacao("sistema", meu_id, self.blockchain.recompensa_mineracao)
            transacoes_para_bloco.insert(0, recompensa)

            ultimo = self.blockchain.obter_ultimo_bloco()
            novo = Bloco(ultimo.indice + 1, ultimo.hash, transacoes_para_bloco)

            print(f"⚙️  Tentando minerar bloco {novo.indice}...")
            novo.minerar(self.blockchain.dificuldade)

            with self.trava_seguranca:
                if ultimo.hash != self.blockchain.obter_ultimo_bloco().hash:
                    print("🔄 A rede atualizou primeiro. Reiniciando tentativa...")
                    continue
                resultado = self.blockchain.adicionar_bloco(novo)
                if resultado:
                    print(f"💎 Sucesso! Bloco {novo.indice} criado.")
                    # O outro nó espera que o bloco venha dentro da chave "block"
                    self.espalhar_mensagem('NEW_BLOCK', {"block": novo.formatar_para_dict()})

    def _escutar_conexoes(self):
        """ Fica à espera que outros nós enviem dados. """
        while self.ativo:
            try:
                conexao, endereco = self.socket_servidor.accept()
                threading.Thread(target=self._gerir_cliente, args=(conexao, endereco), daemon=True).start()
            except:
                break

    def _gerir_cliente(self, conexao, endereco):
        """ Processa as mensagens recebidas e devolve a resposta no mesmo socket, se houver. """
        with conexao:
            try:
                cabecalho = conexao.recv(4)
                if not cabecalho: return
                tamanho = int.from_bytes(cabecalho, 'big')
                
                corpo = conexao.recv(tamanho).decode('utf-8')
                mensagem = json.loads(corpo)
                
                # Pega a resposta gerada pelo protocolo
                resposta = self._processar_protocolo(mensagem, endereco)
                
                # Se houver resposta (ex: RESPONSE_CHAIN), envia de volta na mesma hora
                if resposta:
                    pacote_resp = json.dumps(resposta).encode('utf-8')
                    cab_resp = len(pacote_resp).to_bytes(4, 'big')
                    conexao.sendall(cab_resp + pacote_resp)
            except Exception as e:
                print(f"⚠️ Erro ao receber/responder dados para {endereco}: {e}")

    def enviar_direto(self, host, porta, tipo, conteudo):
        """ Envia uma mensagem e aguarda para ver se há resposta na mesma conexão. """
        try:
            meu_endereco = f"{self.host}:{self.porta}"
            dicionario_msg = {
                "type": tipo, 
                "payload": conteudo, 
                "sender": meu_endereco
            }
            pacote = json.dumps(dicionario_msg).encode('utf-8')
            cabecalho = len(pacote).to_bytes(4, 'big')
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5) # Espera no máximo 5 segundos por uma resposta
                s.connect((host, int(porta)))
                s.sendall(cabecalho + pacote)
                
                # Fica escutando a resposta no mesmo tubo
                try:
                    cabecalho_resp = s.recv(4)
                    if cabecalho_resp:
                        tamanho_resp = int.from_bytes(cabecalho_resp, 'big')
                        
                        corpo_resp = b""
                        while len(corpo_resp) < tamanho_resp:
                            chunk = s.recv(min(4096, tamanho_resp - len(corpo_resp)))
                            if not chunk: break
                            corpo_resp += chunk
                            
                        msg_resp = json.loads(corpo_resp.decode('utf-8'))
                        self._processar_protocolo(msg_resp, (host, porta))
                except socket.timeout:
                    pass # Timeout normal para mensagens que não têm resposta
                    
        except Exception as e:
            pass # Nó offline

    def _processar_protocolo(self, msg, endereco):
        """ Decide o que fazer e retorna a resposta (se necessário). """
        tipo = msg.get('type')
        dados = msg.get('payload', {})
        remetente = msg.get('sender')
        
        print(f"📩 Recebido: {tipo} de {remetente}")

        # Registra o vizinho dinamicamente usando a string do sender
        if remetente:
            try:
                host_rem, porta_rem = remetente.split(':')
                self.vizinhos.add((host_rem, int(porta_rem)))
            except:
                pass

        if tipo == 'REQUEST_CHAIN':
            print("📤 Respondendo com minha corrente...")
            corrente_data = [b.formatar_para_dict() for b in self.blockchain.corrente]
            meu_endereco = f"{self.host}:{self.porta}"
            
            # Retorna o dicionário com a estrutura exata que o outro grupo espera
            return {
                "type": "RESPONSE_CHAIN",
                "payload": {
                    "blockchain": {
                        "chain": corrente_data
                    }
                },
                "sender": meu_endereco
            }

        elif tipo == 'RESPONSE_CHAIN':
            # Lê a lista de blocos de dentro da subchave "chain"
            lista_blocos = dados.get("blockchain", {}).get("chain", [])
            nova_corrente = [Bloco.restaurar_de_dict(b) for b in lista_blocos]
            with self.trava_seguranca:
                if self.blockchain.replace_chain(nova_corrente):
                    print("✅ Minha corrente foi atualizada pela rede.")

        elif tipo == 'NEW_BLOCK':
            # Extrai o bloco da subchave "block"
            bloco_data = dados.get("block", dados)
            bloco_recebido = Bloco.restaurar_de_dict(bloco_data)
            with self.trava_seguranca:
                if self.blockchain.adicionar_bloco(bloco_recebido):
                    print(f"📦 Novo bloco {bloco_recebido.indice} recebido e aceite!")
                    self.espalhar_mensagem('NEW_BLOCK', {"block": bloco_data})
                    
        return None # Retorna None se não precisar responder na mesma conexão
    

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
            self.espalhar_mensagem('NEW_TRANSACTION', {"transaction": tx.formatar_para_dict()})
            return tx
        else:
            print("❌ Falha ao criar transação (verifique o saldo ou os dados).")
            return None