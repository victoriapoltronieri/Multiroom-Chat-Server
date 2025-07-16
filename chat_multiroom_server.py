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
    sock.send("Digite o nome de usuário: ".encode(ENCODING))
    user = sock.recv(1024).decode(ENCODING).strip()
    sock.send("Digite a senha: ".encode(ENCODING))
    pwd = sock.recv(1024).decode(ENCODING).strip()
    if database.add_user(user, pwd):
        sock.send("\nUsuário registrado com sucesso!\n".encode(ENCODING))
    else:
        sock.send("\nErro: Usuário já existe ou ocorreu um problema no registro.\n".encode(ENCODING))

def _handle_login(sock):
    sock.send("\n--- FAZER LOGIN ---\n".encode(ENCODING))
    sock.send("Digite o nome de usuário: ".encode(ENCODING))
    user = sock.recv(1024).decode(ENCODING).strip()
    sock.send("Digite a senha: ".encode(ENCODING))
    pwd = sock.recv(1024).decode(ENCODING).strip()
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
    sock.send("Digite o nome da nova sala: ".encode(ENCODING))
    room_name = sock.recv(1024).decode(ENCODING).strip()

    sock.send("Esta sala será privada? (s/n): ".encode(ENCODING))
    is_private_choice = sock.recv(1024).decode(ENCODING).strip().lower()
    room_password = None
    if is_private_choice == 's':
        sock.send("Digite a senha para a sala privada: ".encode(ENCODING))
        room_password = sock.recv(1024).decode(ENCODING).strip()

    with lock:
        if database.create_room(room_name, room_password):
            rooms[room_name] = set() # Adiciona a sala ao dicionário de salas ativas
            sock.send(f"\nSala '{room_name}' criada com sucesso!\n".encode(ENCODING))
        else:
            sock.send(f"\nErro: Sala '{room_name}' já existe ou ocorreu um problema na criação.\n".encode(ENCODING))

def _handle_join_room(sock):
    sock.send("\n--- ENTRAR EM SALA ---\n".encode(ENCODING))
    sock.send("Digite o nome da sala que deseja entrar: ".encode(ENCODING))
    room_name = sock.recv(1024).decode(ENCODING).strip()
    room_password = None

    with lock:
        room_details = database.get_room_details(room_name)
        if not room_details:
            sock.send("\nErro: Sala inexistente.\n".encode(ENCODING))
            return False
        
        _, is_private, stored_password_hash = room_details

        if is_private:
            sock.send("Esta sala é privada. Digite a senha: ".encode(ENCODING))
            room_password = sock.recv(1024).decode(ENCODING).strip()
            if database.hash_password(room_password) != stored_password_hash:
                sock.send("\nErro: Senha incorreta para esta sala.\n".encode(ENCODING))
                return False
        
        # Se o usuário já estiver em uma sala, sai dela primeiro
        if sock in user_rooms:
            _handle_leave_room(sock)

        if room_name not in rooms: # Sala existe no DB mas não está ativa (ninguém nela)
            rooms[room_name] = set() # Ativa a sala
        
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
