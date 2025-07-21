# Servidor de Chat Multi-Sala em Python

## Descrição

Este projeto implementa um sistema de chat cliente-servidor robusto e concorrente, desenvolvido em Python. Ele permite que múltiplos usuários se registrem, façam login e interajam em tempo real dentro de diferentes salas de chat. O sistema utiliza sockets TCP para comunicação, `threading` para gerenciar múltiplos clientes simultaneamente e um banco de dados SQLite para persistir informações de usuários e salas.

O foco do projeto é demonstrar conceitos fundamentais de redes de computadores, como a arquitetura cliente-servidor, concorrência, persistência de dados e a criação de um protocolo de aplicação simples baseado em texto.

---

## Tecnologias Utilizadas

- **Linguagem Principal:** **Python 3.8+**
- **Comunicação de Rede:** Módulo `socket` da biblioteca padrão para comunicação TCP de baixo nível.
- **Concorrência:** Módulo `threading` da biblioteca padrão para lidar com clientes de forma concorrente.
- **Banco de Dados:** Módulo `sqlite3` da biblioteca padrão para criar e gerenciar o banco de dados local.
- **Segurança:** Módulo `hashlib` da biblioteca padrão para gerar hashes SHA256 das senhas.
- **Estrutura do Projeto:** O projeto é gerenciado com `poetry` para um controle de dependências limpo, embora não utilize bibliotecas externas além da padrão do Python.

---

## Como Executar

### Requisitos

- **Python 3.8 ou superior.**
- **Poetry** (gerenciador de dependências). Se não o tiver, instale com `pip install poetry`.

### Instruções de Execução

O projeto foi projetado para ser executado em múltiplos terminais usando um lançador central.

1.  **Clone o Repositório:**
    ```bash
    git clone <URL_DO_SEU_REPOSITORIO>
    cd <NOME_DO_DIRETORIO>
    ```

2.  **Instale as Dependências (via Poetry):**
    ```bash
    poetry install
    ```

3.  **Inicie o Servidor:**
    - Abra um terminal e digite:

    ```bash
    poetry run python3 main.py
    ```
    - No menu que aparecer, digite `1` e pressione Enter. O terminal será então dedicado a rodar o servidor e exibir seus logs.

4.  **Inicie um Cliente:**
    - Abra um **novo** terminal e digite:

    ```bash
    poetry run python3 main.py
    ```
    - No menu, digite `2` e pressione Enter.
    - Você será solicitado a fornecer a porta do servidor (use a porta padrão `12345` para testes locais, ou a porta do `ngrok` se estiver usando).
    - O terminal será então dedicado ao cliente do chat.

---

## Como Testar

Após iniciar o servidor e pelo menos dois clientes seguindo as instruções acima, siga este fluxo para testar todas as funcionalidades principais:

1.  **Registro de Usuário:**
    - Em um dos clientes, no menu inicial, escolha a opção `1` para registrar.
    - Quando solicitado, digite um nome de usuário e senha separados por espaço. Ex: `usuario1 123`

2.  **Login:**
    - Após o registro, o menu inicial será exibido novamente. Escolha a opção `2` para fazer login com as credenciais que você acabou de criar. Ex: `usuario1 123`

3.  **Criação de Sala:**
    - No menu principal, escolha a opção `2` para criar uma sala.
    - Crie uma sala pública. Ex: `sala_publica n`
    - Crie uma sala privada. Ex: `sala_privada s senhasecreta`

4.  **Listagem de Salas:**
    - No menu principal, escolha a opção `1` para listar as salas. Verifique se as duas salas que você criou aparecem na lista.

5.  **Entrar na Sala e Conversar:**
    - Escolha a opção `3` para entrar em uma sala. Digite o nome da sala pública: `sala_publica`
    - Você receberá uma confirmação e entrará no modo de chat. Envie algumas mensagens.

6.  **Teste com o Segundo Cliente:**
    - No segundo terminal de cliente, registre e faça login com um usuário diferente (ex: `usuario2 456`).
    - Peça para o segundo cliente entrar na mesma sala (`sala_publica`).
    - Verifique se o segundo cliente recebe a notificação de que o `usuario2` entrou.
    - Envie uma mensagem do `usuario2`. Verifique se o `usuario1` a recebe, e vice-versa.

7.  **Teste dos Comandos do Chat:**
    - Em um dos clientes, digite `/menu`. Você será levado de volta ao menu principal.
    - Observe que o menu agora tem as opções `5. Sair da Sala Atual` e `6. Voltar para o Chat`.
    - Escolha a opção `6`. Você deve retornar à conversa da sala.
    - Agora, digite `/leave`. Você sairá da sala e voltará ao menu principal, que não terá mais as opções 5 e 6.

---

## Funcionalidades Implementadas

- **Autenticação de Usuários:** Registro e login com senhas armazenadas de forma segura (hash SHA256).
- **Gerenciamento de Salas:** Criação de salas públicas e privadas (protegidas por senha), com listagem das salas disponíveis.
- **Comunicação em Tempo Real:** Mensagens instantâneas dentro das salas e notificações de entrada/saída de usuários.
- **Interface de Linha de Comando (CLI):** Menu interativo e contextual para uma navegação clara e intuitiva.
- **Persistência de Dados:** Uso de um banco de dados SQLite (`chat.db`) para armazenar usuários e salas.
- **Concorrência:** Servidor multithread capaz de gerenciar múltiplos clientes simultaneamente.

---

## Possíveis Melhorias Futuras

- **Canais Cifrados (TLS/SSL):** Envolver os sockets com o módulo `ssl` para cifrar toda a comunicação.
- **Mensagens Privadas:** Implementar um comando `/whisper <usuario> <mensagem>` para mensagens diretas.
- **Interface Gráfica (GUI):** Desenvolver um cliente com `PyQt` ou `Tkinter` para uma experiência de usuário mais rica.
- **Histórico de Mensagens:** Salvar e carregar o histórico de mensagens das salas no banco de dados.
- **Testes Automatizados:** Criar testes unitários e de integração para validar a lógica do sistema.