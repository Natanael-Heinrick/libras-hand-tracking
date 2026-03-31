# 🌐 API HTTP

[⬅️ Voltar para o README principal](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/README.md)

Este documento descreve a API HTTP do projeto, incluindo:

- rotas disponíveis
- métodos
- parâmetros
- respostas esperadas
- exemplos de uso

## 📌 Visão Geral

Arquivo principal da API:

- [api_server.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/api_server.py)

Endereço base:

```text
http://127.0.0.1:8000
```

A API atualmente atende dois contextos principais:

1. consulta e controle do fluxo de hand tracking
2. soletração por palavras com GIFs, áudio e tela web

## ▶️ Como subir a API

No terminal:

```powershell
python api_server.py
```

Quando o servidor subir, ele libera as rotas documentadas abaixo.

## 🧭 Índice de Rotas

### Rotas gerais

- `GET /`

### Rotas de hand tracking

- `GET /alfabeto`
- `GET /estado`
- `GET /camera/iniciar`
- `GET /camera/parar`
- `GET /camera/stream`
- `GET /teste/a`
- `GET /teste/letra/A`

### Rotas de soletração por palavras

- `GET /soletracao-palavras?texto=oi`
- `GET /soletracao-palavras/iniciar?texto=oi`
- `GET /soletracao-palavras/status`
- `GET /soletracao-palavras/tela`
- `GET /soletracao-palavras/gifs/<arquivo>`
- `GET /soletracao-palavras/audios/<arquivo>`
- `POST /soletracao-palavras/audio`
- `POST /soletracao-palavras/transcrever`

## 🏠 `GET /`

### Finalidade

Retorna uma resposta simples informando que a API está ativa e lista as principais rotas.

### Parâmetros

Nenhum.

### Resposta esperada

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

### Exemplo de uso

```text
http://127.0.0.1:8000/
```

## ✋ `GET /alfabeto`

### Finalidade

Consulta o estado atual do modo alfabeto, incluindo letras suportadas e estado da câmera.

### Parâmetros

Nenhum obrigatório.

### Resposta esperada

Campos principais:

- `rota`
- `letras_suportadas`
- `camera_ativa`
- `estado_atual`
- `observacao`
- `query_params_recebidos`

### Exemplo de uso

```text
http://127.0.0.1:8000/alfabeto
```

## 📊 `GET /estado`

### Finalidade

Retorna somente o estado atual detectado pelo serviço de hand tracking.

### Parâmetros

Nenhum.

### Resposta esperada

Campos comuns:

- `letra`
- `letra_estavel`
- `palavra`
- `maos_detectadas`
- `deteccoes`

### Exemplo de uso

```text
http://127.0.0.1:8000/estado
```

## 📷 `GET /camera/iniciar`

### Finalidade

Solicita a abertura da webcam pelo serviço.

### Parâmetros

Nenhum.

### Resposta esperada

```json
{
  "mensagem": "Webcam iniciada com sucesso",
  "camera_ativa": true
}
```

### Exemplo de uso

```text
http://127.0.0.1:8000/camera/iniciar
```

## 🛑 `GET /camera/parar`

### Finalidade

Encerra o uso da webcam pelo serviço.

### Parâmetros

Nenhum.

### Resposta esperada

```json
{
  "mensagem": "Webcam encerrada com sucesso",
  "camera_ativa": false
}
```

### Exemplo de uso

```text
http://127.0.0.1:8000/camera/parar
```

## 🎥 `GET /camera/stream`

### Finalidade

Abre um stream MJPEG da câmera processada.

### Parâmetros

Nenhum.

### Resposta esperada

- tipo de conteúdo `multipart/x-mixed-replace`
- frames JPEG em sequência

### Exemplo de uso

```text
http://127.0.0.1:8000/camera/stream
```

## 🧪 `GET /teste/a`

### Finalidade

Executa um teste específico para a letra `A`.

### Parâmetros

Nenhum.

### Resposta esperada

O retorno depende do reconhecimento:

- sucesso: status `200`
- timeout/falha: status `408`

### Exemplo de uso

```text
http://127.0.0.1:8000/teste/a
```

## 🔤 `GET /teste/letra/A`

### Finalidade

Executa um teste de reconhecimento para uma letra específica suportada.

### Parâmetros

Na própria rota:

- `A`, `C`, `D`, `E`, `F`, `G`, `I`, `J`, `K`, `M`, `N`, `O`, `P`, `R`, `S`, `T`, `U`, `V`

### Resposta esperada

- sucesso: status `200`
- timeout/falha: status `408`
- letra inválida: status `400`

### Exemplo de uso

```text
http://127.0.0.1:8000/teste/letra/O
```

## 📝 `GET /soletracao-palavras?texto=oi`

### Finalidade

Recebe um texto e devolve a estrutura de soletração por palavras e letras.

### Parâmetros

Query param obrigatório:

- `texto`

Exemplo:

- `?texto=oi`
- `?texto=oi tudo bem`

### Resposta esperada

Campos principais:

