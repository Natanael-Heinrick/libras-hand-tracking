# 🧱 Estrutura do Projeto

[⬅️ Voltar para o README principal](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/README.md)

Este documento apresenta a arquitetura geral do projeto, os principais diretórios e o papel de cada arquivo relevante.

## 📌 Visão Geral

O projeto está organizado hoje em duas frentes principais:

1. reconhecimento de letras e palavras por hand tracking com WebSocket
2. soletração por voz com API HTTP, GIFs e tela web

Além disso, existem alguns arquivos auxiliares e uma estrutura de documentação em `docs/`.

## 🗂️ Estrutura de alto nível

Na raiz do projeto:

- [api_server.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/api_server.py)
- [websocket_server.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/websocket_server.py)
- [websocket_client.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/websocket_client.py)
- [websocket_exercicios_client.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/websocket_exercicios_client.py)
- [hand_tracking_service.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/hand_tracking_service.py)
- [letter_classifier.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/letter_classifier.py)
- [hand_geometry.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/hand_geometry.py)
- [test_camera.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/test_camera.py)
- [README.md](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/README.md)

Diretórios principais:

- [docs](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/docs)
- [soletracao_palavras](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/soletracao_palavras)
- [exercicios_libras](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/exercicios_libras)
- [voice_to_libras](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/voice_to_libras)

## 🧠 Núcleo de hand tracking

Esses arquivos formam a base do reconhecimento de letras por gesto.

### [hand_tracking_service.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/hand_tracking_service.py)

Responsável por:

- receber e processar frames
- usar MediaPipe para detectar mãos
- estabilizar letras detectadas
- manter a palavra sendo montada

É o núcleo que alimenta tanto:

- o fluxo HTTP de hand tracking
- o fluxo WebSocket

### [letter_classifier.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/letter_classifier.py)

Responsável por:

- implementar regras de classificação das letras
- tratar letras estáticas
- tratar letras dinâmicas como `H`, `J`, `K` e `W`

Esse arquivo concentra a lógica mais específica de reconhecimento.

### [hand_geometry.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/hand_geometry.py)

Responsável por:

- funções geométricas auxiliares
- cálculo de distâncias
- apoio à classificação dos dedos e posições da mão

## 🌐 Camada HTTP

Responsável pela parte de soletração por voz, tela web e rotas de apoio.

### [api_server.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/api_server.py)

É o ponto de entrada do servidor HTTP.

Responsável por:

- expor as rotas da API local
- entregar a tela web de soletração
- servir GIFs e áudios locais
- iniciar e acompanhar sessões de soletração
- integrar hand tracking em rotas de consulta e teste

## 🔌 Camada WebSocket

Responsável pela comunicação em tempo real da webcam com o servidor.

### [websocket_server.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/websocket_server.py)

É o ponto de entrada do servidor WebSocket.

Responsável por:

- receber frames da webcam em base64
- processar os frames com `HandTrackingService`
- responder com estado atualizado
- expor duas rotas:
  - `/alfabeto`
  - `/exercicios`

### [websocket_client.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/websocket_client.py)

Cliente do modo alfabeto.

Responsável por:

- abrir a webcam
- codificar o frame em base64
- enviar frames ao servidor
- exibir a letra e a palavra reconhecida

### [websocket_exercicios_client.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/websocket_exercicios_client.py)

Cliente do modo exercícios.

Responsável por:

- abrir a webcam
- enviar frames ao servidor
- exibir o estado do jogo
- mostrar palavra alvo, pontuação, nível e feedback

## 🎤 Módulo `soletracao_palavras`

Diretório:

- [soletracao_palavras](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/soletracao_palavras)

Esse módulo concentra o fluxo HTTP de soletração por voz e GIFs.

### Arquivos principais

- [soletracao_palavras/service.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/soletracao_palavras/service.py)
- [soletracao_palavras/audio_service.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/soletracao_palavras/audio_service.py)
- [soletracao_palavras/transcription_service.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/soletracao_palavras/transcription_service.py)
- [soletracao_palavras/tela.html](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/soletracao_palavras/tela.html)
- [soletracao_palavras/__init__.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/soletracao_palavras/__init__.py)

### Subpastas importantes

- [soletracao_palavras/gifs](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/soletracao_palavras/gifs)
  Base local de GIFs por letra.
- [soletracao_palavras/audios](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/soletracao_palavras/audios)
  Arquivos de áudio enviados pela tela.

