# Servidor de Chat Multi-Sala em Python

## Descrição

Este projeto implementa um sistema de chat cliente-servidor robusto e concorrente, desenvolvido em Python. Ele permite que múltiplos usuários se registrem, façam login e interajam em tempo real dentro de diferentes salas de chat. O sistema utiliza sockets TCP para comunicação, `threading` para gerenciar múltiplos clientes simultaneamente e um banco de dados SQLite para persistir informações de usuários e salas.

O foco do projeto é demonstrar conceitos fundamentais de redes de computadores, como a arquitetura cliente-servidor, concorrência, persistência de dados e a criação de um protocolo de aplicação simples baseado em texto.

---

## Tecnologias Utilizadas

- **Linguagem Principal:** **Python 3.8+**
- **Comunicação de Rede:** Módulo `socket` da biblioteca padrão para comunicação TCP de baixo nível.
- **Segurança de Comunicação:** Módulo `ssl` da biblioteca padrão para criptografia TLS/SSL das conexões.
- **Concorrência:** Módulo `threading` da biblioteca padrão para lidar com clientes de forma concorrente.
- **Banco de Dados:** Módulo `sqlite3` da biblioteca padrão para criar e gerenciar o banco de dados local.
- **Segurança de Dados:** Módulo `hashlib` da biblioteca padrão para gerar hashes SHA256 das senhas.
- **Estrutura do Projeto:** O projeto é gerenciado com `poetry` para um controle de dependências limpo, embora não utilize bibliotecas externas além da padrão do Python.
- **Túnel de Rede Externo:** ngrok para expor o servidor local à internet de forma segura e acessível remotamente (via túnel TCP), permitindo que usuários em diferentes redes possam se conectar ao servidor.
---

## Como Executar

### Requisitos

- **Python 3.8 ou superior.**
- **Poetry** (gerenciador de dependências). Se não o tiver, instale com `pip install poetry`.
- **Certificados SSL:** Os arquivos `cert.pem` e `key.pem` devem estar presentes no diretório raiz do projeto para comunicação SSL.

### Instruções de Execução

O projeto foi projetado para ser executado em múltiplos terminais usando um lançador central. Ele pode ser executado localmente ou disponibilizado para acesso remoto através do ngrok.

1.  **Clone o Repositório:**
    ```bash
    git clone <URL_DO_SEU_REPOSITORIO>
    cd <NOME_DO_DIRETORIO>
    ```

2.  **Instale as Dependências (via Poetry):**
    ```bash
    poetry install
    ```

3. **Entre no ambiente do poetry:**
	```bash
	poetry shell
	```

4. **Configure os Certificados SSL:**
   - Os arquivos `cert.pem` e `key.pem` já estão incluídos no projeto para desenvolvimento
   - Para produção, gere novos certificados SSL seguindo as instruções na seção "Configuração SSL"

5.  **Inicie o Servidor:**
    - Abra um terminal e digite:

    ```bash
    poetry run python3 main.py
    ```
    - No menu que aparecer, digite `1` e pressione Enter. O terminal será então dedicado a rodar o servidor e exibir seus logs.
    - O servidor iniciará automaticamente com SSL habilitado na porta 12345.

6.  **Inicie um Cliente:**
    - Abra um **novo** terminal e digite:

    ```bash
    poetry run python3 main.py
    ```
    - No menu, digite `2` e pressione Enter.
    - Você será solicitado a fornecer a porta do servidor:
      - Para testes locais, use a porta padrão `12345`
      - Para conexões remotas via ngrok, use a porta fornecida pelo túnel ngrok (explicado na seção "Conexão Remota com ngrok")
    - O cliente estabelecerá automaticamente uma conexão SSL segura com o servidor.
    - O terminal será então dedicado ao cliente do chat.

---

## Configuração SSL

### Visão Geral da Segurança

O sistema implementa criptografia SSL/TLS para proteger todas as comunicações entre cliente e servidor. Isso garante que:

- **Confidencialidade:** Todas as mensagens são criptografadas durante a transmissão
- **Integridade:** Os dados não podem ser modificados sem detecção
- **Autenticação:** O servidor é autenticado através de certificados digitais

### Certificados SSL

O projeto inclui certificados SSL auto-assinados para desenvolvimento:

- **`cert.pem`:** Certificado público do servidor
- **`key.pem`:** Chave privada do servidor

