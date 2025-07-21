"""
Servidor de Chat Multi-Sala com criptografia SSL/TLS.

Este módulo implementa um servidor de chat multi-thread seguro que suporta:
- Comunicações criptografadas SSL/TLS
- Autenticação e registro de usuários
- Múltiplas salas de chat (públicas e privadas)
- Mensagens em tempo real
- Tratamento concorrente de clientes
"""

import socket
import threading
import json
import os
import ssl
import database

# Configuração do servidor
HOST = "0.0.0.0"
PORT = 12345
ENCODING = "utf-8"

# Estruturas de dados globais para gerenciamento de clientes
clients = {}           # Mapeia objetos socket para nomes de usuário
authenticated = set()  # Conjunto de objetos socket autenticados
rooms = {}             # Mapeia nomes de salas para conjuntos de sockets de clientes ativos
user_rooms = {}        # Mapeia objetos socket para nomes de salas atuais
lock = threading.Lock()  # Lock de sincronização de threads


def create_ssl_context():
    """
    Cria e configura o contexto SSL para o servidor.
    
    Carrega os certificados SSL dos arquivos cert.pem e key.pem no diretório raiz.
    
    Returns:
        ssl.SSLContext: Contexto SSL configurado para conexões do lado servidor
        None: Se a configuração SSL falhar
    """
    try:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain("cert.pem", "key.pem")
        print("[INFO] Certificados SSL carregados com sucesso.")
        return context
    except FileNotFoundError as e:
        print(f"[ERRO] Certificados SSL não encontrados: {e}")
        print("[ERRO] Certifique-se de que cert.pem e key.pem estão no diretório raiz.")
        return None
    except ssl.SSLError as e:
        print(f"[ERRO] Erro ao carregar certificados SSL: {e}")
        return None
    except Exception as e:
        print(f"[ERRO] Erro inesperado na configuração SSL: {e}")
        return None


def broadcast(msg, room, sender=None):
    """
    Transmite uma mensagem para todos os clientes em uma sala específica.
    
    Args:
        msg (str): Mensagem para transmitir
        room (str): Nome da sala de destino
        sender (socket, opcional): Socket do remetente para excluir da transmissão
        
    Nota:
        Esta função deve ser chamada dentro de um bloco `with lock:` para segurança de thread.
    """
    if not msg.endswith("\n"):
        msg += "\n"

    dead_sockets = []
    for client in list(rooms.get(room, [])):
        if client != sender:
            try:
                client.send(msg.encode(ENCODING))
            except Exception as e:
                print(
                    f"[INFO] Falha ao enviar mensagem para {clients.get(client, 'desconhecido')}. Marcando para remoção: {e}"
                )
                dead_sockets.append(client)

    # Limpa clientes desconectados
    for dead_socket in dead_sockets:
        _handle_leave_room(dead_socket, silent=True)


def _handle_register(sock):
    """Gerencia o processo de registro de usuário."""
    sock.send("\n--- REGISTRAR NOVO USUÁRIO ---\n".encode(ENCODING))
    sock.send(
        "Digite o usuário e a senha, separados por espaço (ex: novo_usuario 12345): ".encode(
            ENCODING
        )
    )

    response = sock.recv(1024).decode(ENCODING).strip()

    try:
        user, pwd = response.split(" ", 1)
    except ValueError:
        sock.send(
            "\nFormato inválido. O usuário e a senha devem ser separados por espaço.\n".encode(
                ENCODING
            )
        )
        return

    if database.add_user(user, pwd):
        sock.send("\nUsuário registrado com sucesso!\n".encode(ENCODING))
    else:
        sock.send(
            "\nErro: Usuário já existe ou ocorreu um problema no registro.\n".encode(
                ENCODING
            )
        )


