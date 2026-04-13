# 🧱 Estrutura do Projeto — Libras Hand Tracking

[⬅️ Voltar para o README principal](https://github.com/Natanael-Heinrick/libras-hand-tracking/blob/main/README.md)

> 📖 Este documento apresenta a **arquitetura geral** do projeto, os principais diretórios, o papel de cada arquivo e como os módulos se conectam entre si.

---

## 📑 Sumário

- [📌 Visão Geral](#-visão-geral)
- [🗂️ Estrutura de Alto Nível](#️-estrutura-de-alto-nível)
- [🧠 Núcleo de Hand Tracking](#-núcleo-de-hand-tracking)
- [🌐 Camada HTTP](#-camada-http)
- [🔌 Camada WebSocket](#-camada-websocket)
- [🎤 Módulo `soletracao_palavras`](#-módulo-soletracao_palavras)
- [🎮 Módulo `exercicios_libras`](#-módulo-exercicios_libras)
- [🧪 Arquivos Auxiliares](#-arquivos-auxiliares)
- [🗃️ Diretório `docs`](#️-diretório-docs)
- [🔁 Relação entre os Módulos](#-relação-entre-os-módulos)
- [⚠️ Observações Técnicas](#️-observações-técnicas)

---

## 📌 Visão Geral

O projeto está organizado em duas frentes principais:

| # | 🎯 Frente                        | 📋 Descrição                                                                |
|---|----------------------------------|-----------------------------------------------------------------------------|
| 1 | **✋ Hand Tracking + WebSocket** | Reconhecimento de letras e palavras por gestos em tempo real via webcam      |
| 2 | **🎤 Soletração por Voz**        | API HTTP com GIFs, áudio e tela web interativa para soletração por palavras |

> 💡 Além disso, existem arquivos auxiliares e uma estrutura de documentação organizada em `docs/`.

---

## 🗂️ Estrutura de Alto Nível

### 📁 Arquivos na raiz

| 📄 Arquivo                           | 🎯 Função principal                                  |
| ------------------------------------ | ----------------------------------------------------- |
| `api_server.py`                      | 🌐 Servidor HTTP — rotas de soletração e hand tracking |
| `websocket_server.py`                | 🔌 Servidor WebSocket — alfabeto e exercícios          |
| `websocket_client.py`                | 📡 Cliente WebSocket — modo alfabeto                   |
| `websocket_exercicios_client.py`     | 🎮 Cliente WebSocket — modo exercícios                 |
| `hand_tracking_service.py`           | 🧠 Núcleo de detecção e estabilização de letras        |
| `letter_classifier.py`              | 🔤 Regras de classificação de letras (estáticas/dinâmicas) |
| `hand_geometry.py`                   | 📐 Funções geométricas auxiliares                      |
| `test_camera.py`                     | 🧪 Script de teste da webcam                           |
| `README.md`                          | 📖 Documentação principal do projeto                   |

### 📂 Diretórios principais

| 📁 Diretório           | 🎯 Função                                              |
| ---------------------- | ------------------------------------------------------- |
| `docs/`                | 📚 Documentação técnica detalhada                       |
| `soletracao_palavras/` | 🎤 Módulo de soletração por voz e GIFs                  |
| `exercicios_libras/`   | 🎮 Módulo do modo exercícios (jogo)                     |
| `voice_to_libras/`     | 🔬 Estrutura conceitual de voz para LIBRAS (em progresso) |

---

## 🧠 Núcleo de Hand Tracking

> Esses arquivos formam a **base do reconhecimento de letras por gesto** e são reutilizados tanto pelo fluxo HTTP quanto pelo WebSocket.

---

### 🧠 `hand_tracking_service.py`

> Núcleo central que alimenta **todos os fluxos** do projeto.

| 🎯 Responsabilidade                                      |
| --------------------------------------------------------- |
| 📷 Receber e processar frames da webcam                   |
| 🖐️ Usar **MediaPipe** para detectar mãos                  |
| 🔤 Estabilizar letras detectadas (filtro temporal)         |
| 📝 Manter a palavra sendo montada em tempo real           |

> 🔗 É usado por: `api_server.py` (HTTP) e `websocket_server.py` (WebSocket)

---

### 🔤 `letter_classifier.py`

> Concentra a **lógica de reconhecimento** de cada letra em LIBRAS.

| 🎯 Responsabilidade                                      |
| --------------------------------------------------------- |
| 📏 Implementar regras de classificação por posição dos dedos |
| ✋ Tratar letras **estáticas** (posição fixa da mão)       |
| 🤟 Tratar letras **dinâmicas** como `H`, `J`, `K` e `W`  |

---

### 📐 `hand_geometry.py`

> Funções **geométricas auxiliares** usadas pela classificação.

| 🎯 Responsabilidade                                      |
| --------------------------------------------------------- |
| 📏 Cálculo de distâncias entre pontos da mão              |
| 🖐️ Apoio à classificação de dedos e posições              |
| 🔢 Funções matemáticas reutilizáveis                      |

---

## 🌐 Camada HTTP

> Responsável pela parte de **soletração por voz**, tela web e rotas de apoio.

---

### 🌐 `api_server.py`

> **Ponto de entrada** do servidor HTTP.

| 🎯 Responsabilidade                                      |
| --------------------------------------------------------- |
| 🛣️ Expor as rotas da API local                            |
| 🖥️ Entregar a tela web de soletração                      |
| 🖼️ Servir GIFs e áudios locais                            |
| ▶️ Iniciar e acompanhar sessões de soletração              |
| 🧪 Integrar hand tracking em rotas de consulta e teste    |

> 📖 Documentação completa das rotas: [`docs/api.md`](./docs/api.md)

---

## 🔌 Camada WebSocket

> Responsável pela **comunicação em tempo real** da webcam com o servidor.

---

### 🔌 `websocket_server.py`

> **Ponto de entrada** do servidor WebSocket.

| 🎯 Responsabilidade                                      |
| --------------------------------------------------------- |
| 📡 Receber frames da webcam em base64                     |
| 🧠 Processar os frames com `HandTrackingService`          |
| 📤 Responder com estado atualizado                        |

**🛣️ Rotas expostas:**

| Rota           | 📋 Descrição                          |
| -------------- | ------------------------------------- |
| `/alfabeto`    | 🔤 Modo reconhecimento de letras      |
| `/exercicios`  | 🎮 Modo jogo de exercícios            |

---

### 📡 `websocket_client.py`

> Cliente do **modo alfabeto**.

| 🎯 Responsabilidade                                      |
| --------------------------------------------------------- |
| 📷 Abrir a webcam                                         |
| 🔄 Codificar o frame em base64                            |
| 📤 Enviar frames ao servidor                              |
| 🔤 Exibir a letra e a palavra reconhecida                 |

---

### 🎮 `websocket_exercicios_client.py`

> Cliente do **modo exercícios**.

| 🎯 Responsabilidade                                      |
| --------------------------------------------------------- |
| 📷 Abrir a webcam                                         |
| 📤 Enviar frames ao servidor                              |
| 🎯 Exibir o estado do jogo                                |
| 📊 Mostrar palavra alvo, pontuação, nível e feedback      |

---

## 🎤 Módulo `soletracao_palavras`

> 📁 Diretório: `soletracao_palavras/`
>
> Concentra o **fluxo HTTP de soletração por voz e GIFs**.

---

### 📄 Arquivos principais

| 📄 Arquivo                | 🎯 Função                                      |
| ------------------------- | ----------------------------------------------- |
| `service.py`              | 🔤 Separação de frases, palavras e letras        |
| `audio_service.py`        | 🎙️ Salvamento e referência de áudios             |
| `transcription_service.py`| 🧠 Transcrição provisória do backend             |
| `tela.html`               | 🖥️ Interface de teste no navegador               |
| `__init__.py`             | 📦 Inicializador do módulo Python                |

### 📂 Subpastas

| 📁 Pasta   | 🎯 Função                                 |
| ---------- | ------------------------------------------ |
| `gifs/`    | 🖼️ Base local de GIFs por letra            |
| `audios/`  | 🔊 Arquivos de áudio enviados pela tela    |

---

### 🔍 Papel detalhado de cada arquivo

#### 🔤 `service.py`

| 🎯 Responsabilidade                                      |
| --------------------------------------------------------- |
| ✂️ Separar frases em palavras                              |
| 🔤 Separar palavras em letras                             |
| 📊 Montar grupos visuais para exibição                    |
| ▶️ Controlar a reprodução com `hold` e `continue`         |

#### 🎙️ `audio_service.py`

| 🎯 Responsabilidade                                      |
| --------------------------------------------------------- |
| 💾 Salvar o áudio enviado pela tela web                   |
| 📎 Guardar referência do último áudio salvo               |

#### 🧠 `transcription_service.py`

| 🎯 Responsabilidade                                      |
| --------------------------------------------------------- |
| 🔄 Oferecer transcrição provisória no backend             |
| 🧪 Validar o fluxo antes da integração real               |

#### 🖥️ `tela.html`

| 🎯 Responsabilidade                                      |
| --------------------------------------------------------- |
| 🌐 Interface de teste no navegador                        |
| 🎙️ Captura de áudio via Web API                           |
| 🗣️ Reconhecimento de fala no navegador (`Web Speech API`) |
| 🖼️ Exibição dos GIFs de letras em tempo real              |

---

## 🎮 Módulo `exercicios_libras`

> 📁 Diretório: `exercicios_libras/`
>
> Concentra a **lógica do modo exercícios** (jogo de soletração).

---

### 📄 Arquivos principais

| 📄 Arquivo                             | 🎯 Função                            |
| -------------------------------------- | ------------------------------------- |
| `service.py`                           | 🎮 Lógica do jogo de exercícios       |
| `__init__.py`                          | 📦 Inicializador do módulo             |
| `README.md`                            | 📖 Documentação do módulo              |

### 🗄️ Base de dados

| 📄 Arquivo                                  | 🎯 Função                         |
| ------------------------------------------- | ---------------------------------- |
| `dados/palavras_libras_filtrado.csv`         | 📋 Palavras usadas no modo jogo    |

---

### 🔍 Papel do serviço (`service.py`)

| 🎯 Responsabilidade                                      |
| --------------------------------------------------------- |
| 📋 Carregar palavras do CSV                               |
| 🎯 Filtrar por dificuldade (`facil`, `medio`, `dificil`)  |
| 📊 Controlar pontuação e calcular nível                   |
| 📝 Registrar última palavra concluída                     |
| 🎲 Escolher nova palavra aleatória (sem repetição imediata) |

---

## 🧪 Arquivos Auxiliares

---

### 🧪 `test_camera.py`

> Script simples para **testar se a webcam abre corretamente**.

---

### 📄 `hand_tracking.py`

> Arquivo relacionado à camada de hand tracking, mas **não é o principal ponto de entrada** do sistema atualmente.

---

### 📁 `voice_to_libras/`

> Diretório com **estrutura inicial conceitual** para uma trilha de voz para LIBRAS.

> ⚠️ Hoje **não é o núcleo do fluxo principal** ativo.

**📄 Arquivos relacionados:**

| 📄 Arquivo                    | 🎯 Função                              |
| ----------------------------- | --------------------------------------- |
| `voice_to_libras_demo.py`     | 🔬 Demo conceitual de voz para LIBRAS   |
| `VOICE_TO_LIBRAS_PLAN.md`     | 📋 Plano de desenvolvimento da feature  |

---

## 🗃️ Diretório `docs`

> 📁 Diretório: `docs/`
>
> Centraliza a **documentação técnica** do projeto, separando o README principal dos detalhes específicos.

### 📚 Documentos disponíveis

| 📄 Documento             | 🎯 Conteúdo                              |
| ------------------------ | ----------------------------------------- |
| `api.md`                 | 🌐 Documentação da API HTTP               |
| `websocket.md`           | 🔌 Documentação do WebSocket               |
| `exercicios.md`          | 🎮 Documentação do modo exercícios         |
| `soletracao-voz.md`      | 🎤 Documentação da soletração por voz      |
| `instalacao.md`          | ⚙️ Guia de instalação                      |
| `estrutura-projeto.md`   | 🧱 Este documento (estrutura do projeto)   |

---

## 🔁 Relação entre os Módulos

### 🔌 Fluxo WebSocket

```
📷 websocket_client.py / websocket_exercicios_client.py
    │
    │ 📤 envia frame (base64)
    ▼
🔌 websocket_server.py
    │
    │ 🧠 processa frame
    ▼
🧠 hand_tracking_service.py
    │
    │ 🔤 classifica letra
    ▼
🔤 letter_classifier.py
    │
    │ 📤 retorna estado
    ▼
📡 Cliente recebe resposta atualizada
```

---

### 🌐 Fluxo HTTP

```
🌐 Requisição HTTP
    │
    ▼
🌐 api_server.py
    │
    │ 🎤 usa serviços
    ▼
📦 soletracao_palavras/ (service, audio, transcription)
    │
    │ 📤 retorna
    ▼
📄 JSON / 🖼️ GIFs / 🔊 Áudios / 🖥️ HTML
```

---

### 🎮 Fluxo de Exercícios

```
🎮 websocket_exercicios_client.py
    │
    │ 📤 envia frame + ações
    ▼
🔌 websocket_server.py
    │
    ├── 🧠 hand_tracking_service.py (letras)
    │
    ├── 🎮 exercicios_libras/service.py (lógica do jogo)
    │
    │ 📤 retorna estado + exercicio
    ▼
🎮 Cliente recebe payload unificado
```

---

## ⚠️ Observações Técnicas

- ⚙️ O projeto ainda combina **HTTP e WebSocket** no mesmo repositório — coerente para a fase atual.
- 🔮 No futuro, pode valer separar mais claramente as camadas (ex: microsserviços).
- 🚫 Pastas como `__pycache__` e `venv` **não fazem parte** da lógica do projeto.
- 📚 A documentação em `docs/` existe para facilitar a leitura da estrutura por **novos colaboradores**.

---

[⬅️ Voltar para o README principal](https://github.com/Natanael-Heinrick/libras-hand-tracking/blob/main/README.md)