⚠️ **Importante:** Os certificados incluídos são apenas para desenvolvimento. Para produção, você deve gerar novos certificados.

### Gerando Novos Certificados (Opcional)

Para gerar novos certificados SSL auto-assinados:

```bash
# Gerar chave privada
openssl genrsa -out key.pem 2048

# Gerar certificado auto-assinado válido por 365 dias
openssl req -new -x509 -key key.pem -out cert.pem -days 365
```

Durante a geração, você será solicitado a fornecer informações como país, estado, cidade, etc. Para desenvolvimento, você pode usar valores fictícios.

### Como Funciona o SSL no Sistema

#### Servidor (`chat_multiroom_server.py`)

1. **Carregamento de Certificados:**
   ```python
   context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
   context.load_cert_chain('cert.pem', 'key.pem')
   ```

2. **Envolvimento SSL:**
   - Cada conexão de cliente é envolvida com SSL após a aceitação
   - O handshake SSL é realizado automaticamente

3. **Tratamento de Erros:**
   - Falhas no handshake SSL são capturadas e logadas
   - Conexões sem SSL são rejeitadas

#### Cliente (`chat_client_terminal.py`)

1. **Contexto SSL:**
   ```python
   context = ssl.create_default_context()
   context.check_hostname = False  # Para certificados auto-assinados
   context.verify_mode = ssl.CERT_NONE
   ```

2. **Conexão Segura:**
   - Conecta primeiro com socket normal
   - Envolve a conexão com SSL
   - Realiza handshake SSL automaticamente

---

## Conexão Remota com ngrok

O sistema foi projetado para permitir conexões remotas através do ngrok, possibilitando que usuários em diferentes redes possam se conectar ao mesmo servidor de chat sem a necessidade de configurar redirecionamento de portas em roteadores ou lidar com firewalls.

### O que é o ngrok?

O ngrok é uma ferramenta que cria túneis seguros para expor serviços locais à internet. No contexto deste projeto, ele permite que o servidor de chat, rodando em sua máquina local, seja acessível por qualquer pessoa na internet.

### Como Configurar o ngrok