def _handle_login(sock):
    """
    Gerencia o processo de autenticação de usuário.
    
    Args:
        sock: Conexão socket do cliente
        
    Returns:
        bool: True se login bem-sucedido, False caso contrário
    """
    sock.send("\n--- FAZER LOGIN ---\n".encode(ENCODING))
    sock.send(
        "Digite seu usuário e senha, separados por espaço (ex: usuario_existente 12345): ".encode(
            ENCODING
        )
    )

    response = sock.recv(1024).decode(ENCODING).strip()

    try:
        user, pwd = response.split(" ", 1)
    except ValueError:
        sock.send("\nFormato inválido. Login falhou.\n".encode(ENCODING))
        return False

    if database.check_user_credentials(user, pwd):
        authenticated.add(sock)
        clients[sock] = user
        sock.send("\nLogin bem-sucedido!\n".encode(ENCODING))
        return True
    else:
        sock.send("\nErro: Nome de usuário ou senha inválidos.\n".encode(ENCODING))
        return False


def _handle_list_rooms(sock):
    """Envia lista de salas disponíveis para o cliente."""
    all_rooms = database.get_rooms()
    if all_rooms:
        room_list_str = "\n".join(
            [
                f"- {name} (Privada)" if is_private else f"- {name}"
                for name, is_private in all_rooms
            ]
        )
        sock.send(f"\n--- SALAS DISPONÍVEIS ---\n{room_list_str}\n".encode(ENCODING))
    else:
        sock.send("\nNenhuma sala disponível.\n".encode(ENCODING))


def _handle_create_room(sock):
    """Gerencia o processo de criação de salas públicas e privadas."""
    sock.send("\n--- CRIAR NOVA SALA ---\n".encode(ENCODING))
    sock.send(
        "Use o formato: <nome_sala> <s/n para privada> [senha_se_privada]\n".encode(
            ENCODING
        )
    )
    sock.send("Exemplos:\n".encode(ENCODING))
    sock.send("  - Sala pública: public_room n\n".encode(ENCODING))
    sock.send("  - Sala privada: private_room s 12345\n".encode(ENCODING))
    sock.send("Sua entrada: ".encode(ENCODING))

    response = sock.recv(1024).decode(ENCODING).strip()
    parts = response.split()

    if len(parts) < 2:
        sock.send(
            "\nFormato inválido. Você deve fornecer pelo menos o nome da sala e 's' ou 'n'.\n".encode(
                ENCODING
            )
        )
        return

    room_name = parts[0]
    is_private_choice = parts[1].lower()
    room_password = None

    if is_private_choice == "s":
        if len(parts) < 3:
            sock.send(
                "\nFormato inválido. Salas privadas exigem uma senha.\n".encode(
                    ENCODING
                )
            )
            return
        room_password = parts[2]
    elif is_private_choice != "n":
        sock.send(
            "\nOpção inválida para privacidade. Use 's' para sim ou 'n' para não.\n".encode(
                ENCODING
            )
        )
        return

    with lock:
        if database.create_room(room_name, room_password):
            rooms[room_name] = set()
            sock.send(f"\nSala '{room_name}' criada com sucesso!\n".encode(ENCODING))
        else:
            sock.send(
                f"\nErro: Sala '{room_name}' já existe ou ocorreu um problema na criação.\n".encode(
                    ENCODING
                )
            )


