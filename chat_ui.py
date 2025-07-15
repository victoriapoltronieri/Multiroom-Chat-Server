from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QLineEdit, QListWidget, QTextEdit, QMessageBox, QInputDialog, QSizePolicy)
from PyQt5.QtCore import Qt
import socket
import threading
import sys

HOST = '127.0.0.1'
PORT = 12345
ENCODING = 'utf-8'

class ChatClient(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat App")
        self.setMinimumSize(700, 500)

        self.sock = None
        self.username = ""

        self.init_login_ui()

    def init_login_ui(self):
        self.login_widget = QWidget()
        layout = QVBoxLayout(self.login_widget)
        layout.setContentsMargins(50, 50, 50, 50)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Usuário")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Senha")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.register_button = QPushButton("Registrar")
        self.register_button.clicked.connect(self.register_user)
        layout.addWidget(self.register_button)

        self.connect_button = QPushButton("Entrar no chat")
        self.connect_button.clicked.connect(self.connect_to_server)
        layout.addWidget(self.connect_button)

        self.setLayout(layout)

    def send_auth_command(self, command):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, PORT))
            self.sock.recv(1024)
            self.sock.send(command.encode(ENCODING))
            response = self.sock.recv(1024).decode(ENCODING)
            return response
        except Exception as e:
            return f"Erro: {e}"

    def register_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Atenção", "Preencha nome e senha.")
            return
        response = self.send_auth_command(f"/register {username} {password}")
        QMessageBox.information(self, "Registro", response)
        self.sock.close()

    def connect_to_server(self):
        self.username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not self.username or not password:
            QMessageBox.warning(self, "Atenção", "Preencha nome e senha.")
            return

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, PORT))
            self.sock.recv(1024)
            self.sock.send(f"/login {self.username} {password}".encode(ENCODING))
            response = self.sock.recv(1024).decode(ENCODING)

            if response.startswith("Login bem-sucedido"):
                self.build_main_interface()
                threading.Thread(target=self.receive_messages, daemon=True).start()
            else:
                QMessageBox.warning(self, "Erro", response)
                self.sock.close()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao conectar: {e}")

    def build_main_interface(self):
        for i in reversed(range(self.layout().count())):
            widget = self.layout().itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        main_layout = QHBoxLayout()

        # Painel lateral esquerdo (salas)
        left_panel = QVBoxLayout()
        self.room_list = QListWidget()
        self.room_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        left_panel.addWidget(QLabel("Salas Disponíveis"))
        left_panel.addWidget(self.room_list)

        self.refresh_btn = QPushButton("Atualizar Lista")
        self.refresh_btn.clicked.connect(self.list_rooms)
        left_panel.addWidget(self.refresh_btn)

        self.join_btn = QPushButton("Entrar na Sala")
        self.join_btn.clicked.connect(self.join_room)
        left_panel.addWidget(self.join_btn)

        self.create_btn = QPushButton("Criar Sala")
        self.create_btn.clicked.connect(self.create_room)
        left_panel.addWidget(self.create_btn)

        self.leave_btn = QPushButton("Sair da Sala")
        self.leave_btn.clicked.connect(self.leave_room)
        left_panel.addWidget(self.leave_btn)

        main_layout.addLayout(left_panel, 1)

        # Painel principal (chat)
        right_panel = QVBoxLayout()
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        right_panel.addWidget(QLabel("Chat"))
        right_panel.addWidget(self.chat_display, 5)

        input_row = QHBoxLayout()
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Digite uma mensagem...")
        self.msg_input.returnPressed.connect(self.send_message)
        input_row.addWidget(self.msg_input)

        self.send_btn = QPushButton("Enviar")
        self.send_btn.clicked.connect(self.send_message)
        input_row.addWidget(self.send_btn)

        right_panel.addLayout(input_row)

        main_layout.addLayout(right_panel, 3)

        for i in reversed(range(self.layout().count())):
            item = self.layout().itemAt(i)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
            self.layout().removeItem(item)


        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.layout().addWidget(central_widget)


    def list_rooms(self):
        self.sock.send("/list".encode(ENCODING))

    def join_room(self):
        selected = self.room_list.currentItem()
        if selected:
            room = selected.text()
            self.sock.send(f"/join {room}".encode(ENCODING))

    def create_room(self):
        room, ok = QInputDialog.getText(self, "Criar Sala", "Nome da sala:")
        if ok and room:
            self.sock.send(f"/create {room}".encode(ENCODING))

    def leave_room(self):
        self.sock.send("/leave".encode(ENCODING))

    def send_message(self):
        msg = self.msg_input.text().strip()
        if msg:
            self.sock.send(msg.encode(ENCODING))
            self.msg_input.clear()

    def receive_messages(self):
        while True:
            try:
                msg = self.sock.recv(1024).decode(ENCODING)
                if msg.startswith("Rooms:"):
                    self.room_list.clear()
                    rooms = msg[7:].split(',')
                    for room in rooms:
                        room = room.strip()
                        if room:
                            self.room_list.addItem(room)
                else:
                    self.chat_display.append(msg)
            except:
                break

def main():
    app = QApplication(sys.argv)
    client = ChatClient()
    client.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
