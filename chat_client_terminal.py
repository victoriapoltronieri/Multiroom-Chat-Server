import socket
import threading
import sys
import os # Adicionado para os._exit()

# Configurações do servidor
HOST = '0.tcp.sa.ngrok.io'
PORT = int(sys.argv[1]) # Porta varia a cada nova abertura do servidor.
# HOST = '127.0.0.1'
# PORT = 12345
ENCODING = 'utf-8'

# Funções auxiliares
def receive_messages(sock):
    while True:
        try:
            msg = sock.recv(1024).decode(ENCODING)
            if not msg:
                os._exit(0) # Termina o processo do cliente com sucesso
            print(msg, end='')
        except Exception as e:
            print(f"Erro ao receber mensagem: {e}")
            os._exit(1) # Termina o processo do cliente com erro

def send_messages(sock):
    while True:
        try:
            msg = input()
            sock.send(msg.encode(ENCODING))
        except:
            break

# Serviço principal
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client_socket.connect((HOST, PORT))
    print(f"Conectado ao servidor em {HOST}:{PORT}")

    threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()
    send_messages(client_socket)

except ConnectionRefusedError:
    print("[Erro] Não foi possível conectar ao servidor. Certifique-se de que ele está rodando.")
finally:
    client_socket.close()