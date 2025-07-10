import socket
import select
import threading

# Configuração do servidor
HOST = '127.0.0.1'
PORT = 12345
ENCODING = 'utf-8'

# Dados dos chats
clients = {}  # socket -> username
rooms = {}    # room_name -> uma lista de sockets
user_rooms = {}  # socket -> room_name

lock = threading.Lock()

# Funções auxiliares
def broadcast(message, room, sender_socket):
    with lock:
        for client in rooms.get(room, set()):
            if client != sender_socket:
                try:
                    client.send(message.encode(ENCODING))
                except:
                    pass

def handle_client(client_socket):
    try:
        client_socket.send("Digite seu nome: ".encode(ENCODING))
        username = client_socket.recv(1024).decode(ENCODING).strip()
        clients[client_socket] = username

        client_socket.send("Bem-vindo(a)!\nUse /create, /join, /list, /leave para entrar numa sala de chat.\n".encode(ENCODING))

        while True:
            data = client_socket.recv(1024).decode(ENCODING)
            if not data:
                break

            if data.startswith("/"):
                handle_command(client_socket, data.strip())
            else:
                room = user_rooms.get(client_socket)
                if room:
                    msg = f"[{clients[client_socket]}@{room}]: {data}"
                    broadcast(msg, room, client_socket)
                else:
                    client_socket.send("Se junte a uma sala de bate-papo para trocar mensagens.\n".encode(ENCODING))

    except:
        pass
    finally:
        disconnect_client(client_socket)

def handle_command(sock, command):
    args = command.split()
    if not args:
        return
    
    cmd = args[0]

    if cmd == "/list":
        room_list = ", ".join(rooms.keys())
        sock.send(f"Salas: {room_list}\n".encode(ENCODING))

    elif cmd == "/create" and len(args) > 1:
        room = args[1]
        with lock:
            rooms.setdefault(room, set())
        sock.send(f"Sala '{room}' criada.\n".encode(ENCODING))

    elif cmd == "/join" and len(args) > 1:
        room = args[1]
        with lock:
            if room not in rooms:
                sock.send("Ops! Essa sala não existe.\n".encode(ENCODING))
                return
            rooms[room].add(sock)
            user_rooms[sock] = room
        sock.send(f"Você entrou em'{room}'.\n".encode(ENCODING))

    elif cmd == "/leave":
        with lock:
            room = user_rooms.pop(sock, None)
            if room and sock in rooms[room]:
                rooms[room].remove(sock)
        sock.send("Você saiu da sala.\n".encode(ENCODING))

    else:
        sock.send("Comando desconhecido ou argumentos inválidos.\n".encode(ENCODING))

def disconnect_client(sock):
    with lock:
        if sock in clients:
            username = clients.pop(sock)
            room = user_rooms.pop(sock, None)
            if room:
                rooms[room].discard(sock)
        sock.close()

# Serviço principal
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()
print(f"Servidor rodando na porta: {HOST}:{PORT}")

try:
    while True:
        client_socket, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()
except KeyboardInterrupt:
    print("\nServidor desligando.")
finally:
    server_socket.close()

def main():
    app = QApplication(sys.argv)
    client = ChatClient()
    client.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()