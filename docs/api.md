# 🌐 API — Libras Hand Tracking

[⬅️ Voltar para o README principal](https://github.com/Natanael-Heinrick/libras-hand-tracking/blob/main/README.md)

> 📖 Documentação completa da API HTTP do projeto **Libras Hand Tracking**, incluindo rotas, métodos, parâmetros, códigos de resposta e exemplos práticos com `curl`.

---

## 📑 Sumário

- [🔍 Visão Geral](#-visão-geral)
- [▶️ Como Subir a API](#️-como-subir-a-api)
- [🔓 Autenticação](#-autenticação)
- [📦 Formato de Resposta](#-formato-de-resposta)
- [🗺️ Rotas](#️-rotas)
  - [🏠 Geral](#-geral)
  - [✋ Hand Tracking](#-hand-tracking)
  - [📝 Soletração por Palavras](#-soletração-por-palavras)
- [📊 Códigos de Status HTTP](#-códigos-de-status-http)
- [🧪 Fluxos de Teste Recomendados](#-fluxos-de-teste-recomendados)
- [⚠️ Observações Técnicas](#️-observações-técnicas)

---

## 🔍 Visão Geral

| 🏷️ Item           | 📋 Valor                                                                                                       |
| ------------------ | --------------------------------------------------------------------------------------------------------------- |
| **📁 Arquivo**     | [`api_server.py`](https://github.com/Natanael-Heinrick/libras-hand-tracking/blob/main/api_server.py)            |
| **🌍 Base URL**    | `http://127.0.0.1:8000`                                                                                        |
| **⚙️ Servidor**    | `ThreadingHTTPServer` (stdlib)                                                                                  |
| **📄 Formato**     | JSON (exceto rotas de stream, arquivos estáticos e HTML)                                                        |

A API cobre dois domínios:

| # | 🎯 Domínio                     | 📋 Descrição                                                                  |
|---|--------------------------------|-------------------------------------------------------------------------------|
| 1 | **✋ Hand Tracking**            | Controle de câmera, reconhecimento de letras em Libras e consulta de estado   |
| 2 | **📝 Soletração por Palavras** | Decomposição de texto em letras, reprodução com GIFs/áudio e tela web interativa |

---

## ▶️ Como Subir a API

```bash
python api_server.py
```

> 💡 Após a inicialização, todas as rotas ficam disponíveis em `http://127.0.0.1:8000`.

---

## 🔓 Autenticação

A API **não exige autenticação**. Todas as rotas são públicas e acessíveis localmente.

---

## 📦 Formato de Resposta

Salvo indicação em contrário, todas as respostas são retornadas em **JSON** com `Content-Type: application/json`.

⚠️ **Exceções:**

| 🛣️ Rota                                | 📄 Content-Type                  |
| ---------------------------------------- | -------------------------------- |
| `GET /camera/stream`                     | `multipart/x-mixed-replace`     |
| `GET /soletracao-palavras/tela`          | `text/html`                     |
| `GET /soletracao-palavras/gifs/...`      | `image/gif`                     |
| `GET /soletracao-palavras/audios/...`    | depende do formato do arquivo    |

---

## 🗺️ Rotas

### 🏠 Geral

---

#### 🏠 `GET /`

> Verifica se a API está ativa e lista as principais rotas disponíveis.

**📥 Parâmetros:** nenhum

**📤 Resposta:**

| Campo      | Tipo       | Descrição                           |
| ---------- | ---------- | ----------------------------------- |
| `mensagem` | `string`   | Confirmação de que a API está ativa |
| `rotas`    | `string[]` | Lista das rotas principais          |

**💻 Exemplo:**

```bash
curl http://127.0.0.1:8000/
```

```json
{
  "mensagem": "API de hand tracking ativa",
  "rotas": [
    "/alfabeto",
    "/estado",
    "/soletracao-palavras?texto=oi"
  ]
}
```

---

### ✋ Hand Tracking

---

#### 🔤 `GET /alfabeto`

> Consulta o estado atual do modo alfabeto, incluindo letras suportadas e estado da câmera.

**📥 Parâmetros:** nenhum

**📤 Resposta:**

| Campo                      | Tipo       | Descrição                                   |
| -------------------------- | ---------- | ------------------------------------------- |
| `rota`                     | `string`   | Rota chamada                                |
| `letras_suportadas`        | `string[]` | Lista de letras reconhecidas pelo modelo     |
| `camera_ativa`             | `boolean`  | Se a webcam está ligada                     |
| `estado_atual`             | `object`   | Último estado detectado pelo hand tracking  |
| `observacao`               | `string`   | Informações adicionais                      |
| `query_params_recebidos`   | `object`   | Query params enviados na requisição         |

**💻 Exemplo:**

```bash
curl http://127.0.0.1:8000/alfabeto
```

---

#### 📊 `GET /estado`

> Retorna o estado mais recente detectado pelo serviço de hand tracking.

**📥 Parâmetros:** nenhum

**📤 Resposta:**

| Campo             | Tipo       | Descrição                                  |
| ----------------- | ---------- | ------------------------------------------ |
| `letra`           | `string`   | Letra detectada no frame atual             |
| `letra_estavel`   | `string`   | Letra estabilizada após filtro temporal    |
| `palavra`         | `string`   | Palavra acumulada até o momento            |
| `maos_detectadas` | `integer`  | Quantidade de mãos visíveis na câmera      |
| `deteccoes`       | `object[]` | Detalhes de cada mão detectada             |

**💻 Exemplo:**

```bash
curl http://127.0.0.1:8000/estado
```

---

#### 📷 `GET /camera/iniciar`

> Inicia a captura da webcam pelo serviço de hand tracking.

**📥 Parâmetros:** nenhum

**📤 Resposta:**

| Campo          | Tipo      | Descrição                     |
| -------------- | --------- | ----------------------------- |
| `mensagem`     | `string`  | Mensagem de confirmação       |
| `camera_ativa` | `boolean` | `true` se iniciada com êxito  |

**💻 Exemplo:**

```bash
curl http://127.0.0.1:8000/camera/iniciar
```

```json
{
  "mensagem": "Webcam iniciada com sucesso",
  "camera_ativa": true
}
```

---

#### 🛑 `GET /camera/parar`

> Encerra a captura da webcam.

**📥 Parâmetros:** nenhum

**📤 Resposta:**

| Campo          | Tipo      | Descrição                       |
| -------------- | --------- | ------------------------------- |
| `mensagem`     | `string`  | Mensagem de confirmação         |
| `camera_ativa` | `boolean` | `false` se encerrada com êxito  |

**💻 Exemplo:**

```bash
curl http://127.0.0.1:8000/camera/parar
```

```json
{
  "mensagem": "Webcam encerrada com sucesso",
  "camera_ativa": false
}
```

---

#### 🎥 `GET /camera/stream`

> Abre um stream MJPEG da câmera com o processamento de hand tracking aplicado.

**📥 Parâmetros:** nenhum

**📤 Resposta:** `multipart/x-mixed-replace` com frames JPEG em sequência.

> 💡 **Dica:** abra esta URL diretamente no navegador ou use em uma tag `<img>` para visualizar o stream em tempo real.

**💻 Exemplo:**

```bash
# 🌐 Abrir no navegador
http://127.0.0.1:8000/camera/stream

# 🖼️ Ou usar em HTML
# <img src="http://127.0.0.1:8000/camera/stream" />
```

---

#### 🧪 `GET /teste/a`

> Executa um teste automatizado de reconhecimento específico para a letra **A**.

**📥 Parâmetros:** nenhum

**📤 Códigos de resposta:**

| Status | 🏷️   | Descrição                                |
| ------ | ----- | ---------------------------------------- |
| `200`  | ✅    | Letra reconhecida com sucesso            |
| `408`  | ⏱️    | Timeout — letra não reconhecida a tempo  |

**💻 Exemplo:**

```bash
curl http://127.0.0.1:8000/teste/a
```

---

#### 🔤 `GET /teste/letra/{letra}`

> Executa um teste de reconhecimento para uma letra específica suportada pelo modelo.

**📥 Parâmetro de rota:**

| Parâmetro | Tipo     | Obrigatório | Descrição                       |
| --------- | -------- | ----------- | ------------------------------- |
| `letra`   | `string` | ✅ sim      | Letra maiúscula a ser testada   |

**🔠 Letras suportadas:**

> `A` · `C` · `D` · `E` · `F` · `G` · `I` · `J` · `K` · `M` · `N` · `O` · `P` · `R` · `S` · `T` · `U` · `V`

**📤 Códigos de resposta:**

| Status | 🏷️   | Descrição                           |
| ------ | ----- | ----------------------------------- |
| `200`  | ✅    | Letra reconhecida com sucesso       |
| `400`  | ❌    | Letra inválida / não suportada      |
| `408`  | ⏱️    | Timeout — não reconhecida a tempo   |

**💻 Exemplo:**

```bash
curl http://127.0.0.1:8000/teste/letra/O
```

---

### 📝 Soletração por Palavras

---

#### 📝 `GET /soletracao-palavras`

> Recebe um texto e devolve a estrutura completa de soletração, decomposta em palavras e letras.

**📥 Query params:**

| Parâmetro | Tipo     | Obrigatório | Descrição         |
| --------- | -------- | ----------- | ----------------- |
| `texto`   | `string` | ✅ sim      | Texto a soletrar  |

**📤 Resposta:**

| Campo              | Tipo       | Descrição                                     |
| ------------------ | ---------- | --------------------------------------------- |
| `rota`             | `string`   | Rota chamada                                  |
| `texto_original`   | `string`   | Texto enviado sem alterações                  |
| `texto_normalizado`| `string`   | Texto em maiúsculas, sem espaços/acentos      |
| `palavras`         | `string[]` | Lista de palavras extraídas                   |
| `grupos_palavras`  | `object[]` | Agrupamento de letras por palavra             |
| `letras`           | `string[]` | Todas as letras na ordem de soletração        |
| `sequencia`        | `object[]` | Sequência detalhada para reprodução           |
| `status_atual`     | `string`   | Estado atual da sessão                        |
| `proximo_status`   | `string`   | Próximo passo sugerido                        |

**💻 Exemplo:**

```bash
curl "http://127.0.0.1:8000/soletracao-palavras?texto=oi%20tudo%20bem"
```

```json
{
  "texto_original": "oi tudo bem",
  "texto_normalizado": "OITUDOBEM",
  "palavras": ["OI", "TUDO", "BEM"]
}
```

---

#### ▶️ `GET /soletracao-palavras/iniciar`

> Inicia uma sessão de reprodução da soletração no backend. A sessão controla o ritmo e a ordem de exibição das letras.

**📥 Query params:**

| Parâmetro | Tipo     | Obrigatório | Descrição         |
| --------- | -------- | ----------- | ----------------- |
| `texto`   | `string` | ✅ sim      | Texto a soletrar  |

**📤 Resposta:**

| Campo              | Tipo       | Descrição                                   |
| ------------------ | ---------- | ------------------------------------------- |
| `session_id`       | `string`   | Identificador único da sessão               |
| `texto_original`   | `string`   | Texto enviado                               |
| `texto_normalizado`| `string`   | Texto normalizado                           |
| `palavras`         | `string[]` | Palavras extraídas                          |
| `grupos_palavras`  | `object[]` | Letras agrupadas por palavra                |
| `fila`             | `object[]` | Fila de itens a reproduzir                  |
| `duracao_item_ms`  | `integer`  | Duração de cada item em milissegundos       |
| `duracao_pausa_ms` | `integer`  | Duração da pausa entre itens (ms)           |
| `status_atual`     | `string`   | Estado da sessão após inicialização         |

**💻 Exemplo:**

```bash
curl "http://127.0.0.1:8000/soletracao-palavras/iniciar?texto=oi"
```

---

#### ⏱️ `GET /soletracao-palavras/status`

> Consulta o progresso da sessão de reprodução em andamento.

**📥 Parâmetros:** nenhum

**📤 Resposta:**

| Campo             | Tipo       | Descrição                                    |
| ----------------- | ---------- | -------------------------------------------- |
| `status_atual`    | `string`   | Estado atual (`reproduzindo`, `pausado`...)   |
| `session_id`      | `string`   | ID da sessão ativa                           |
| `palavras`        | `string[]` | Palavras da sessão                           |
| `grupos_palavras` | `object[]` | Letras por palavra                           |
| `fila`            | `object[]` | Fila completa de itens                       |
| `item_atual`      | `object`   | Item sendo reproduzido no momento            |
| `indice_atual`    | `integer`  | Índice do item atual na fila                 |
| `restante_ms_item`| `integer`  | Tempo restante do item atual (ms)            |
| `finalizado`      | `boolean`  | `true` se toda a fila já foi reproduzida     |

**💻 Exemplo:**

```bash
curl http://127.0.0.1:8000/soletracao-palavras/status
```

---

#### 🖥️ `GET /soletracao-palavras/tela`

> Entrega a página HTML interativa para testar o fluxo de soletração com GIFs e reconhecimento de voz no navegador.

**📥 Parâmetros:** nenhum

**📤 Resposta:** `text/html`

**💻 Exemplo:**

```bash
# 🌐 Abrir diretamente no navegador
http://127.0.0.1:8000/soletracao-palavras/tela
```

---

#### 🖼️ `GET /soletracao-palavras/gifs/{arquivo}`

> Entrega um GIF de letra da base local.

**📥 Parâmetro de rota:**

| Parâmetro | Tipo     | Obrigatório | Descrição                         |
| --------- | -------- | ----------- | --------------------------------- |
| `arquivo` | `string` | ✅ sim      | Nome do arquivo (ex: `O.gif`)     |

**📤 Códigos de resposta:**

| Status | 🏷️   | Descrição                   |
| ------ | ----- | --------------------------- |
| `200`  | ✅    | GIF retornado com sucesso   |
| `404`  | ❌    | Arquivo não encontrado      |

**💻 Exemplo:**

```bash
curl -O http://127.0.0.1:8000/soletracao-palavras/gifs/O.gif
```

---

#### 🔊 `GET /soletracao-palavras/audios/{arquivo}`

> Entrega um arquivo de áudio previamente salvo no backend.

**📥 Parâmetro de rota:**

| Parâmetro | Tipo     | Obrigatório | Descrição                                             |
| --------- | -------- | ----------- | ----------------------------------------------------- |
| `arquivo` | `string` | ✅ sim      | Nome do arquivo (ex: `audio_20260330_150241.webm`)    |

**📤 Códigos de resposta:**

| Status | 🏷️   | Descrição                     |
| ------ | ----- | ----------------------------- |
| `200`  | ✅    | Áudio retornado com sucesso   |
| `404`  | ❌    | Arquivo não encontrado        |

**💻 Exemplo:**

```bash
curl -O http://127.0.0.1:8000/soletracao-palavras/audios/audio_20260330_150241_861975.webm
```

---

#### 🎙️ `POST /soletracao-palavras/audio`

> Recebe um áudio codificado em base64 (enviado pela tela web) e salva o arquivo localmente no backend.

**📥 Headers:** `Content-Type: application/json`

**📥 Corpo (JSON):**

| Campo          | Tipo     | Obrigatório | Descrição                                          |
| -------------- | -------- | ----------- | -------------------------------------------------- |
| `audio_base64` | `string` | ✅ sim      | Áudio em base64 (ex: `data:audio/webm;base64,...`) |
| `extensao`     | `string` | ❌ não      | Extensão do arquivo (padrão: `webm`)               |

**📤 Códigos de resposta:**

| Status | 🏷️   | Descrição                             |
| ------ | ----- | ------------------------------------- |
| `201`  | ✅    | Áudio salvo com sucesso               |
| `400`  | ❌    | JSON inválido ou base64 mal formado   |

**💻 Exemplo:**

```bash
curl -X POST http://127.0.0.1:8000/soletracao-palavras/audio \
  -H "Content-Type: application/json" \
  -d '{
    "audio_base64": "data:audio/webm;base64,GkXfo59ChoEBQv...",
    "extensao": "webm"
  }'
```

**✅ Resposta (`201`):**

```json
{
  "rota": "/soletracao-palavras/audio",
  "mensagem": "Audio recebido com sucesso",
  "audio": {
    "arquivo": "audio_20260330_150241_861975.webm",
    "arquivo_url": "/soletracao-palavras/audios/audio_20260330_150241_861975.webm"
  }
}
```

---

#### 🧠 `POST /soletracao-palavras/transcrever`

> Executa a transcrição do último áudio salvo. Atualmente opera em modo provisório (simulado).

**📥 Headers:** `Content-Type: application/json`

**📥 Corpo (JSON):** pode ser vazio (`{}`)

**📤 Resposta:**

| Campo              | Tipo     | Descrição                                         |
| ------------------ | -------- | ------------------------------------------------- |
| `rota`             | `string` | Rota chamada                                      |
| `modo`             | `string` | Modo de transcrição (`provisorio` ou `real`)       |
| `mensagem`         | `string` | Descrição do resultado                            |
| `audio`            | `object` | Informações do arquivo de áudio processado        |
| `texto_transcrito` | `string` | Texto resultante da transcrição                   |
| `texto_normalizado`| `string` | Texto normalizado (maiúsculas, sem acentos)       |
| `observacao`       | `string` | Notas adicionais sobre o modo de operação         |

**💻 Exemplo:**

```bash
curl -X POST http://127.0.0.1:8000/soletracao-palavras/transcrever \
  -H "Content-Type: application/json" \
  -d '{}'
```

**✅ Resposta:**

```json
{
  "rota": "/soletracao-palavras/transcrever",
  "modo": "provisorio",
  "mensagem": "Transcricao simulada com sucesso",
  "texto_transcrito": "oi",
  "texto_normalizado": "oi"
}
```

---

## 📊 Códigos de Status HTTP

Resumo dos códigos utilizados pela API:

| Status | 🏷️ Ícone | Significado                                           |
| ------ | --------- | ----------------------------------------------------- |
| `200`  | ✅        | Requisição bem-sucedida                               |
| `201`  | 🆕        | Recurso criado com sucesso (ex: áudio salvo)          |
| `400`  | ❌        | Requisição inválida (parâmetro ausente, JSON ruim)    |
| `404`  | 🔍        | Recurso não encontrado (arquivo, rota)                |
| `408`  | ⏱️        | Timeout no reconhecimento de letra                    |

---

## 🧪 Fluxos de Teste Recomendados

### 🚀 Fluxo 1 — Verificação rápida

> 🎯 **Objetivo:** confirmar que a API está rodando.

```bash
# 1️⃣ Subir a API
python api_server.py

# 2️⃣ Verificar resposta da raiz
curl http://127.0.0.1:8000/
```

---

### 🖥️ Fluxo 2 — Tela web interativa

> 🎯 **Objetivo:** testar soletração com GIFs e voz pelo navegador.

```bash
# 1️⃣ Subir a API
python api_server.py

# 2️⃣ Abrir a tela no navegador
# 🌐 http://127.0.0.1:8000/soletracao-palavras/tela

# 3️⃣ Digitar uma palavra ou usar os botões de voz
```

---

### 📝 Fluxo 3 — Soletração via API

> 🎯 **Objetivo:** testar a decomposição de texto em letras diretamente pela API.

```bash
# 1️⃣ Consultar a estrutura de soletração
curl "http://127.0.0.1:8000/soletracao-palavras?texto=oi%20tudo%20bem"

# 2️⃣ Iniciar uma sessão de reprodução
curl "http://127.0.0.1:8000/soletracao-palavras/iniciar?texto=oi%20tudo%20bem"

# 3️⃣ Consultar o progresso
curl http://127.0.0.1:8000/soletracao-palavras/status
```

---

### 🎙️ Fluxo 4 — Ciclo completo de áudio

> 🎯 **Objetivo:** enviar áudio, transcrever e soletrar.

```bash
# 1️⃣ Enviar áudio em base64
curl -X POST http://127.0.0.1:8000/soletracao-palavras/audio \
  -H "Content-Type: application/json" \
  -d '{"audio_base64": "data:audio/webm;base64,...", "extensao": "webm"}'

# 2️⃣ Transcrever o áudio salvo
curl -X POST http://127.0.0.1:8000/soletracao-palavras/transcrever \
  -H "Content-Type: application/json" \
  -d '{}'

# 3️⃣ Soletrar o texto transcrito
curl "http://127.0.0.1:8000/soletracao-palavras?texto=oi"
```

---

## 📋 Referência Rápida de Rotas

| 🔵 Método | 🛣️ Rota                                  | 📋 Descrição                        |
| --------- | ----------------------------------------- | ------------------------------------ |
| `GET`     | `/`                                       | 🏠 Status da API                    |
| `GET`     | `/alfabeto`                               | 🔤 Estado do modo alfabeto          |
| `GET`     | `/estado`                                 | 📊 Estado atual do hand tracking    |
| `GET`     | `/camera/iniciar`                         | 📷 Iniciar webcam                   |
| `GET`     | `/camera/parar`                           | 🛑 Parar webcam                     |
| `GET`     | `/camera/stream`                          | 🎥 Stream MJPEG da câmera           |
| `GET`     | `/teste/a`                                | 🧪 Teste da letra A                 |
| `GET`     | `/teste/letra/{letra}`                    | 🔤 Teste de letra específica        |
| `GET`     | `/soletracao-palavras?texto=...`          | 📝 Estrutura de soletração          |
| `GET`     | `/soletracao-palavras/iniciar?texto=...`  | ▶️ Iniciar sessão de soletração     |
| `GET`     | `/soletracao-palavras/status`             | ⏱️ Status da sessão                 |
| `GET`     | `/soletracao-palavras/tela`               | 🖥️ Tela HTML interativa             |
| `GET`     | `/soletracao-palavras/gifs/{arquivo}`     | 🖼️ Servir GIF de letra              |
| `GET`     | `/soletracao-palavras/audios/{arquivo}`   | 🔊 Servir arquivo de áudio          |
| `POST`    | `/soletracao-palavras/audio`              | 🎙️ Enviar áudio em base64           |
| `POST`    | `/soletracao-palavras/transcrever`        | 🧠 Transcrever último áudio         |

---

## ⚠️ Observações Técnicas

- ⚙️ O servidor utiliza `ThreadingHTTPServer` da stdlib do Python, permitindo múltiplas conexões simultâneas.
- 🔗 O fluxo de câmera e hand tracking reutiliza o módulo [`hand_tracking_service.py`](https://github.com/Natanael-Heinrick/libras-hand-tracking/blob/main/hand_tracking_service.py).
- 🚧 A transcrição de áudio no backend ainda opera em **modo provisório** (simulado). O fluxo mais completo de voz utiliza a tela web com reconhecimento de fala via browser (`Web Speech API`).
- 📁 Os GIFs de letras devem estar na pasta local configurada no servidor para que a rota `/soletracao-palavras/gifs/` funcione corretamente.

---

[⬅️ Voltar para o README principal](https://github.com/Natanael-Heinrick/libras-hand-tracking/blob/main/README.md)
