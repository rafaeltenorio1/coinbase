import time
from block import Bloco # Importamos a classe que criámos antes
from transaction import Transacao

class RedeBlockchain:
    def __init__(self, dificuldade=3):
        self.corrente = [self.criar_bloco_genesis()]
        self.transacoes_pendentes = []
        self.dificuldade = dificuldade
        self.recompensa_mineracao = 50.0

    def criar_bloco_genesis(self):
        """ Cria o primeiríssimo bloco da rede. """
        # Um bloco com índice 0 e hash anterior fixo
        return Bloco(0, "0"*64, [], nonce=0, timestamp=0)

    def obter_ultimo_bloco(self):
        """ Atalho para pegar o bloco mais recente da lista. """
        return self.corrente[-1]

    def adicionar_bloco(self, novo_bloco):
        """ Valida e insere um novo bloco na corrente. """
        ultimo_bloco = self.obter_ultimo_bloco()

        # 1. Verificação de continuidade
        if novo_bloco.hash_anterior != ultimo_bloco.hash:
            print("❌ Erro: O hash anterior não coincide.")
            return False
        
        # 2. Verificação de integridade
        if novo_bloco.hash != novo_bloco.gerar_hash():
            print("❌ Erro: O conteúdo do bloco foi alterado.")
            return False

        # 3. Verificação de trabalho (Mineração)
        if not novo_bloco.hash.startswith("0" * self.dificuldade):
            print("❌ Erro: O bloco não foi minerado corretamente.")
            return False

        self.corrente.append(novo_bloco)
        
        # Limpar as transações pendentes que agora já estão no bloco
        ids_confirmados = {tx.id for tx in novo_bloco.transacoes if hasattr(tx, 'id')}
        self.transacoes_pendentes = [t for t in self.transacoes_pendentes if t.id not in ids_confirmados]
        
        return True

    def verificar_rede_valida(self):
        """ Percorre toda a corrente para garantir que nada foi alterado. """
        for i in range(1, len(self.corrente)):
            atual = self.corrente[i]
            anterior = self.corrente[i-1]

            # Valida o hash do próprio bloco
            if atual.hash != atual.gerar_hash():
                return False

            # Valida a ligação com o bloco anterior
            if atual.hash_anterior != anterior.hash:
                return False
        return True

    def nova_transacao(self, remetente, destino, valor):
        """ Cria e tenta adicionar uma transação à fila de espera. """
        tx = Transacao(remetente, destino, valor)
        
        # Validação básica de assinatura/estrutura
        if not tx.validar():
            return False

        # Impedir gasto duplo (se o saldo é suficiente)
        if remetente != "sistema": # 'sistema' é quem cria moedas (recompensa)
            if self.consultar_saldo(remetente) < valor:
                print(f"⚠️ Saldo insuficiente para {remetente}")
                return False
            
        self.transacoes_pendentes.append(tx)
        return tx

    def consultar_saldo(self, endereco):
        """ Calcula o saldo total percorrendo todo o histórico. """
        saldo = 0.0
        
        # Verificar blocos confirmados na corrente
        for bloco in self.corrente:
            for tx in bloco.transacoes:
                # Se for um objeto Transacao, usamos getattr para segurança
                # Se for um dicionário (JSON), usamos o .get()
                if isinstance(tx, dict):
                    de = tx.get('origem') or tx.get('remetente')
                    para = tx.get('destino') or tx.get('destinatario')
                    valor = tx.get('valor') or tx.get('quantia', 0)
                else:
                    de = getattr(tx, 'remetente', None)
                    para = getattr(tx, 'destinatario', None)
                    valor = getattr(tx, 'quantia', 0)

                if de == endereco:
                    saldo -= valor
                if para == endereco:
                    saldo += valor
        
        # Também subtraímos o que está na fila de espera (pendentes)
        for tx in self.transacoes_pendentes:
            de = getattr(tx, 'remetente', None)
            if de == endereco:
                saldo -= getattr(tx, 'quantia', 0)
                
        return saldo