### Papel de cada arquivo

#### [soletracao_palavras/service.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/soletracao_palavras/service.py)

Responsável por:

- separar frases em palavras
- separar palavras em letras
- montar grupos visuais
- controlar a reprodução com `hold` e `continue`

#### [soletracao_palavras/audio_service.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/soletracao_palavras/audio_service.py)

Responsável por:

- salvar o áudio enviado pela tela
- guardar referência do último áudio salvo

#### [soletracao_palavras/transcription_service.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/soletracao_palavras/transcription_service.py)

Responsável por:

- oferecer uma transcrição provisória no backend para validar o fluxo

#### [soletracao_palavras/tela.html](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/soletracao_palavras/tela.html)

Responsável por:

- interface de teste no navegador
- captura de áudio
- reconhecimento de fala no navegador
- exibição dos GIFs

## 🎮 Módulo `exercicios_libras`

Diretório:

- [exercicios_libras](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/exercicios_libras)

Esse módulo concentra a lógica do modo exercícios.

### Arquivos principais

- [exercicios_libras/service.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/exercicios_libras/service.py)
- [exercicios_libras/__init__.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/exercicios_libras/__init__.py)
- [exercicios_libras/README.md](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/exercicios_libras/README.md)

### Base de dados

- [exercicios_libras/dados/palavras_libras_filtrado.csv](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/exercicios_libras/dados/palavras_libras_filtrado.csv)

### Papel do serviço

[exercicios_libras/service.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/exercicios_libras/service.py) é responsável por:

- carregar palavras do CSV
- filtrar por dificuldade
- controlar pontuação
- calcular nível
- registrar última palavra concluída
- escolher nova palavra aleatória

## 🧪 Arquivos auxiliares

### [test_camera.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/test_camera.py)

Script simples para testar se a webcam abre corretamente.

### [hand_tracking.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/hand_tracking.py)

Arquivo relacionado à camada de hand tracking, mas hoje não é o principal ponto de entrada do sistema.

### [voice_to_libras](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/voice_to_libras)

Diretório com estrutura inicial conceitual para uma trilha de voz para LIBRAS.

Hoje ele não é o núcleo do fluxo principal ativo.

Arquivos relacionados:

- [voice_to_libras_demo.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/voice_to_libras_demo.py)
- [VOICE_TO_LIBRAS_PLAN.md](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/VOICE_TO_LIBRAS_PLAN.md)

## 🗃️ Diretório `docs`

Diretório:

- [docs](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/docs)

Função:

- centralizar a documentação técnica do projeto
- separar o README principal dos detalhes específicos

Documentos atuais:

- [docs/api.md](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/docs/api.md)
- [docs/websocket.md](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/docs/websocket.md)
- [docs/exercicios.md](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/docs/exercicios.md)
- [docs/soletracao-voz.md](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/docs/soletracao-voz.md)
- [docs/instalacao.md](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/docs/instalacao.md)
- [docs/estrutura-projeto.md](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/docs/estrutura-projeto.md)

## 🔁 Relação entre os módulos

### Fluxo WebSocket

1. `websocket_client.py` ou `websocket_exercicios_client.py` captura a webcam
2. envia o frame para `websocket_server.py`
3. `websocket_server.py` usa `hand_tracking_service.py`
4. `hand_tracking_service.py` usa `letter_classifier.py`
5. o servidor responde com o estado atualizado

### Fluxo HTTP

1. `api_server.py` recebe a requisição
2. usa serviços de `soletracao_palavras`
3. entrega JSON, GIFs, áudios ou HTML
4. a interface `tela.html` coordena a experiência no navegador

### Fluxo de exercícios

1. `websocket_server.py` recebe ações do cliente de exercícios
2. usa `hand_tracking_service.py` para as letras
3. usa `exercicios_libras/service.py` para a lógica do jogo
4. devolve `estado` e `exercicio` no mesmo payload

## ⚠️ Observações técnicas

- O projeto ainda combina HTTP e WebSocket no mesmo repositório.
- Isso é coerente para a fase atual, mas no futuro pode valer separar mais claramente as camadas.
- Pastas como `__pycache__` e `venv` não fazem parte da lógica do projeto.
- A documentação em `docs/` existe justamente para facilitar a leitura dessa estrutura por novos colaboradores.

[⬅️ Voltar para o README principal](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/README.md)