1. **Instale o ngrok:**
   - Baixe em [ngrok.com](https://ngrok.com/download)
   - Siga as instruções de instalação para seu sistema operacional

2. **Inicie o túnel TCP:**
   ```bash
   ngrok tcp 12345
   ```
   Onde `12345` é a porta em que seu servidor de chat está rodando localmente.

3. **Obtenha as informações do túnel:**
   - O ngrok fornecerá uma saída semelhante a esta:
   ```
   Forwarding tcp://0.tcp.ngrok.io:12345 -> localhost:12345
   ```
   - O endereço `0.tcp.ngrok.io` e a porta (neste exemplo, `12345`) são o que os clientes remotos usarão para se conectar.

### Conectando Clientes Remotos

1. **No código do cliente:**
   - O arquivo `chat_client_terminal.py` já está configurado para usar o endereço ngrok:
   ```python
   HOST = "0.tcp.sa.ngrok.io"  # Hostname do túnel ngrok
   PORT = int(sys.argv[1])     # Porta dinâmica fornecida pelo ngrok
   ```

2. **Ao iniciar o cliente:**
   - Quando solicitado a fornecer a porta do servidor, insira a porta fornecida pelo ngrok.
   - Esta porta muda a cada vez que você inicia um novo túnel ngrok.

3. **Compartilhando acesso:**
   - Compartilhe a porta do ngrok com outros usuários que desejam se conectar ao seu servidor.
   - Eles precisarão apenas executar o cliente e inserir a porta correta quando solicitado.

### Vantagens do ngrok

- **Sem configuração de rede:** Não é necessário configurar redirecionamento de portas no roteador.
- **Bypass de firewalls:** Funciona mesmo em redes corporativas ou educacionais restritivas.
- **Segurança adicional:** O túnel ngrok é criptografado, adicionando uma camada extra de segurança além do SSL.
- **Acesso global:** Qualquer pessoa com internet pode se conectar ao seu servidor de chat.

### Solução de Problemas com ngrok

**Erro: "Não foi possível conectar ao servidor"**
- Verifique se o túnel ngrok está ativo e funcionando
- Confirme se está usando a porta correta fornecida pelo ngrok
- Certifique-se de que o servidor está rodando antes de iniciar o túnel ngrok

**Erro: "Túnel expirado"**
- Os túneis gratuitos do ngrok expiram após algumas horas
- Reinicie o túnel ngrok para obter uma nova porta e endereço

**Erro: "Porta já em uso"**
- Certifique-se de que não há outro serviço usando a porta 12345
- Você pode alterar a porta do servidor no código e iniciar o ngrok com a nova porta

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

8.  **Teste da Funcionalidade SSL:**
    - Observe nos logs do servidor as mensagens de SSL: `[INFO] Certificados SSL carregados com sucesso.`
    - Observe nos logs do cliente as mensagens: `[INFO] Handshake SSL bem-sucedido com o servidor`
    - Todas as comunicações entre cliente e servidor estão agora criptografadas
    - Teste desconectar e reconectar clientes para verificar se o handshake SSL funciona consistentemente
    
9.  **Teste de Conexão Remota com ngrok (Opcional):**
    - Inicie o servidor normalmente
    - Em outro terminal, inicie o túnel ngrok: `ngrok tcp 12345`
    - Observe a porta fornecida pelo ngrok (ex: `tcp://0.tcp.ngrok.io:12345`)
    - Inicie um cliente em outra máquina ou rede
    - Quando solicitado, insira a porta fornecida pelo ngrok
    - Verifique se a conexão é estabelecida com sucesso
    - Teste o registro, login e troca de mensagens através da conexão remota

---

## Funcionalidades Implementadas

- **Criptografia SSL/TLS:** Todas as comunicações entre cliente e servidor são criptografadas usando SSL, garantindo confidencialidade e integridade dos dados.
- **Autenticação de Usuários:** Registro e login com senhas armazenadas de forma segura (hash SHA256).
- **Gerenciamento de Salas:** Criação de salas públicas e privadas (protegidas por senha), com listagem das salas disponíveis.
- **Comunicação em Tempo Real:** Mensagens instantâneas dentro das salas e notificações de entrada/saída de usuários.
- **Interface de Linha de Comando (CLI):** Menu interativo e contextual para uma navegação clara e intuitiva.
- **Persistência de Dados:** Uso de um banco de dados SQLite (`chat.db`) para armazenar usuários e salas.
- **Concorrência:** Servidor multithread capaz de gerenciar múltiplos clientes simultaneamente.
- **Interconectividade:** Com o servidor hospedado no ngrok é possível que várias pessoas conectadas a redes distintas se conectem na sala de chat apenas com o número da porta fornecida pelo túnel ngrok, sem necessidade de configuração de roteadores ou firewalls.
- **Codificação das mensagens:** Com `.ENCODING` as mensagens enviadas são sempre codificadas antes do seu envio.
- **Tratamento de Erros SSL:** Captura e tratamento adequado de erros relacionados a SSL tanto no servidor quanto no cliente.
- **Certificados Auto-assinados:** Suporte para certificados SSL auto-assinados para desenvolvimento e testes.
---

## Possíveis Melhorias Futuras

- **Mensagens Privadas:** – Implementar um comando para possibilitar mensagens diretas.
- **Histórico de Mensagens:** – Salvar e carregar o histórico de mensagens das salas no banco de dados.
- **Interface de Usuário** – cliente gráfico construído com PyQt ou Tkinter.
É possível criar uma interface gráfica para o usuário afim de facilitar a utilização da aplicação, e tornar a experiência mais rica.
- **Implementação** – criação de testes unitários com pytest.
É possível criar testes para garantir que a aplicação esteja funcionando corretamente.
- **Documentação** – criação de documentação com Sphinx;
É possível adicionar Docstrings e criar documentação para explicar como a aplicação funciona e como ela pode ser utilizada.
- **Segurança** – implementação de controles de segurança;
É possível adicionar controles de segurança para garantir que os dados estejam seguros, como senhas, usuários, chaves das salas.- **Ce
rtificados SSL de Produção** – implementação de certificados SSL válidos;
É possível implementar suporte para certificados SSL de autoridades certificadoras para uso em produção.
- **Autenticação de Cliente SSL** – implementação de autenticação mútua SSL;
É possível implementar autenticação mútua SSL onde clientes também precisam de certificados.- **Interfac
e Web para ngrok** – implementação de interface web para gerenciar túneis;
É possível criar uma interface web para gerenciar os túneis ngrok, facilitando o compartilhamento de acesso e monitoramento de conexões remotas.