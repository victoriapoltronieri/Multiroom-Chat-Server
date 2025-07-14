# Multiroom-Chat-Server
## Descrição
- Servidor e cliente de chat em tempo real escritos em Python 3.12 com asyncio e WebSocket.
- Suporta múltiplas salas, autenticação de usuários, mensagens cifradas ponto‑a‑ponto via TLS e salas privadas protegidas por senha.
- Projeto proposto na disciplina de Redes de Computadores para demonstrar conhecimento de protocolos, concorrência assíncrona, segurança e testes de carga.

## Tecnologias Utilizadas
- **Python 3.12**: Linguagem de programação principal do projeto. Utiliza recursos modernos como programação assíncrona (asyncio) e criptografia com a biblioteca padrão (ssl).

- **WebSocket**: Tecnologia de comunicação em tempo real full-duplex sobre TCP. Utilizado para envio/recebimento de mensagens entre cliente e servidor de forma contínua e eficiente.

- **Terminal / Interface Gráfica**: A aplicação é acessível via terminal por padrão e por um cliente com interface gráfica utilizando PyQt.

- **TLS/SSL** (segurança): Comunicação protegida com criptografia ponto a ponto (certificado próprio). Implementado com a biblioteca ssl da própria linguagem Python.

## Bibliotecas/Frameworks utilizados
### **Obrigatórias (base do projeto)**

- **websockets**: Biblioteca para criar servidores e clientes WebSocket de forma assíncrona com suporte a TLS.

- **bcrypt**: Utilizado para armazenar senhas de forma segura com hash e sal. Protege contra ataques de força bruta.

- **pytest**: Framework de testes automatizados para garantir a estabilidade e o comportamento esperado do sistema.

- **pytest-asyncio**: Permite escrever testes para funções assíncronas com `async def` e `await`.


### **Auxiliares (organização e desenvolvimento)**

- **Poetry**: Gerenciador de dependências e ambiente virtual. Facilita a instalação e portabilidade do projeto em qualquer máquina.

- **black** *(opcional)*: Formatador automático de código, usado para manter um estilo consistente.


### **Interface gráfica**

- **PyQt5 ou PyQt6**: Biblioteca para construção de interfaces gráficas em Python.Será usada para implementar um cliente com interface simples, modularizada e **desacoplada do core do projeto** (servidor e cliente CLI continuam funcionando normalmente se a interface for desativada).

## Estrutura do Projeto
Estrutura de pastas enxuta – cada item com seu papel em tópicos (sem tabelas)
- chat/  (código-fonte do projeto)
    - server.py – ponto de entrada do servidor (python -m chat.server).
        - Cria o WebSocket TLS, aceita conexões, roteia mensagens para salas.
	- client.py – cliente de terminal (python -m chat.client).
	    - Lê comandos do usuário, mantém a conexão WebSocket, mostra mensagens.
	- rooms.py – camada de domínio “Salas”.
	    - Mantém um dicionário {nome_da_sala: set(websocket)}.
	    - Exponde funções list_rooms(), create_room(), join_room(), leave_room().
	- auth.py – registro e login.
	    - Usa bcrypt para hash; guarda usuários em memória ou arquivo JSON.
	- models.py – dataclasses / pydantic para padronizar payloads (LoginRequest, ChatMessage etc.).

- tests/  (código de teste)

## Como Executar
### Requisitos
Lista de dependências necessárias.

### Instruções de Execução

### Como Testar
Instruções para testar a aplicação.

## Funcionalidades Implementadas
Lista das funcionalidades desenvolvidas.

## Possíveis Melhorias Futuras
Sugestões de melhorias para versões futuras.