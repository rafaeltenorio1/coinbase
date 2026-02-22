import argparse
import sys
import time
from node import NoDaRede

def processar_vizinhos(texto_vizinhos):
    """ Transforma a lista de texto 'host:porta' numa lista real para o Python. """
    if not texto_vizinhos:
        return set()
    
    lista_final = set()
    try:
        for p in texto_vizinhos.split(','):
            host, porta = p.split(':')
            lista_final.add((host, int(porta)))
    except ValueError:
        print("❌ Formato de vizinho inválido! Usa: localhost:5000,localhost:5001")
        sys.exit(1)
    return lista_final

def exibir_menu():
    print("\n--- 🌐 COMANDOS DA ESTAÇÃO ---")
    print("[1] Ver Saldo")
    print("[2] Ver Blocos (Corrente)")
    print("[3] Enviar Moedas")
    print("[4] Ligar/Desligar Mineração")
    print("[0] Sair")
    print("------------------------------")

def main():
    parser = argparse.ArgumentParser(description="Lançar um Nó da Rede Blockchain")
    parser.add_argument("--ip", default="localhost", help="IP para o servidor")
    parser.add_argument("--porta", type=int, required=True, help="Porta para escutar")
    parser.add_argument("--conectar", help="Lista de vizinhos iniciais (host:porta,host:porta)")
    
    args = parser.parse_args()

    # Criamos e iniciamos o nosso Nó
    vizinhos_iniciais = processar_vizinhos(args.conectar)
    meu_no = NoDaRede(args.ip, args.porta, vizinhos_iniciais)

    try:
        meu_no.iniciar()
        
        while True:
            exibir_menu()
            opcao = input("Escolha uma opção: ")

            if opcao == "1":
                endereco = input("Introduza o endereço (ex: localhost:5000): ")
                saldo = meu_no.blockchain.consultar_saldo(endereco)
                print(f"💰 Saldo de {endereco}: {saldo} moedas")

            elif opcao == "2":
                print(f"\n--- 🧱 CORRENTE ATUAL ({len(meu_no.blockchain.corrente)} blocos) ---")
                for bloco in meu_no.blockchain.corrente:
                    print(f"Bloco #{bloco.indice} | Hash: {bloco.hash[:15]}... | Anterior: {bloco.hash_anterior[:15]}...")

            elif opcao == "3":
                destino = input("Destinatário (host:porta): ")
                try:
                    valor = float(input("Quantia: "))
                    # Criamos a transação e espalhamos pela rede
                    sucesso = meu_no.nova_transacao(f"{meu_no.host}:{meu_no.porta}", destino, valor)
                    if sucesso:
                        print("✅ Transação enviada para a fila de espera!")
                        meu_no.espalhar_mensagem('NOVA_TRANSACAO', sucesso.formatar_para_dict())
                except ValueError:
                    print("❌ Valor inválido.")

            elif opcao == "4":
                if meu_no.minerando:
                    meu_no.minerando = False
                    print("🛑 Mineração interrompida.")
                else:
                    meu_no.iniciar_mineracao()

            elif opcao == "0":
                raise KeyboardInterrupt

            else:
                print("⚠️ Opção desconhecida.")

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n🛑 A desligar a estação... Até à próxima!")
        meu_no.parar()
        sys.exit(0)

if __name__ == "__main__":
    main()