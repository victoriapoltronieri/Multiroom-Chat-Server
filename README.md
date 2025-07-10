# Multiroom-Chat-Server

## Descrição
- Servidor e cliente de chat em tempo real escritos em Python 3.12 com asyncio e WebSocket.
- Suporta múltiplas salas, autenticação de usuários, mensagens cifradas ponto‑a‑ponto via TLS e salas privadas protegidas por senha.
- Projeto proposto na disciplina de Redes de Computadores para demonstrar conhecimento de protocolos, concorrência assíncrona, segurança e testes de carga.

## Tecnologias Utilizadas
- **Python 3.12** – linguagem principal; já traz os módulos‐padrão usados (socket, threading, ssl, sys).

- **TCP Sockets (socket)** – comunicação em tempo real entre cliente e servidor.

- **Threading (threading)** – permite lidar com múltiplos clientes de forma concorrente.

- **TLS/SSL (ssl, stdlib)** – cifra o canal TCP (certificado autoassinado em desenvolvimento).

- **Interface de Usuário** – cliente gráfico opcional construído com PyQt5; versão em terminal continua funcionando sem essa dependência.

## Bibliotecas/Frameworks utilizados
- **PyQt5** – constrói a GUI (widgets, layouts, eventos).

- **Módulos da biblioteca padrão**

    - **socket** – criação de servidor e cliente TCP.

	- **threading** – execução paralela de conexões.

	- **ssl** – encapsula o socket em TLS (se ativado).
    
	- **sys** – manipula argumentos e encerramento limpo da aplicação.

__(Não há dependências externas além do PyQt5. Todo o resto é 100 % stdlib.)__

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
~$ poetry run python3 chat_server_multisalas.py
```

### 6) Em outro terminal, execute este cliente:

```
~$poetry run python3 chat_client_terminal.py
~$poetry run python3 chat_client_terminal.py
```

### 7) O que é esperado de ver:
### 7) O que é esperado de ver:

Você verá:
```
Bem-vindo(a)!
Use /create, /join, /list, /leave para entrar numa sala de chat.
```

OBS: Mensagens só serão enviadas se você estiver em uma sala.

OBS: Mensagens só serão enviadas se você estiver em uma sala.