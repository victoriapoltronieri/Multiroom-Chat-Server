import socket
import threading
import json
# import hashlib
import os
import database # Importa o módulo de banco de dados

HOST = '0.0.0.0'
PORT = 12345
# HOST = '127.0.0.1'
# PORT = 12345
ENCODING = 'utf-8'
# USER_DB = 'users.json'

clients = {}           # socket -> username
authenticated = set()  # sockets autenticados
rooms = {}             # nome -> set de socket (clientes ativos na sala)
user_rooms = {}        # socket -> nome da sala
lock = threading.Lock()

# def load_users():
#     if os.path.exists(USER_DB):
#         with open(USER_DB, 'r') as f:
#             return json.load(f)
#     return {}

# def save_users(users):
#     with open(USER_DB, 'w') as f:
#         json.dump(users, f)

# def hash_password(password):
#     return hashlib.sha256(password.encode(ENCODING)).hexdigest()

def broadcast(msg, room, sender=None):
    with lock:
        for client in rooms.get(room, set()):
            if client != sender:
                try:
                    client.send(msg.encode(ENCODING))
                except Exception as e:
                    # Remove o cliente da sala e do user_rooms se houver erro no envio
                    if client in rooms.get(room, set()):
                        rooms[room].remove(client)
                    if client in user_rooms and user_rooms[client] == room:
                        del user_rooms[client]
                    # Opcional: fechar o socket do cliente se o erro for grave
                    # client.close()
                    pass

def _handle_register(sock):
    sock.send("\n--- REGISTRAR NOVO USUÁRIO ---\n".encode(ENCODING))
    sock.send("Digite o usuário e a senha, separados por espaço (ex: novo_usuario 12345): ".encode(ENCODING))
    
    # Recebe a resposta do cliente (ex: "novo_usuario 12345")
    response = sock.recv(1024).decode(ENCODING).strip()
    
    try:
        # Divide a string recebida em duas partes no primeiro espaço encontrado.
        user, pwd = response.split(' ', 1)
    except ValueError:
        # Se o cliente não digitar no formato esperado (ex: sem espaço), envia um erro.
        sock.send("\nFormato inválido. O usuário e a senha devem ser separados por espaço.\n".encode(ENCODING))
        return

    if database.add_user(user, pwd):
        sock.send("\nUsuário registrado com sucesso!\n".encode(ENCODING))
    else:
        sock.send("\nErro: Usuário já existe ou ocorreu um problema no registro.\n".encode(ENCODING))

def _handle_login(sock):
    sock.send("\n--- FAZER LOGIN ---\n".encode(ENCODING))
    # Pede ao cliente para digitar usuário e senha em uma única linha.
    sock.send("Digite seu usuário e senha, separados por espaço (ex: usuario_existente 12345): ".encode(ENCODING))
    
    # Recebe a resposta do cliente.
    response = sock.recv(1024).decode(ENCODING).strip()

    try:
        # Tenta dividir a resposta em usuário e senha.
        user, pwd = response.split(' ', 1)
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
        room_list_str = "\n".join([f"- {name} (Privada)" if is_private else f"- {name}" for name, is_private in all_rooms])
        sock.send(f"\n--- SALAS DISPONÍVEIS ---\n{room_list_str}\n".encode(ENCODING))
    else:
        sock.send("\nNenhuma sala disponível.\n".encode(ENCODING))

def _handle_create_room(sock):
    sock.send("\n--- CRIAR NOVA SALA ---\n".encode(ENCODING))
    # Pede ao cliente para digitar os detalhes da sala em uma única linha.
    # Formato para sala pública: nome_da_sala n
    # Formato para sala privada: nome_da_sala s senha_da_sala
    sock.send("Use o formato: <nome_sala> <s/n para privada> [senha_se_privada]\n".encode(ENCODING))
    sock.send("Exemplos:\n".encode(ENCODING))
    sock.send("  - Sala pública: public_room n\n".encode(ENCODING))
    sock.send("  - Sala privada: private_room s 12345\n".encode(ENCODING))
    sock.send("Sua entrada: ".encode(ENCODING))

    # Recebe a resposta completa do cliente.
    response = sock.recv(1024).decode(ENCODING).strip()
    parts = response.split()

    # Validação básica da entrada.
    if len(parts) < 2:
        sock.send("\nFormato inválido. Você deve fornecer pelo menos o nome da sala e 's' ou 'n'.\n".encode(ENCODING))
        return

    room_name = parts[0]
    is_private_choice = parts[1].lower()
    room_password = None

    if is_private_choice == 's':
        if len(parts) < 3:
            # Se a sala for privada, uma senha é obrigatória.
            sock.send("\nFormato inválido. Salas privadas exigem uma senha.\n".encode(ENCODING))
            return
        room_password = parts[2]
    elif is_private_choice != 'n':
        # A segunda parte deve ser 's' ou 'n'.
        sock.send("\nOpção inválida para privacidade. Use 's' para sim ou 'n' para não.\n".encode(ENCODING))
        return

    with lock:
        if database.create_room(room_name, room_password):
            rooms[room_name] = set() # Adiciona a sala ao dicionário de salas ativas
            sock.send(f"\nSala '{room_name}' criada com sucesso!\n".encode(ENCODING))
        else:
            sock.send(f"\nErro: Sala '{room_name}' já existe ou ocorreu um problema na criação.\n".encode(ENCODING))


