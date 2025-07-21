import os
import sys

# Define o caminho para o diretório do projeto
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SERVER_PATH = os.path.join(PROJECT_ROOT, "chat_multiroom_server.py")
CLIENT_PATH = os.path.join(PROJECT_ROOT, "chat_client_terminal.py")


def main():
    """
    Este script atua como um lançador. Ele apresenta um menu e, em seguida,
    substitui seu próprio processo pelo processo do servidor ou do cliente,
    entregando o controle total do terminal para o script escolhido.
    """
    while True:
        print(
            """
----------------------------------------
|        Menu Principal                |
----------------------------------------
| 1. Iniciar Servidor                  |
| 2. Iniciar Cliente                   |
| 3. Sair                              |
----------------------------------------"""
        )
        choice = input("Escolha uma opção: ")

        if choice == "1":
            print("Iniciando o servidor... O terminal será dedicado a ele.")
            try:
                # Constrói os argumentos para a chamada de sistema.
                # O primeiro argumento é o caminho para o executável (python).
                # O segundo é uma lista que começa com o nome do programa
                # e é seguida pelos argumentos do script.
                args = [sys.executable, SERVER_PATH]
                os.execv(sys.executable, args)
            except OSError as e:
                # Este código só é alcançado se os.execv falhar.
                print(f"Erro ao iniciar o servidor: {e}")
                continue

        elif choice == "2":
            print("\n--- Iniciar Cliente ---")
            port_str = input("Digite o número da porta do servidor ngrok: ")
            if not port_str.isdigit():
                print("Porta inválida. Por favor, digite apenas números.")
                continue

            print("Iniciando o cliente... O terminal será dedicado a ele.")
            try:
                # Constrói os argumentos para o cliente.
                args = [sys.executable, CLIENT_PATH, port_str]
                os.execv(sys.executable, args)
            except OSError as e:
                # Este código só é alcançado se os.execv falhar.
                print(f"Erro ao iniciar o cliente: {e}")
                continue

        elif choice == "3":
            print("Saindo...")
            break
        else:
            print("Opção inválida. Tente novamente.")


if __name__ == "__main__":
    main()
