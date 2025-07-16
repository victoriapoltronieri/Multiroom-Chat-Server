import subprocess
import time
import os
import sys
import socket
import threading

# Define o caminho para o diretório do projeto
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SERVER_PATH = os.path.join(PROJECT_ROOT, 'chat_multiroom_server.py')
CLIENT_PATH = os.path.join(PROJECT_ROOT, 'chat_client_terminal.py')

SERVER_PORT = 12345 # Porta definida no chat_multiroom_server.py
HOST = '0.0.0.0' # Host padrão para conexão local

def start_server():    
    # Comando para rodar o servidor usando poetry
    command = [sys.executable, SERVER_PATH]
    
    server_process = subprocess.Popen(
        command,
        cwd=PROJECT_ROOT
    )
    print(f"Servidor iniciado com PID: {server_process.pid}")
    print(f"Aguardando 2 segundos para o servidor iniciar completamente...")
    time.sleep(2)

    # Verifica se o processo do servidor encerrou prematuramente
    if server_process.poll() is not None:
        if server_process.returncode != 0:
            print(f"[ERRO] O servidor encerrou inesperadamente com código de saída {server_process.returncode}.")
            return None # Indica falha na inicialização
    return server_process



def main():
    server_proc = None
    try:
        while True:
            print("""
----------------------------------------
|        Menu Principal                |
----------------------------------------
| 1. Iniciar Servidor                  |
| 2. Iniciar Cliente                   |
| 3. Sair                              |
----------------------------------------""")
            try:
                choice = input("Escolha uma opção: ")
                choice_int = int(choice)
                if choice_int < 1 or choice_int > 3:
                    raise ValueError
            except ValueError:
                print("Opção inválida. Por favor, digite 1, 2 ou 3.")
                continue

            if choice_int == 1:
                if server_proc and server_proc.poll() is None:
                    print("O servidor já está rodando.")
                else:
                    try:
                        server_proc = start_server()
                        if server_proc:
                            print("Servidor iniciado. Você pode iniciar um cliente em outro terminal ou neste mesmo.")
                    except Exception as e:
                        print(f"[ERRO] Não foi possível iniciar o servidor: {e}")
            elif choice_int == 2:
                print("\n--- Iniciar Cliente ---")

                port_str = input(f"Digite o número da porta do servidor ngrok (5 dígitos, ex: {SERVER_PORT}): ")

                
                print("Iniciando o cliente...")
                client_command = [sys.executable, CLIENT_PATH, port_str]
                client_process = subprocess.Popen(
                    client_command,
                    cwd=PROJECT_ROOT
                )
                client_process.wait() # Espera o cliente encerrar
                print("Cliente encerrado.")
            elif choice == '3':
                print("Saindo...")
                break
            else:
                print("Opção inválida. Tente novamente.")

    except KeyboardInterrupt:
        print("\nEncerrando o programa...")
    finally:
        if server_proc and server_proc.poll() is None:
            print("Encerrando o servidor de chat...")
            server_proc.terminate()
            try:
                server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("Servidor não encerrou graciosamente, forçando encerramento...")
                server_proc.kill()
            print("Servidor encerrado.")

if __name__ == "__main__":
    main()