def _handle_join_room(sock):
    sock.send("\n--- ENTRAR EM SALA ---\n".encode(ENCODING))
    # Pede ao cliente para digitar o nome da sala e a senha (se necessária) em uma linha.
    sock.send("Digite o nome da sala e a senha (se for privada), separados por espaço:\n".encode(ENCODING))
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
                sock.send("\nErro: Esta sala é privada e requer uma senha.\n".encode(ENCODING))
                return False
            # Compara a senha fornecida com a senha armazenada.
            if database.hash_password(user_provided_password) != stored_password_hash:
                sock.send("\nErro: Senha incorreta para esta sala.\n".encode(ENCODING))
                return False
        
        # Se o usuário já estiver em uma sala, remove-o da sala antiga primeiro.
        if sock in user_rooms:
            _handle_leave_room(sock)

        # Ativa a sala se for a primeira pessoa a entrar.
        if room_name not in rooms:
            rooms[room_name] = set()
        
        # Adiciona o usuário à nova sala.
        rooms[room_name].add(sock)
        user_rooms[sock] = room_name
        broadcast(f"{clients[sock]} entrou na sala.", room_name, sock)
        sock.send(f"\nVocê entrou na sala '{room_name}'.\n".encode(ENCODING))
        return True

def _handle_leave_room(sock):
    with lock:
        room = user_rooms.pop(sock, None)
        if room and sock in rooms[room]:
            rooms[room].remove(sock)
            broadcast(f"{clients[sock]} saiu da sala.", room, sock)
    sock.send("\nVocê saiu da sala.\n".encode(ENCODING))

def _handle_chat_mode(sock):
    sock.send("\n--- MODO CHAT ---\n".encode(ENCODING))
    sock.send("Você está na sala. Digite suas mensagens. Para voltar ao menu, digite /menu. Para sair da sala, digite /leave.\n".encode(ENCODING))
    while True:
        try:
            data = sock.recv(1024).decode(ENCODING)
            if not data:
                return False # Cliente desconectou

            if data.strip().lower() == "/menu":
                return True # Voltar ao menu principal
            elif data.strip().lower() == "/leave":
                _handle_leave_room(sock)
                return True # Voltar ao menu principal após sair da sala
            else:
                room = user_rooms.get(sock)
                if room:
                    msg = f"[{clients[sock]}@{room}]: {data}"
                    broadcast(msg, room, sock)
                else:
                    sock.send("Você não está em uma sala. Digite /menu para voltar ao menu principal.\n".encode(ENCODING))
        except Exception as e:
            # print(f"Erro no modo chat para {clients.get(sock, 'desconhecido')}: {e}")
            return False # Erro, desconectar cliente

def handle_client(sock):
    current_state = "AUTH_MENU" # AUTH_MENU, MAIN_MENU, IN_CHAT_ROOM

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
""".encode(ENCODING)
                sock.send(menu_message)
                
                choice = sock.recv(1024).decode(ENCODING).strip()

                if choice == '1':
                    _handle_register(sock)
                elif choice == '2':
                    if _handle_login(sock):
                        current_state = "MAIN_MENU"
                else:
                    sock.send("\nOpção inválida. Por favor, escolha 1 ou 2.\n".encode(ENCODING))
            
            elif current_state == "MAIN_MENU":
                menu_message_authenticated = """
----------------------------------------
|        Menu Principal                |
----------------------------------------
| 1. Listar Salas                      |
| 2. Criar Sala                        |
| 3. Entrar em Sala                    |
| 4. Sair da Sala Atual                |
| 5. Sair (Desconectar)                |
----------------------------------------
Sua escolha: 
""".encode(ENCODING)
                sock.send(menu_message_authenticated)

                choice = sock.recv(1024).decode(ENCODING).strip()

                if choice == '1': # Listar Salas
                    _handle_list_rooms(sock)
                elif choice == '2': # Criar Sala
                    _handle_create_room(sock)
                elif choice == '3': # Entrar em Sala
                    if _handle_join_room(sock):
                        current_state = "IN_CHAT_ROOM"
                elif choice == '4': # Sair da Sala Atual
                    _handle_leave_room(sock)
                elif choice == '5': # Sair (Desconectar)
                    break # Sai do loop e desconecta o cliente
                else:
                    sock.send("\nOpção inválida. Tente novamente.\n".encode(ENCODING))
            
            elif current_state == "IN_CHAT_ROOM":
                if not _handle_chat_mode(sock): # Se _handle_chat_mode retornar False (desconexão)
                    break
                else: # Se _handle_chat_mode retornar True (voltar ao menu principal)
                    current_state = "MAIN_MENU"

    except Exception as e:
        # print(f"Erro no handle_client para {clients.get(sock, 'desconhecido')}: {e}")
        pass # Ignora erros para evitar que o servidor caia por um cliente
    finally:
        with lock:
            user = clients.pop(sock, None)
            room = user_rooms.pop(sock, None)
            if room:
                rooms[room].discard(sock)
                if user: # Só broadcast se o usuário for conhecido
                    broadcast(f"🔕 {user} saiu da sala.", room, sock)
            authenticated.discard(sock)
        sock.close()

# === MAIN ===
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()

# Inicializa o banco de dados
database.init_db()

# Carrega as salas existentes do banco de dados para a memória
rooms = {room_name: set() for room_name, _ in database.get_rooms()}
print(f"Servidor rodando em {HOST}:{PORT}")

try:
    while True:
        client_socket, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()
except KeyboardInterrupt:
    print("Encerrando o servidor...")
finally:
    server_socket.close()