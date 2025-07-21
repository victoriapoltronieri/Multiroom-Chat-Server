import sqlite3
import hashlib

DB_NAME = "chat.db"
ENCODING = "utf-8"


def hash_password(password):
    """Gera o hash de uma senha usando SHA256."""
    return hashlib.sha256(password.encode(ENCODING)).hexdigest()


def init_db():
    """
    Inicializa o banco de dados e cria as tabelas de usuários e salas se não existirem.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Tabela de usuários
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """
    )

    # Tabela de salas
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            is_private BOOLEAN NOT NULL DEFAULT FALSE,
            password_hash TEXT
        )
    """
    )

    conn.commit()
    conn.close()


def add_user(username, password):
    """
    Adiciona um novo usuário ao banco de dados.
    Retorna True se o usuário foi adicionado com sucesso, False caso contrário.
    """
    password_h = hash_password(password)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_h),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_user_hash(username):
    """
    Busca o hash da senha de um usuário no banco de dados.
    Retorna o hash se o usuário for encontrado, None caso contrário.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def check_user_credentials(username, password):
    """Verifica as credenciais de um usuário comparando a senha fornecida com o hash armazenado."""
    stored_hash = get_user_hash(username)
    if not stored_hash:
        return False
    return stored_hash == hash_password(password)


def create_room(name, password=None):
    """
    Cria uma nova sala no banco de dados.
    Se uma senha for fornecida, a sala é marcada como privada.
    Retorna True se a sala foi criada com sucesso, False caso contrário.
    """
    is_private = password is not None
    password_h = hash_password(password) if is_private else None

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO rooms (name, is_private, password_hash) VALUES (?, ?, ?)",
            (name, is_private, password_h),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_rooms():
    """
    Retorna uma lista de tuplas (nome_da_sala, é_privada).
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, is_private FROM rooms ORDER BY name")
    rooms = cursor.fetchall()
    conn.close()
    return rooms


def get_room_details(name):
    """

    Busca os detalhes de uma sala (nome, é_privada, hash_da_senha).
    Retorna uma tupla com os detalhes se a sala for encontrada, None caso contrário.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, is_private, password_hash FROM rooms WHERE name = ?", (name,)
    )
    details = cursor.fetchone()
    conn.close()
    return details
