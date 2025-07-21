import socket
import threading
import sys
import os  # Adicionado para os._exit()
import ssl

# Configurações do servidor
HOST = "0.tcp.sa.ngrok.io"
PORT = int(sys.argv[1])  # Porta varia a cada nova abertura do servidor.
# HOST = '127.0.0.1'
# PORT = 12345
ENCODING = "utf-8"


def create_client_ssl_context():
    """
    Cria e configura o contexto SSL para o cliente.
    Configurado para aceitar certificados auto-assinados.
    """
    try:
        context = ssl.create_default_context()
        # Configurações para aceitar certificados auto-assinados
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        print("[INFO] Contexto SSL do cliente configurado com sucesso.")
        return context
    except ssl.SSLError as e:
        print(f"[ERRO] Erro ao configurar contexto SSL: {e}")
        return None
    except Exception as e:
        print(f"[ERRO] Erro inesperado ao configurar SSL: {e}")
        return None


# Funções auxiliares
def receive_messages(sock):
    while True:
        try:
            msg = sock.recv(1024).decode(ENCODING)
            if not msg:
                os._exit(0)  # Termina o processo do cliente com sucesso
            print(msg, end="")
            sys.stdout.flush()  # Garante que o texto apareça imediatamente
        except Exception as e:
            print(f"Erro ao receber mensagem: {e}")
            os._exit(1)  # Termina o processo do cliente com erro


def send_messages(sock):
    while True:
        try:
            msg = input()
            sock.send(msg.encode(ENCODING))
        except:
            break


# Serviço principal
ssl_context = create_client_ssl_context()
if ssl_context is None:
    print("[ERRO] Não foi possível configurar SSL. Encerrando cliente.")
    exit(1)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    # Conecta primeiro com socket normal
    client_socket.connect((HOST, PORT))
    print(f"Conectado ao servidor em {HOST}:{PORT}")

    # Envolve o socket com SSL
    ssl_client_socket = ssl_context.wrap_socket(client_socket, server_hostname=HOST)
    print("[INFO] Handshake SSL bem-sucedido com o servidor")

    threading.Thread(
        target=receive_messages, args=(ssl_client_socket,), daemon=True
    ).start()
    send_messages(ssl_client_socket)

except ConnectionRefusedError:
    print(
        "[ERRO] Não foi possível conectar ao servidor. Certifique-se de que ele está rodando."
    )
except ssl.SSLError as e:
    print(f"[ERRO] Falha no handshake SSL: {e}")
except Exception as e:
    print(f"[ERRO] Erro inesperado na conexão: {e}")
finally:
    client_socket.close()
