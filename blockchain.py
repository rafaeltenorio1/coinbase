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
                    print(tx)
                    de = tx.get('origem') or tx.get('remetente')
                    para = tx.get('destino') or tx.get('destinatario')
                    valor = tx.get('valor') or tx.get('quantia', 0)
                else:
                    de = getattr(tx, 'remetente', None)
                    para = getattr(tx, 'destinatario', None)
                    valor = getattr(tx, 'quantia', 0)
                    print(de, para, valor)


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
    
    def replace_chain(self, nova_corrente):
        """Substitui a corrente local por uma nova se for válida e mais longa."""
        # 1. Verifica se a nova corrente é realmente maior
        if len(nova_corrente) <= len(self.corrente):
            return False
            
        # 2. Valida a integridade da nova corrente
        if not self.validar_outra_corrente(nova_corrente):
            return False
            
        # 3. Substitui a corrente
        self.corrente = nova_corrente
        
        # 4. Atualiza as transações pendentes
        # Removemos da fila o que já foi confirmado na nova corrente
        ids_confirmados = set()
        for bloco in self.corrente:
            for tx in bloco.transacoes:
                # Tenta pegar o ID seja objeto ou dicionário
                if hasattr(tx, 'id'):
                    ids_confirmados.add(tx.id)
                elif isinstance(tx, dict):
                    ids_confirmados.add(tx.get('id'))
                    
        self.transacoes_pendentes = [
            tx for tx in self.transacoes_pendentes 
            if getattr(tx, 'id', None) not in ids_confirmados
        ]
        
        return True

    def validar_outra_corrente(self, corrente_externa):
        """Método auxiliar para validar correntes recebidas de outros nós."""
        for i in range(1, len(corrente_externa)):
            bloco_atual = corrente_externa[i]
            bloco_anterior = corrente_externa[i-1]

            if bloco_atual.hash != bloco_atual.gerar_hash():
                return False

            if bloco_atual.hash_anterior != bloco_anterior.hash:
                return False

            if not bloco_atual.hash.startswith("0" * self.dificuldade):
                return False
        return True