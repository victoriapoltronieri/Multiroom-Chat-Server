# Design Document

## Overview

Esta implementação adiciona criptografia SSL/TLS ao servidor de chat multi-sala existente usando o módulo `ssl` nativo do Python. A abordagem é minimalista e transparente - envolvemos os sockets existentes com SSL sem alterar a lógica de negócio. O servidor usará os certificados já criados (cert.pem e key.pem) para estabelecer conexões seguras.

## Architecture

### SSL Wrapper Pattern
- **Servidor**: O socket do servidor será envolvido com `ssl.wrap_socket()` após aceitar conexões
- **Cliente**: O socket do cliente será envolvido com SSL antes de conectar ao servidor
- **Transparência**: Uma vez envolvidos, os sockets SSL funcionam como sockets normais para send/recv

### Certificate Management
- Certificados localizados no diretório raiz do projeto
- Servidor carrega cert.pem (certificado público) e key.pem (chave privada)
- Cliente configurado para aceitar certificados auto-assinados (desenvolvimento)

## Components and Interfaces

### Server-Side Changes (chat_multiroom_server.py)

#### SSL Context Setup
```python
import ssl

def create_ssl_context():
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain('cert.pem', 'key.pem')
    return context
```

#### Connection Handling
- Modificar o loop principal para envolver conexões aceitas com SSL
- Manter toda a lógica existente de `handle_client()` inalterada
- Adicionar tratamento de erros SSL específicos

### Client-Side Changes (chat_client_terminal.py)

#### SSL Context Setup
```python
import ssl

def create_client_ssl_context():
    context = ssl.create_default_context()
    context.check_hostname = False  # Para certificados auto-assinados
    context.verify_mode = ssl.CERT_NONE  # Para desenvolvimento
    return context
```

#### Connection Establishment
- Envolver socket com SSL antes de conectar
- Manter toda a lógica de envio/recebimento de mensagens inalterada

## Data Models

Nenhuma alteração nos modelos de dados existentes. As estruturas de usuários, salas e mensagens permanecem idênticas:
- `clients = {}` (socket -> username)
- `rooms = {}` (nome -> set de sockets)
- `user_rooms = {}` (socket -> nome da sala)

## Error Handling

### SSL-Specific Errors
1. **Certificate Loading Errors**
   - Capturar `ssl.SSLError` durante carregamento de certificados
   - Exibir mensagem clara e encerrar servidor se certificados inválidos

2. **Connection Errors**
   - Capturar `ssl.SSLError` durante handshake
   - Log de conexões SSL falhadas sem interromper servidor

3. **Runtime SSL Errors**
   - Tratar `ssl.SSLWantReadError` e `ssl.SSLWantWriteError`
   - Manter robustez existente para desconexões de clientes

### Backward Compatibility
- Manter mensagens de erro existentes para funcionalidades do chat
- Adicionar apenas mensagens específicas de SSL quando necessário

## Testing Strategy

### Manual Testing Approach
1. **Certificate Validation**
   - Verificar se servidor inicia com certificados válidos
   - Testar falha quando certificados ausentes/inválidos

2. **Connection Testing**
   - Conectar cliente SSL ao servidor SSL
   - Verificar handshake SSL bem-sucedido

3. **Functionality Testing**
   - Executar todos os fluxos existentes (registro, login, chat)
   - Confirmar que todas as funcionalidades funcionam sobre SSL

4. **Error Scenarios**
   - Testar cliente não-SSL tentando conectar a servidor SSL
   - Verificar comportamento com certificados expirados

### Test Environment
- Usar localhost para testes locais
- Testar com ngrok para simular ambiente remoto
- Verificar compatibilidade com certificados auto-assinados