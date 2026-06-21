# LIBRAS Hand Tracking

Projeto desenvolvido para auxiliar o aprendizado de LIBRAS utilizando Visão Computacional, reconhecimento de gestos e jogos educativos.

O sistema utiliza OpenCV, MediaPipe, WebSocket e PyWebView para fornecer diferentes modos de aprendizagem interativos.

## Funcionalidades

* Reconhecimento de letras em LIBRAS em tempo real.
* Exercícios com palavras e imagens.
* Duelo local entre jogadores.
* Quiz visual de letras.
* Sistema de pontuação e loja virtual.
* Soletração por voz.
* Comunicação em tempo real utilizando WebSocket.

## Estrutura do Projeto

```text
LIBRAS-HAND-TRACKING/
│
├── docs/
│   ├── api.md
│   ├── estrutura-projeto.md
│   ├── exercicios.md
│   ├── instalacao.md
│   ├── soletracao-voz.md
│   ├── validacao-maos.md
│   └── websocket.md
│
├── duelo_libras/
├── exercicios_libras/
├── image/
├── loja/
├── quiz_visual_libras/
├── soletracao_palavras/
├── validacao_maos/
├── voice_to_libras/
│
├── api_server.py
├── game_menu.py
├── hand_geometry.py
├── hand_tracking_service.py
├── hand_tracking.py
├── letter_classifier.py
├── test_camera.py
├── ui_decor.py
├── voice_to_libras_demo.py
├── websocket_client.py
├── websocket_duelo_client.py
├── websocket_exercicios_client.py
├── websocket_server.py
├── README.md
└── .gitignore
```

## Documentação Técnica

* [Instalação](docs/instalacao.md)
* [API HTTP](docs/api.md)
* [WebSocket](docs/websocket.md)
* [Exercícios](docs/exercicios.md)
* [Soletração por Voz](docs/soletracao-voz.md)
* [Validação das Mãos](docs/validacao-maos.md)
* [Estrutura do Projeto](docs/estrutura-projeto.md)

## Instalação

Para instalar o projeto, consulte:

* [Guia de Instalação](docs/instalacao.md)

## Execução

### Iniciar o servidor WebSocket

```bash
python websocket_server.py
```

### Executar o reconhecimento de letras

```bash
python websocket_client.py
```

### Executar o modo exercícios

```bash
python websocket_exercicios_client.py
```

### Executar o modo duelo

```bash
python websocket_duelo_client.py
```

### Executar o menu principal

```bash
python game_menu.py
```

### Executar a API HTTP

```bash
python api_server.py
```

### Testar a câmera

```bash
python test_camera.py
```

## Modos Disponíveis

### Fotos

Mostra imagens de objetos e o usuário deve soletrar corretamente o nome utilizando LIBRAS.

### Palavras

Treino tradicional utilizando palavras selecionadas aleatoriamente.

### Imagens de Letras

Exibe imagens das configurações das mãos para identificação das letras correspondentes.

### Loja

Permite utilizar os pontos conquistados durante os exercícios para desbloquear itens.

### Duelo de Tempo

Competição local entre dois jogadores utilizando a mesma câmera.

### Voz para LIBRAS

Converte palavras faladas em representações visuais em LIBRAS.

## Tecnologias Utilizadas

* Python
* OpenCV
* MediaPipe
* NumPy
* WebSocket
* PyWebView
* HTML
* CSS
* JavaScript

## Objetivo

Promover o ensino e a prática de LIBRAS através de tecnologias de Visão Computacional e jogos educativos interativos.
