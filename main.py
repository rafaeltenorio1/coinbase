import argparse
import sys
from node import NoDaRede

# Importamos a classe da interface que criámos no outro ficheiro
from interface import BlockchainGUI 

def processar_vizinhos(texto_vizinhos):
    """ 
    Transforma a lista de texto 'host:porta' numa lista real para o Python. 
    Mantemos esta função aqui pois trata de configurações de inicialização.
    """
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

def main():
    """ Função principal que une o Nó (Backend) com a Interface (Frontend) """
    
    # 1. Lemos os argumentos passados no terminal (ex: --porta 5000)
    parser = argparse.ArgumentParser(description="Lançar um Nó da Rede Blockchain")
    parser.add_argument("--ip", default="localhost", help="IP para o servidor")
    parser.add_argument("--porta", type=int, required=True, help="Porta para escutar")
    parser.add_argument("--conectar", help="Lista de vizinhos iniciais (host:porta,host:porta)")
    args = parser.parse_args()

    # 2. Preparamos as ligações
    vizinhos_iniciais = processar_vizinhos(args.conectar)
    
    # 3. Criamos e iniciamos o nosso Nó da Rede (o "Motor" da aplicação)
    meu_no = NoDaRede(args.ip, args.porta, vizinhos_iniciais)
    meu_no.iniciar()

    # 4. Criamos e iniciamos a Interface Gráfica (a "Carroçaria" da aplicação)
    print("🎨 A iniciar a Interface Gráfica...")
    app = BlockchainGUI(meu_no)
    
    # Garantimos que, se o utilizador fechar a janela no [X], o nó também se desliga em segurança
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Mantém a janela aberta e a funcionar
    app.mainloop()

if __name__ == "__main__":
    main()