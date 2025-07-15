import socket
import threading
import json
import hashlib
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
rooms = {}             # nome -> set de socket
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

def hash_password(password):
    return hashlib.sha256(password.encode(ENCODING)).hexdigest()

def broadcast(msg, room, sender=None):
    with lock:
        for client in rooms.get(room, set()):
            if client != sender:
                try:
                    client.send(msg.encode(ENCODING))
                except:
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
                    password_h = hash_password(pwd)
                    if database.add_user(user, password_h):
                        sock.send("Usuário registrado com sucesso.\n".encode(ENCODING))
                    else:
                        sock.send("Usuário já existe.\n".encode(ENCODING))

                elif data.startswith("/login"):
                    _, user, pwd = data.strip().split()
                    if user in users and users[user] == hash_password(pwd):
                        authenticated.add(sock)
                        clients[sock] = user
                        sock.send("Login bem-sucedido.\n".encode(ENCODING))
                    else:
                        sock.send("Login inválido.\n".encode(ENCODING))
                else:
                    sock.send("Comando inválido. Use /register ou /login.\n".encode(ENCODING))
                continue

            if data.startswith("/list"):
                room_list = ", ".join(rooms.keys())
                sock.send(f"Rooms: {room_list}\n".encode(ENCODING))

            elif data.startswith("/create"):
                _, room = data.strip().split()
                with lock:
                    rooms.setdefault(room, set())
                sock.send(f"Sala '{room}' criada.\n".encode(ENCODING))

            elif data.startswith("/join"):
                _, room = data.strip().split()
                with lock:
                    if room not in rooms:
                        sock.send("Sala inexistente.\n".encode(ENCODING))
                    else:
                        rooms[room].add(sock)
                        user_rooms[sock] = room
                        broadcast(f"🔔 {clients[sock]} entrou na sala.", room, sock)
                        sock.send(f"Você entrou na sala '{room}'.\n".encode(ENCODING))

            elif data.startswith("/leave"):
                with lock:
                    room = user_rooms.pop(sock, None)
                    if room and sock in rooms[room]:
                        rooms[room].remove(sock)
                        broadcast(f"🔕 {clients[sock]} saiu da sala.", room, sock)
                sock.send("Você saiu da sala.\n".encode(ENCODING))

            else:
                room = user_rooms.get(sock)
                if room:
                    msg = f"[{clients[sock]}@{room}]: {data}"
                    broadcast(msg, room, sock)
                else:
                    sock.send("Entre em uma sala com /join para enviar mensagens.\n".encode(ENCODING))

    except:
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
print(f"Servidor rodando em {HOST}:{PORT}")

try:
    while True:
        client_socket, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()
except KeyboardInterrupt:
    print("Encerrando o servidor...")
finally:
    server_socket.close()
