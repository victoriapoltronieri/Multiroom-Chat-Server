"""
Cliente de Chat Multi-sala com criptografia SSL/TLS.

Este módulo implementa um cliente de chat seguro que se conecta ao servidor de chat multi-sala.
Funcionalidades:
- Comunicação criptografada com SSL/TLS
- Recebimento e envio de mensagens em tempo real
- Interface de usuário baseada em terminal
- Gerenciamento automático de conexão e handshake SSL
"""

import socket
import threading
import sys
import os
import ssl

# Configuração de conexão com o servidor
HOST = "0.tcp.sa.ngrok.io"  # Hostname do túnel ngrok para acesso remoto
PORT = int(sys.argv[1])     # Porta dinâmica do túnel ngrok
# HOST = '127.0.0.1'        # Localhost para testes locais
# PORT = 12345              # Porta local padrão
ENCODING = "utf-8"


def create_client_ssl_context():
    """
    Cria e configura o contexto SSL para o cliente.
    
    Configurado para aceitar certificados auto-assinados para uso em desenvolvimento.
    Em produção, uma validação adequada de certificados deve ser implementada.
    
    Returns:
        ssl.SSLContext: Contexto SSL configurado para conexões do cliente
        None: Se a configuração SSL falhar
    """
    try:
        context = ssl.create_default_context()
        # Configuração para certificados auto-assinados (apenas desenvolvimento)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        print("[INFO] Contexto SSL do cliente configurado com sucesso.")
        return context
    except ssl.SSLError as e:
        print(f"[ERRO] Erro na configuração do contexto SSL: {e}")
        return None
    except Exception as e:
        print(f"[ERRO] Erro inesperado na configuração SSL: {e}")
        return None


def receive_messages(sock):
    """
    Recebe e exibe continuamente mensagens do servidor.
    
    Esta função é executada em uma thread separada para lidar com mensagens recebidas
    enquanto a thread principal lida com a entrada do usuário.
    
    Args:
        sock: Conexão socket envolvida com SSL para o servidor
    """
    while True:
        try:
            msg = sock.recv(1024).decode(ENCODING)
            if not msg:
                os._exit(0)  # Saída limpa quando o servidor desconecta
            print(msg, end="")
            sys.stdout.flush()  # Garante exibição imediata das mensagens do servidor
        except Exception as e:
            print(f"[ERRO] Erro ao receber mensagem: {e}")
            os._exit(1)  # Saída com código de erro


def send_messages(sock):
    """
    Lê continuamente a entrada do usuário e envia mensagens para o servidor.
    
    Esta função é executada na thread principal e lida com toda a entrada do usuário,
    enviando-a para o servidor através da conexão SSL.
    
    Args:
        sock: Conexão socket envolvida com SSL para o servidor
    """
    while True:
        try:
            msg = input()
            sock.send(msg.encode(ENCODING))
        except:
            break


def main():
    """Inicialização do cliente e gerenciamento de conexão principal."""
    # Inicializa o contexto SSL
    ssl_context = create_client_ssl_context()
    if ssl_context is None:
        print("[ERRO] Falha ao configurar SSL. Encerrando cliente.")
        exit(1)

    # Inicializa o socket do cliente
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Estabelece a conexão TCP inicial
        client_socket.connect((HOST, PORT))
        print(f"Conectado ao servidor em {HOST}:{PORT}")

        # Envolve a conexão com criptografia SSL
        ssl_client_socket = ssl_context.wrap_socket(client_socket, server_hostname=HOST)
        print("[INFO] Handshake SSL bem-sucedido com o servidor")

        # Inicia a thread de recebimento de mensagens
        threading.Thread(
            target=receive_messages, args=(ssl_client_socket,), daemon=True
        ).start()
        
        # Trata a entrada do usuário na thread principal
        send_messages(ssl_client_socket)

    except ConnectionRefusedError:
        print("[ERRO] Não foi possível conectar ao servidor. Certifique-se de que ele está rodando.")
    except ssl.SSLError as e:
        print(f"[ERRO] Falha no handshake SSL: {e}")
    except Exception as e:
        print(f"[ERRO] Erro inesperado na conexão: {e}")
    finally:
        client_socket.close()


if __name__ == "__main__":
    main()
