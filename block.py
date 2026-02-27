import hashlib
import json
import time
from transaction import Transacao

class Bloco:
    def __init__(self, indice, hash_anterior, transacoes, nonce=0, timestamp=None):
        self.indice = indice
        self.hash_anterior = hash_anterior
        self.transacoes = transacoes
        self.nonce = nonce
        self.timestamp = timestamp if timestamp is not None else time.time()
        
        # Primeiro calculamos o hash, depois atribuímos ao self.hash
        # Isso evita que o formatar_para_dict tente ler algo que não existe
        self.hash = self.gerar_hash()

    def gerar_hash(self):
        """ Cria a 'impressão digital' única deste bloco. """
        # Criamos um dicionário local APENAS com o que compõe o conteúdo
        # IMPORTANTE: Não incluímos o próprio 'hash' aqui!

        lista_txs_preparada = []
        for tx in self.transacoes:
            # Se for objeto Transacao, chama o método de formatar
            if hasattr(tx, 'formatar_para_dict'):
                lista_txs_preparada.append(tx.formatar_para_dict())
            elif hasattr(tx, 'to_dict'):
                lista_txs_preparada.append(tx.to_dict())
            else:
                # Se já for dict ou string, usa como está
                lista_txs_preparada.append(tx)

        conteudo_para_hash = {
            "index": self.indice,
            "previous_hash": self.hash_anterior,
            "transactions": lista_txs_preparada,
            "nonce": self.nonce,
            "timestamp": self.timestamp
        }
        
        bloco_serializado = json.dumps(conteudo_para_hash, sort_keys=True).encode()
        return hashlib.sha256(bloco_serializado).hexdigest()

    def minerar(self, dificuldade):
        """ Tenta encontrar um hash que comece com o número de zeros definido. """
        alvo = "0" * dificuldade
        
        while not self.hash.startswith(alvo):
            self.nonce += 1
            self.hash = self.gerar_hash()
            
        print(f"✅ Bloco {self.indice} minerado! Hash: {self.hash}")

    def formatar_para_dict(self):
        """ Converte o objeto completo para dicionário usando o padrão da rede (Inglês). """
        return {
            "index": self.indice,
            "previous_hash": self.hash_anterior,
            "transactions": [tx.formatar_para_dict() if hasattr(tx, 'formatar_para_dict') else tx for tx in self.transacoes],
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "hash": self.hash
        }

    @staticmethod
    def restaurar_de_dict(dados):
        """ Recria um objeto Bloco a partir de um dicionário de dados. """
        lista_txs = []
        # Ajustado para usar as chaves em português que definimos no dicionário
        transacoes_fonte = dados.get("transacoes") or dados.get("transactions") or []
        
        for tx in transacoes_fonte:
            if isinstance(tx, dict):
                lista_txs.append(Transacao.restaurar_de_dict(tx))
            else:
                lista_txs.append(tx)

        bloco = Bloco(
            indice=dados.get("indice") or dados.get("index"),
            hash_anterior=dados.get("hash_anterior") or dados.get("previous_hash"),
            transacoes=lista_txs,
            nonce=dados["nonce"],
            timestamp=dados["timestamp"]
        )
        bloco.hash = dados["hash"]
        return bloco