def _handle_join_room(sock):
    """
    Gerencia o processo de entrada em salas com validação de senha para salas privadas.
    
    Args:
        sock: Conexão socket do cliente
        
    Returns:
        bool: True se entrou na sala com sucesso, False caso contrário
    """
    sock.send("\n--- ENTRAR EM SALA ---\n".encode(ENCODING))
    sock.send(
        "Digite o nome da sala e a senha (se for privada), separados por espaço:\n".encode(
            ENCODING
        )
    )
    sock.send("Ex: minha_sala_privada 12345\n".encode(ENCODING))
    sock.send("Sua entrada: ".encode(ENCODING))

    response = sock.recv(1024).decode(ENCODING).strip()
    parts = response.split()

    if not parts:
        sock.send("\nEntrada inválida.\n".encode(ENCODING))
        return False

    room_name = parts[0]
    user_provided_password = parts[1] if len(parts) > 1 else None

    with lock:
        room_details = database.get_room_details(room_name)
        if not room_details:
            sock.send("\nErro: Sala inexistente.\n".encode(ENCODING))
            return False

        _, is_private, stored_password_hash = room_details

        # Valida senha para salas privadas
        if is_private:
            if user_provided_password is None:
                sock.send(
                    "\nErro: Esta sala é privada e requer uma senha.\n".encode(ENCODING)
                )
                return False
            if database.hash_password(user_provided_password) != stored_password_hash:
                sock.send("\nErro: Senha incorreta para esta sala.\n".encode(ENCODING))
                return False

        # Remove usuário da sala atual se já estiver em uma
        if sock in user_rooms:
            _handle_leave_room(sock, silent=True)

        # Inicializa sala se for o primeiro usuário entrando
        if room_name not in rooms:
            rooms[room_name] = set()

        # Adiciona usuário à sala
        rooms[room_name].add(sock)
        user_rooms[sock] = room_name

        # Notifica outros usuários na sala
        broadcast(f"*** {clients[sock]} entrou na sala. ***", room_name, sock)

    sock.send(f"\nVocê entrou na sala '{room_name}'.\n".encode(ENCODING))
    return True


def _handle_leave_room(sock, silent=False):
    """
    Remove um cliente de sua sala atual.
    
    Args:
        sock: Conexão socket do cliente
        silent (bool): Se True, não envia mensagem de confirmação para o cliente
        
    Nota:
        Esta função deve ser chamada dentro de um bloco `with lock:` para segurança de thread.
    """
    room = user_rooms.pop(sock, None)
    if room and sock in rooms.get(room, set()):
        rooms[room].remove(sock)
        broadcast(
            f"*** {clients.get(sock, 'Um usuário')} saiu da sala. ***", room, sock
        )
    if not silent:
        try:
            sock.send("\nVocê saiu da sala.\n".encode(ENCODING))
        except Exception as e:
            print(f"[INFO] Não foi possível notificar cliente sobre saída da sala: {e}")


def _handle_chat_mode(sock):
    """
    Gerencia mensagens de chat em tempo real dentro de uma sala.
    
    Args:
        sock: Conexão socket do cliente
        
    Returns:
        bool: True para retornar ao menu principal, False se cliente desconectou
    """
    sock.send("\n--- MODO CHAT ---\n".encode(ENCODING))
    sock.send(
        "Você está na sala. Digite suas mensagens. Para voltar ao menu, digite /menu. Para sair da sala, digite /leave.\n".encode(
            ENCODING
        )
    )
    while True:
        try:
            data = sock.recv(1024).decode(ENCODING)
            if not data:
                return False

            if data.strip().lower() == "/menu":
                return True
            elif data.strip().lower() == "/leave":
                _handle_leave_room(sock)
                return True
            else:
                with lock:
                    room = user_rooms.get(sock)
                    if room:
                        msg = f"[{clients[sock]}@{room}]: {data.strip()}"
                        broadcast(msg, room, sock)
                    else:
                        pass
                if not room:
                    sock.send(
                        "Você não está em uma sala. Digite /menu para voltar ao menu principal.\n".encode(
                            ENCODING
                        )
                    )
        except Exception as e:
            return False