- `rota`
- `texto_original`
- `texto_normalizado`
- `palavras`
- `grupos_palavras`
- `letras`
- `sequencia`
- `status_atual`
- `proximo_status`

### Exemplo de resposta

```json
{
  "texto_original": "oi tudo bem",
  "texto_normalizado": "OITUDOBEM",
  "palavras": ["OI", "TUDO", "BEM"]
}
```

### Exemplo de uso

```text
http://127.0.0.1:8000/soletracao-palavras?texto=oi%20tudo%20bem
```

## ▶️ `GET /soletracao-palavras/iniciar?texto=oi`

### Finalidade

Inicia uma sessão de reprodução da soletração no backend.

### Parâmetros

Query param obrigatório:

- `texto`

### Resposta esperada

Campos principais:

- `session_id`
- `texto_original`
- `texto_normalizado`
- `palavras`
- `grupos_palavras`
- `fila`
- `duracao_item_ms`
- `duracao_pausa_ms`
- `status_atual`

### Exemplo de uso

```text
http://127.0.0.1:8000/soletracao-palavras/iniciar?texto=oi
```

## ⏱️ `GET /soletracao-palavras/status`

### Finalidade

Consulta o estado atual da sessão de reprodução da soletração.

### Parâmetros

Nenhum.

### Resposta esperada

Campos principais:

- `status_atual`
- `session_id`
- `palavras`
- `grupos_palavras`
- `fila`
- `item_atual`
- `indice_atual`
- `restante_ms_item`
- `finalizado`

### Exemplo de uso

```text
http://127.0.0.1:8000/soletracao-palavras/status
```

## 🖥️ `GET /soletracao-palavras/tela`

### Finalidade

Entrega a página HTML usada para testar o fluxo de soletração por voz e GIFs.

### Parâmetros

Nenhum.

### Resposta esperada

- conteúdo HTML

### Exemplo de uso

```text
http://127.0.0.1:8000/soletracao-palavras/tela
```

## 🖼️ `GET /soletracao-palavras/gifs/<arquivo>`

### Finalidade

Entrega um GIF da base local de letras.

### Parâmetros

Na própria rota:

- nome do arquivo GIF, por exemplo `O.gif`

### Resposta esperada

- conteúdo binário do GIF
- ou erro `404` se o arquivo não existir

### Exemplo de uso

```text
http://127.0.0.1:8000/soletracao-palavras/gifs/O.gif
```

## 🔊 `GET /soletracao-palavras/audios/<arquivo>`

### Finalidade

Entrega um áudio previamente salvo no backend.

### Parâmetros

Na própria rota:

- nome do arquivo de áudio

### Resposta esperada

- conteúdo binário do áudio
- ou erro `404`

### Exemplo de uso

```text
http://127.0.0.1:8000/soletracao-palavras/audios/audio_20260330_150241_861975.webm
```

## 🎙️ `POST /soletracao-palavras/audio`

### Finalidade

Recebe um áudio em base64 enviado pela tela web e salva o arquivo localmente.

### Corpo esperado

```json
{
  "audio_base64": "data:audio/webm;base64,...",
  "extensao": "webm"
}
```

### Parâmetros

No JSON:

- `audio_base64`: obrigatório
- `extensao`: opcional, padrão `webm`

### Resposta esperada

Status:

- `201` em caso de sucesso
- `400` em caso de erro de JSON ou base64 inválido

### Exemplo de resposta

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

## 🧠 `POST /soletracao-palavras/transcrever`

### Finalidade

Executa a transcrição provisória do último áudio salvo.

### Corpo esperado

Atualmente a rota aceita um JSON vazio:

```json
{}
```

### Resposta esperada

Campos principais:

- `rota`
- `modo`
- `mensagem`
- `audio`
- `texto_transcrito`
- `texto_normalizado`
- `observacao`

### Exemplo de resposta

```json
{
  "rota": "/soletracao-palavras/transcrever",
  "modo": "provisorio",
  "mensagem": "Transcricao simulada com sucesso",
  "texto_transcrito": "oi",
  "texto_normalizado": "oi"
}
```

## 🧪 Fluxos de teste recomendados

### Fluxo 1: teste rápido da API

1. Suba a API:

```powershell
python api_server.py
```

2. Acesse:

```text
http://127.0.0.1:8000/
```

### Fluxo 2: teste da tela web

1. Suba a API:

```powershell
python api_server.py
```

2. Abra:

```text
http://127.0.0.1:8000/soletracao-palavras/tela
```

3. Digite uma palavra ou use os botões de voz.

### Fluxo 3: teste direto de soletração

Exemplo:

```text
http://127.0.0.1:8000/soletracao-palavras?texto=oi%20tudo%20bem
```

## ⚠️ Observações técnicas

- O servidor usa `ThreadingHTTPServer`.
- O fluxo de câmera e hand tracking reaproveita [hand_tracking_service.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/hand_tracking_service.py).
- A transcrição do backend ainda é provisória.
- O fluxo mais completo de voz hoje usa a tela web e reconhecimento no navegador.

[⬅️ Voltar para o README principal](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/README.md)
