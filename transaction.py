import time
import json
import hashlib

class Transacao:
    def __init__(self, remetente, destinatario, quantia, data_hora=None, id_transacao=None):
        # Detalhes da transferência
        self.remetente = remetente
        self.destinatario = destinatario
        self.quantia = quantia
        
        # Se não houver data, usamos a hora exata do computador
        self.data_hora = data_hora or time.time()
        
        # Se não houver um ID pronto (ex: carregado de um ficheiro), geramos um novo
        self.id = id_transacao or self.gerar_identificador()

    def gerar_identificador(self):
        """ Cria um ID único usando o conteúdo da transação (SHA-256). """
        # Organizamos os dados para que o texto gerado seja sempre previsível
        dados_base = {
            "origem": self.remetente,
            "destino": self.destinatario,
            "valor": self.quantia,
            "data": self.data_hora
        }
        
        # Transformamos em string JSON e aplicamos o algoritmo de Hash
        texto_da_tx = json.dumps(dados_base, sort_keys=True).encode()
        return hashlib.sha256(texto_da_tx).hexdigest()

    def formatar_para_dict(self):
        """ Exporta os dados para um formato que o Python (e o JSON) entende bem. """
        return {
            "id": self.id,
            "origem": self.remetente,
            "destino": self.destinatario,
            "valor": self.quantia,
            "timestamp": self.data_hora
        }

    @staticmethod
    def restaurar_de_dict(dados):
        """ Recria uma transação a partir de um dicionário guardado. """
        return Transacao(
            remetente=dados["origem"],
            destinatario=dados["destino"],
            quantia=dados["valor"],
            data_hora=dados["timestamp"],
            id_transacao=dados["id"]
        )

    def validar(self):
        """ Verifica se a transação faz sentido (valores positivos e endereços preenchidos). """
        if not self.remetente or not self.destinatario:
            print("⚠️ Erro: Remetente ou destinatário ausente.")
            return False
            
        if self.quantia <= 0:
            print(f"⚠️ Erro: Valor inválido ({self.quantia}). Deve ser maior que zero.")
            return False
            
        return True