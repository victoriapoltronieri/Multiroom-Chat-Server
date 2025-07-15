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

def handle_client(sock):
    sock.send("Bem-vindo. Use /register ou /login\n".encode(ENCODING))

    try:
        while True:
            data = sock.recv(1024).decode(ENCODING)
            if not data:
                break

            if sock not in authenticated:
                if data.startswith("/register"):
                    _, user, pwd = data.strip().split()
                    # password_h = hash_password(pwd)
                    if database.add_user(user, pwd):
                        sock.send("Usuário registrado com sucesso.\n".encode(ENCODING))
                    else:
                        sock.send("Usuário já existe.\n".encode(ENCODING))

                elif data.startswith("/login"):
                    _, user, pwd = data.strip().split()
                    if database.check_user_credentials(user, pwd):
                        authenticated.add(sock)
                        clients[sock] = user
                        sock.send("Login bem-sucedido.\n".encode(ENCODING))
                    else:
                        sock.send("Login inválido.\n".encode(ENCODING))
                else:
                    sock.send("Comando inválido. Use /register ou /login.\n".encode(ENCODING))
                continue

            if data.startswith("/list"):
                all_rooms = database.get_rooms()
                if all_rooms:
                    room_list_str = "\n".join([f"- {name} (Privada)" if is_private else f"- {name}" for name, is_private in all_rooms])
                    sock.send(f"Salas disponíveis:\n{room_list_str}\n".encode(ENCODING))
                else:
                    sock.send("Nenhuma sala disponível.\n".encode(ENCODING))

            elif data.startswith("/create"):
                parts = data.strip().split()
                if len(parts) < 2:
                    sock.send("Uso: /create <nome_da_sala> [senha]\n".encode(ENCODING))
                    continue
                room_name = parts[1]
                room_password = parts[2] if len(parts) > 2 else None

                with lock:
                    if database.create_room(room_name, room_password):
                        rooms[room_name] = set() # Adiciona a sala ao dicionário de salas ativas
                        sock.send(f"Sala '{room_name}' criada com sucesso.\n".encode(ENCODING))
                    else:
                        sock.send(f"Sala '{room_name}' já existe ou ocorreu um erro.\n".encode(ENCODING))

            elif data.startswith("/join"):
                parts = data.strip().split()
                if len(parts) < 2:
                    sock.send("Uso: /join <nome_da_sala> [senha]\n".encode(ENCODING))
                    continue
                room_name = parts[1]
                room_password = parts[2] if len(parts) > 2 else None

                with lock:
                    room_details = database.get_room_details(room_name)
                    if not room_details:
                        sock.send("Sala inexistente.\n".encode(ENCODING))
                    else:
                        # Correção aqui: get_room_details retorna 3 valores (name, is_private, password_hash)
                        room_name_from_db, is_private, stored_password_hash = room_details                        
                        if is_private and not room_password:
                            sock.send("Esta sala é privada. Por favor, forneça a senha.\n".encode(ENCODING))
                        elif is_private and database.hash_password(room_password) != stored_password_hash:
                            sock.send("Senha incorreta para esta sala.\n".encode(ENCODING))
                        elif room_name not in rooms: # Sala existe no DB mas não está ativa (ninguém nela)
                            rooms[room_name] = set() # Ativa a sala
                            rooms[room_name].add(sock)
                            user_rooms[sock] = room_name
                            broadcast(f"{clients[sock]} entrou na sala.", room_name, sock)
                            sock.send(f"Você entrou na sala '{room_name}'.\n".encode(ENCODING))
                        else:
                            rooms[room_name].add(sock)
                            user_rooms[sock] = room_name
                            broadcast(f"{clients[sock]} entrou na sala.", room_name, sock)
                            sock.send(f"Você entrou na sala '{room_name}'.\n".encode(ENCODING))

            elif data.startswith("/leave"):
                with lock:
                    room = user_rooms.pop(sock, None)
                    if room and sock in rooms[room]:
                        rooms[room].remove(sock)
                        broadcast(f"{clients[sock]} saiu da sala.", room, sock)
                sock.send("Você saiu da sala.\n".encode(ENCODING))

            else:
                room = user_rooms.get(sock)
                if room:
                    msg = f"[{clients[sock]}@{room}]: {data}"
                    broadcast(msg, room, sock)
                else:
                    sock.send("Entre em uma sala com /join para enviar mensagens.\n".encode(ENCODING))

    except Exception as e:
        pass
    finally:
        with lock:
            user = clients.pop(sock, None)
            room = user_rooms.pop(sock, None)
            if room:
                rooms[room].discard(sock)
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