def handle_client(sock):
    """
    Função principal de tratamento de cliente que gerencia o ciclo de vida da sessão do cliente.
    
    Implementa uma máquina de estados com três estados:
    - AUTH_MENU: Autenticação (registro/login)
    - MAIN_MENU: Menu principal da aplicação
    - IN_CHAT_ROOM: Modo de chat ativo
    
    Args:
        sock: Conexão socket do cliente envolvida com SSL
    """
    current_state = "AUTH_MENU"

    try:
        while True:
            if current_state == "AUTH_MENU":
                menu_message = """
----------------------------------------
|        Bem-vindo ao Chat!            |
----------------------------------------
| Escolha uma opção:                   |
|                                      |
| 1. Registrar Novo Usuário            |
| 2. Fazer Login                       |
|                                      |
----------------------------------------
Sua escolha: 
""".encode(
                    ENCODING
                )
                sock.send(menu_message)

                choice = sock.recv(1024).decode(ENCODING).strip()

                if choice == "1":
                    _handle_register(sock)
                elif choice == "2":
                    if _handle_login(sock):
                        current_state = "MAIN_MENU"
                else:
                    sock.send(
                        "\nOpção inválida. Por favor, escolha 1 ou 2.\n".encode(
                            ENCODING
                        )
                    )

            elif current_state == "MAIN_MENU":
                # Constrói menu dinâmico baseado no estado do usuário
                menu_options = [
                    "1. Listar Salas",
                    "2. Criar Sala",
                    "3. Entrar em Sala",
                    "4. Sair (Desconectar)",
                ]

                in_room = sock in user_rooms
                if in_room:
                    current_room_name = user_rooms[sock]
                    menu_options.insert(
                        4, f"5. Sair da Sala Atual ({current_room_name})"
                    )
                    menu_options.insert(5, "6. Voltar para o Chat")

                menu_header = "\n----------------------------------------\n|        Menu Principal                |\n----------------------------------------\n"
                menu_body = "\n".join([f"| {opt:<36} |" for opt in menu_options])
                menu_footer = (
                    "\n----------------------------------------\nSua escolha: "
                )

                menu_message = (menu_header + menu_body + menu_footer).encode(ENCODING)
                sock.send(menu_message)

                choice = sock.recv(1024).decode(ENCODING).strip()

                if choice == "1":
                    _handle_list_rooms(sock)
                elif choice == "2":
                    _handle_create_room(sock)
                elif choice == "3":
                    if _handle_join_room(sock):
                        current_state = "IN_CHAT_ROOM"
                elif choice == "4":
                    break
                elif choice == "5" and in_room:
                    with lock:
                        _handle_leave_room(sock)
                elif choice == "6" and in_room:
                    current_state = "IN_CHAT_ROOM"
                else:
                    sock.send("\nOpção inválida. Tente novamente.\n".encode(ENCODING))

            elif current_state == "IN_CHAT_ROOM":
                if not _handle_chat_mode(sock):
                    break
                else:
                    current_state = "MAIN_MENU"

    except Exception as e:
        print(f"[ERRO] Erro fatal na thread do cliente para {clients.get(sock, 'desconhecido')}: {e}")
    finally:
        # Limpeza quando cliente desconecta
        with lock:
            user = clients.pop(sock, None)
            room = user_rooms.pop(sock, None)
            if room and user and rooms.get(room):
                print(f"[INFO] Limpando usuário {user} da sala {room}.")
                rooms[room].discard(sock)
                broadcast(f"*** {user} desconectou-se. ***", room)

            if sock in authenticated:
                authenticated.discard(sock)
        sock.close()


def main():
    """Loop principal de inicialização do servidor e tratamento de conexões."""
    # Inicializa contexto SSL
    ssl_context = create_ssl_context()
    if ssl_context is None:
        print("[ERRO] Falha ao configurar SSL. Encerrando servidor.")
        exit(1)

    # Inicializa socket do servidor
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    # Inicializa banco de dados
    database.init_db()

    # Carrega salas existentes do banco de dados para a memória
    global rooms
    rooms = {room_name: set() for room_name, _ in database.get_rooms()}
    print(f"[INFO] Servidor SSL rodando em {HOST}:{PORT}")

    try:
        while True:
            client_socket, addr = server_socket.accept()
            print(f"[INFO] Nova conexão de {addr}")

            try:
                # Envolve socket aceito com SSL
                ssl_client_socket = ssl_context.wrap_socket(client_socket, server_side=True)
                print(f"[INFO] Handshake SSL bem-sucedido com {addr}")
                threading.Thread(
                    target=handle_client, args=(ssl_client_socket,), daemon=True
                ).start()
            except ssl.SSLError as e:
                print(f"[ERRO] Falha no handshake SSL com {addr}: {e}")
                client_socket.close()
            except Exception as e:
                print(f"[ERRO] Erro inesperado ao processar conexão de {addr}: {e}")
                client_socket.close()

    except KeyboardInterrupt:
        print("\n[INFO] Encerrando o servidor...")
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
