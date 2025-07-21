import socket
import threading
import json
import os
import ssl
import database

HOST = "0.0.0.0"
PORT = 12345
# HOST = '127.0.0.1'
# PORT = 12345
ENCODING = "utf-8"

clients = {}  # socket -> username
authenticated = set()  # sockets autenticados
rooms = {}  # nome -> set de socket (clientes ativos na sala)
user_rooms = {}  # socket -> nome da sala
lock = threading.Lock()


def create_ssl_context():
    """
    Cria e configura o contexto SSL para o servidor.
    Carrega os certificados cert.pem e key.pem do diretório raiz.
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
        print(f"[ERRO] Erro inesperado ao configurar SSL: {e}")
        return None


def broadcast(msg, room, sender=None):
    """
    Envia uma mensagem para TODOS os clientes em uma sala.
    IMPORTANTE: Esta função deve ser chamada de dentro de um bloco `with lock:`.
    """
    # Garante que a mensagem sempre termine com uma nova linha para exibição correta.
    if not msg.endswith("\n"):
        msg += "\n"

    dead_sockets = []
    # Itera sobre uma cópia da lista de clientes para evitar erros de iteração.
    for client in list(rooms.get(room, [])):
        if client != sender:
            try:
                client.send(msg.encode(ENCODING))
            except Exception as e:
                print(
                    f"[INFO] Erro ao enviar para {clients.get(client, 'desconhecido')}. Marcando para remoção: {e}"
                )
                dead_sockets.append(client)

    # Remove os sockets mortos após a iteração.
    for dead_socket in dead_sockets:
        _handle_leave_room(dead_socket, silent=True)


def _handle_register(sock):
    sock.send("\n--- REGISTRAR NOVO USUÁRIO ---\n".encode(ENCODING))
    # Pede ao cliente para digitar usuário e senha em uma única linha, separados por espaço.
    sock.send(
        "Digite o usuário e a senha, separados por espaço (ex: novo_usuario 12345): ".encode(
            ENCODING
        )
    )

    # Recebe a resposta do cliente (ex: "novo_usuario 12345")
    response = sock.recv(1024).decode(ENCODING).strip()

    try:
        # Divide a string recebida em duas partes no primeiro espaço encontrado.
        user, pwd = response.split(" ", 1)
    except ValueError:
        # Se o cliente não digitar no formato esperado (ex: sem espaço), envia um erro.
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
    sock.send("\n--- FAZER LOGIN ---\n".encode(ENCODING))
    # Pede ao cliente para digitar usuário e senha em uma única linha.
    sock.send(
        "Digite seu usuário e senha, separados por espaço (ex: usuario_existente 12345): ".encode(
            ENCODING
        )
    )

    # Recebe a resposta do cliente.
    response = sock.recv(1024).decode(ENCODING).strip()

    try:
        # Tenta dividir a resposta em usuário e senha.
        user, pwd = response.split(" ", 1)
    except ValueError:
        # Se o formato for inválido, envia um erro e falha o login.
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
    sock.send("\n--- CRIAR NOVA SALA ---\n".encode(ENCODING))
    # Pede ao cliente para digitar os detalhes da sala em uma única linha.
    # Formato para sala pública: nome_da_sala n
    # Formato para sala privada: nome_da_sala s senha_da_sala
    sock.send(
        "Use o formato: <nome_sala> <s/n para privada> [senha_se_privada]\n".encode(
            ENCODING
        )
    )
    sock.send("Exemplos:\n".encode(ENCODING))
    sock.send("  - Sala pública: public_room n\n".encode(ENCODING))
    sock.send("  - Sala privada: private_room s 12345\n".encode(ENCODING))
    sock.send("Sua entrada: ".encode(ENCODING))

    # Recebe a resposta completa do cliente.
    response = sock.recv(1024).decode(ENCODING).strip()
    parts = response.split()

    # Validação básica da entrada.
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
            # Se a sala for privada, uma senha é obrigatória.
            sock.send(
                "\nFormato inválido. Salas privadas exigem uma senha.\n".encode(
                    ENCODING
                )
            )
            return
        room_password = parts[2]
    elif is_private_choice != "n":
        # A segunda parte deve ser 's' ou 'n'.
        sock.send(
            "\nOpção inválida para privacidade. Use 's' para sim ou 'n' para não.\n".encode(
                ENCODING
            )
        )
        return

    with lock:
        if database.create_room(room_name, room_password):
            rooms[room_name] = set()  # Adiciona a sala ao dicionário de salas ativas
            sock.send(f"\nSala '{room_name}' criada com sucesso!\n".encode(ENCODING))
        else:
            sock.send(
                f"\nErro: Sala '{room_name}' já existe ou ocorreu um problema na criação.\n".encode(
                    ENCODING
                )
            )


def _handle_join_room(sock):
    sock.send("\n--- ENTRAR EM SALA ---\n".encode(ENCODING))
    # Pede ao cliente para digitar o nome da sala e a senha (se necessária) em uma linha.
    sock.send(
        "Digite o nome da sala e a senha (se for privada), separados por espaço:\n".encode(
            ENCODING
        )
    )
    sock.send("Ex: minha_sala_privada 12345\n".encode(ENCODING))
    sock.send("Sua entrada: ".encode(ENCODING))

    # Recebe a resposta do cliente.
    response = sock.recv(1024).decode(ENCODING).strip()
    parts = response.split()

    if not parts:
        sock.send("\nEntrada inválida.\n".encode(ENCODING))
        return False

    room_name = parts[0]
    # A senha é a segunda parte, se existir. Se não, é None.
    user_provided_password = parts[1] if len(parts) > 1 else None

    with lock:
        room_details = database.get_room_details(room_name)
        if not room_details:
            sock.send("\nErro: Sala inexistente.\n".encode(ENCODING))
            return False

        _, is_private, stored_password_hash = room_details

        if is_private:
            # Se a sala é privada, a senha é obrigatória.
            if user_provided_password is None:
                sock.send(
                    "\nErro: Esta sala é privada e requer uma senha.\n".encode(ENCODING)
                )
                return False
            # Compara a senha fornecida com a senha armazenada.
            if database.hash_password(user_provided_password) != stored_password_hash:
                sock.send("\nErro: Senha incorreta para esta sala.\n".encode(ENCODING))
                return False

        # Se o usuário já estiver em uma sala, remove-o da sala antiga primeiro.
        if sock in user_rooms:
            _handle_leave_room(sock, silent=True)

        # Ativa a sala se for a primeira pessoa a entrar.
        if room_name not in rooms:
            rooms[room_name] = set()

        # Adiciona o usuário à nova sala.
        rooms[room_name].add(sock)
        user_rooms[sock] = room_name

        # Notifica todos na sala (exceto o novo usuário) sobre a entrada.
        broadcast(f"*** {clients[sock]} entrou na sala. ***", room_name, sock)

    # Envia a confirmação para o próprio usuário FORA do lock.
    sock.send(f"\nVocê entrou na sala '{room_name}'.\n".encode(ENCODING))
    return True


def _handle_leave_room(sock, silent=False):
    """
    Remove um cliente de uma sala.
    IMPORTANTE: Esta função deve ser chamada de dentro de um bloco `with lock:`.
    """
    room = user_rooms.pop(sock, None)
    if room and sock in rooms.get(room, set()):
        rooms[room].remove(sock)
        # Notifica os outros que o usuário saiu.
        broadcast(
            f"*** {clients.get(sock, 'Um usuário')} saiu da sala. ***", room, sock
        )
    if not silent:
        try:
            sock.send("\nVocê saiu da sala.\n".encode(ENCODING))
        except Exception as e:
            print(f"[INFO] Não foi possível notificar cliente sobre saída da sala: {e}")


def _handle_chat_mode(sock):
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
                return False  # Cliente desconectou

            if data.strip().lower() == "/menu":
                return True  # Voltar ao menu principal
            elif data.strip().lower() == "/leave":
                _handle_leave_room(sock)
                return True  # Voltar ao menu principal após sair da sala
            else:
                with lock:
                    room = user_rooms.get(sock)
                    if room:
                        # Formata a mensagem e envia para todos na sala, exceto o remetente.
                        msg = f"[{clients[sock]}@{room}]: {data.strip()}"
                        broadcast(msg, room, sock)
                    else:
                        # Esta parte é executada fora do lock para evitar deadlock
                        pass
                if not room:
                    sock.send(
                        "Você não está em uma sala. Digite /menu para voltar ao menu principal.\n".encode(
                            ENCODING
                        )
                    )
        except Exception as e:
            # print(f"Erro no modo chat para {clients.get(sock, 'desconhecido')}: {e}")
            return False  # Erro, desconectar cliente


def handle_client(sock):
    current_state = "AUTH_MENU"  # AUTH_MENU, MAIN_MENU, IN_CHAT_ROOM

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
                # Constrói o menu dinamicamente com base no estado do usuário.
                menu_options = [
                    "1. Listar Salas",
                    "2. Criar Sala",
                    "3. Entrar em Sala",
                    "4. Sair (Desconectar)",
                ]

                in_room = sock in user_rooms
                if in_room:
                    # Se estiver em uma sala, insere as opções contextuais na posição correta.
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
                elif choice == "4":  # Sair (Desconectar)
                    break
                elif choice == "5" and in_room:  # Sair da Sala Atual
                    with lock:
                        _handle_leave_room(sock)
                elif choice == "6" and in_room:  # Voltar para o Chat
                    current_state = "IN_CHAT_ROOM"
                else:
                    sock.send("\nOpção inválida. Tente novamente.\n".encode(ENCODING))

            elif current_state == "IN_CHAT_ROOM":
                if not _handle_chat_mode(
                    sock
                ):  # Se _handle_chat_mode retornar False (desconexão)
                    break
                else:  # Se _handle_chat_mode retornar True (voltar ao menu principal)
                    current_state = "MAIN_MENU"

    except Exception as e:
        # Aumenta a visibilidade de erros fatais na thread do cliente.
        print(f"[ERRO FATAL] na thread para {clients.get(sock, 'desconhecido')}: {e}")
    finally:
        # Bloco de limpeza robusto para quando um cliente desconecta.
        with lock:
            user = clients.pop(sock, None)
            room = user_rooms.pop(sock, None)
            if room and user and rooms.get(room):
                print(f"[INFO] Limpando {user} da sala {room}.")
                rooms[room].discard(sock)
                # Notifica os outros que o usuário se desconectou.
                broadcast(f"*** {user} desconectou-se. ***", room)

            if sock in authenticated:
                authenticated.discard(sock)
        sock.close()


# === MAIN ===
# Cria e configura o contexto SSL
ssl_context = create_ssl_context()
if ssl_context is None:
    print("[ERRO] Não foi possível configurar SSL. Encerrando servidor.")
    exit(1)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()

# Inicializa o banco de dados
database.init_db()

# Carrega as salas existentes do banco de dados para a memória
rooms = {room_name: set() for room_name, _ in database.get_rooms()}
print(f"Servidor SSL rodando em {HOST}:{PORT}")

try:
    while True:
        client_socket, addr = server_socket.accept()
        print(f"[INFO] Nova conexão de {addr}")

        try:
            # Envolve o socket aceito com SSL
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
    print("Encerrando o servidor...")
finally:
    server_socket.close()
