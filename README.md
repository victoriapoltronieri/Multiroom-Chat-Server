# Multiroom-Chat-Server
## Como usar:
### 1) Faça um clone do repositório do GitHub.

### 2) Instale o poetry no seu computador:

```
~$ pip install poetry
```

### 3) Inicialize o projeto poetry:

```
~$ poetry install
```

### 4) Entre no terminal do poetry:

```
~$ poetry shell
```

### 5) Execute primeiro o servidor usando o poetry:

```
~$ poetry run python3 chat_server_multisalas.py
```
### 6) Em outro terminal, execute este cliente:

```
~$poetry run python3 chat_client_terminal.py
```

### 7) O que é esperado de ver:

Você verá:
```
Bem-vindo(a)!
Use /create, /join, /list, /leave para entrar numa sala de chat.
```

OBS: Mensagens só serão enviadas se você estiver em uma sala.