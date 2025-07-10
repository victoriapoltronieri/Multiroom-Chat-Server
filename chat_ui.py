from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QLineEdit, QListWidget, QTextEdit, QMessageBox, QInputDialog)
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
        self.setGeometry(100, 100, 600, 400)

        self.sock = None
        self.username = ""

        self.init_login_ui()

    def init_login_ui(self):
        self.login_layout = QVBoxLayout()

        self.label = QLabel("Nome de usuário:")
        self.login_layout.addWidget(self.label)

        self.username_input = QLineEdit()
        self.login_layout.addWidget(self.username_input)

        self.connect_button = QPushButton("Entrar no chat")
        self.connect_button.clicked.connect(self.connect_to_server)
        self.login_layout.addWidget(self.connect_button)

        self.setLayout(self.login_layout)

    def connect_to_server(self):
        self.username = self.username_input.text().strip()
        if not self.username:
            QMessageBox.warning(self, "Atenção", "Digite um nome de usuário.")
            return

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, PORT))
            self.sock.recv(1024)
            self.sock.send(self.username.encode(ENCODING))

            self.build_main_interface()
            threading.Thread(target=self.receive_messages, daemon=True).start()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao conectar: {e}")

    def build_main_interface(self):
        for i in reversed(range(self.layout().count())):
            self.layout().itemAt(i).widget().setParent(None)

        main_layout = QHBoxLayout()

        left_panel = QVBoxLayout()
        self.room_list = QListWidget()
        left_panel.addWidget(QLabel("Salas Disponíveis"))
        left_panel.addWidget(self.room_list)

        self.refresh_btn = QPushButton("Atualizar Lista")
        self.refresh_btn.clicked.connect(self.list_rooms)
        left_panel.addWidget(self.refresh_btn)

        self.join_btn = QPushButton("Entrar na Sala")

def main():
    app = QApplication(sys.argv)
    client = ChatClient()
    client.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
