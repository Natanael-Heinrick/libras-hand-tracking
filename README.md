# Hand Tracking Project

Projeto em Python para reconhecimento de letras e palavras em LIBRAS com duas frentes principais:

- hand tracking em tempo real com webcam, OpenCV, MediaPipe e WebSocket
- soletracao por voz com servidor HTTP, tela web e exibicao de GIFs

## Sumario

- [Visao Geral](#visao-geral)
- [Como Navegar na Documentacao](#como-navegar-na-documentacao)
- [Execucao Rapida](#execucao-rapida)
- [Execucao por Terminal](#execucao-por-terminal)
- [Documentacao Detalhada](#documentacao-detalhada)
- [Observacoes](#observacoes)

## Visao Geral

O projeto possui hoje dois fluxos principais:

1. WebSocket + webcam para reconhecimento de letras e modo exercicios
2. HTTP + navegador para soletracao por voz e exibicao de GIFs

Este `README.md` agora funciona como ponto de entrada da documentacao. Os detalhes tecnicos foram separados para a pasta `docs/`.

## Como Navegar na Documentacao

Documentos disponiveis:

- [API HTTP](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/docs/api.md)
- [WebSocket](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/docs/websocket.md)
- [Soletracao por Voz](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/docs/soletracao-voz.md)
- [Modo Exercicios](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/docs/exercicios.md)
- [Instalacao](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/docs/instalacao.md)
- [Estrutura do Projeto](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/docs/estrutura-projeto.md)

Cada documento dentro de `docs/` possui link de retorno para este `README.md`.

## Execucao Rapida

### Soletracao por voz

```powershell
python api_server.py
```

Depois abra:

```text
http://127.0.0.1:8000/soletracao-palavras/tela
```

### Modo alfabeto via WebSocket

Terminal 1:

```powershell
python websocket_server.py
```

Terminal 2:

```powershell
python websocket_client.py
```

### Modo exercicios via WebSocket

Terminal 1:

```powershell
python websocket_server.py
```

Terminal 2:

```powershell
python websocket_exercicios_client.py
```

## Execucao por Terminal

### Terminal 1: servidor HTTP

Arquivo:

- [api_server.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/api_server.py)

Comando:

```powershell
python api_server.py
```

Libera:

- API HTTP local
- tela web da soletracao
- rotas de GIF, audio e status

### Terminal 1: servidor WebSocket

Arquivo:

- [websocket_server.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/websocket_server.py)

Comando:

```powershell
python websocket_server.py
```

Libera:

- rota `/alfabeto`
- rota `/exercicios`

### Terminal 2: cliente do modo alfabeto

Arquivo:

- [websocket_client.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/websocket_client.py)

Comando:

```powershell
python websocket_client.py
```

Depende de:

- `websocket_server.py` ja estar em execucao

### Terminal 2: cliente do modo exercicios

Arquivo:

- [websocket_exercicios_client.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/websocket_exercicios_client.py)

Comando:

```powershell
python websocket_exercicios_client.py
```

Depende de:

- `websocket_server.py` ja estar em execucao

### Terminal auxiliar: teste de webcam

Arquivo:

- [test_camera.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/test_camera.py)

Comando:

```powershell
python test_camera.py
```

## Documentacao Detalhada

### API HTTP

Use este documento para consultar:

- rotas HTTP
- porta
- endpoints de soletracao
- tela web

Link:

- [docs/api.md](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/docs/api.md)

### WebSocket

Use este documento para consultar:

- rotas `/alfabeto` e `/exercicios`
- clientes
- fluxo em tempo real

Link:

- [docs/websocket.md](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/docs/websocket.md)

### Soletracao por Voz

Use este documento para consultar:

- fluxo HTTP
- GIFs
- audios
- tela de teste

Link:

- [docs/soletracao-voz.md](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/docs/soletracao-voz.md)

### Modo Exercicios

Use este documento para consultar:

- CSV de palavras
- pontuacao
- dificuldade
- nivel
- selecao aleatoria

Link:

- [docs/exercicios.md](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/docs/exercicios.md)

### Instalacao

Link:

- [docs/instalacao.md](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/docs/instalacao.md)

### Estrutura do Projeto

Link:

- [docs/estrutura-projeto.md](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/docs/estrutura-projeto.md)

## Observacoes

- Este bloco 1 cria a base da pasta `docs/`.
- O `README.md` da raiz agora serve como hub principal.
- Nos proximos blocos, cada documento em `docs/` pode ser expandido com mais detalhes tecnicos.
