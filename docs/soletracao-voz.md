# 🎤 Soletracao por Voz

[⬅️ Voltar para o README principal](../README.md)

Este documento descreve o fluxo HTTP de soletração por voz, texto e GIFs.

## 📌 Visão Geral

O módulo de soletração por voz foi criado para:

- receber texto digitado ou reconhecido por voz
- separar o conteúdo por palavras e letras
- localizar os GIFs correspondentes
- reproduzir a sequência na tela

Esse fluxo usa uma API HTTP local e uma interface web simples.

## 🧱 Arquivos principais

- [api_server.py](../api_server.py)
  Servidor HTTP local.
- [soletracao_palavras/service.py](../soletracao_palavras/service.py)
  Lógica da soletração e controle de reprodução.
- [soletracao_palavras/audio_service.py](../soletracao_palavras/audio_service.py)
  Serviço responsável por salvar os áudios enviados.
- [soletracao_palavras/transcription_service.py](../soletracao_palavras/transcription_service.py)
  Serviço de transcrição provisória do backend.
- [soletracao_palavras/tela.html](../soletracao_palavras/tela.html)
  Tela web de teste.

## ▶️ Como executar

No terminal:

```powershell
python api_server.py
```

Depois, no navegador, abra:

```text
http://127.0.0.1:8000/soletracao-palavras/tela
```

## 🌐 Endereço base

```text
http://127.0.0.1:8000
```

## 🖥️ Tela principal

Interface principal:

- `http://127.0.0.1:8000/soletracao-palavras/tela`

Arquivo da interface:

- [soletracao_palavras/tela.html](../soletracao_palavras/tela.html)

## 🧩 Componentes do fluxo

### 1. Soletração de texto

Responsável por:

- normalizar o texto
- separar palavras
- separar letras
- montar grupos visuais por palavra
- mapear cada letra para um GIF local

Arquivo:

- [soletracao_palavras/service.py](../soletracao_palavras/service.py)

### 2. Controle de reprodução

Responsável por:

- iniciar uma sessão
- manter o estado `hold -> continue`
- avançar letra por letra
- inserir pausas entre palavras

Também implementado em:

- [soletracao_palavras/service.py](../soletracao_palavras/service.py)

### 3. Captura e persistência de áudio

Responsável por:

- receber áudio enviado pela tela
- salvar o arquivo localmente
- registrar o último áudio salvo

Arquivo:

- [soletracao_palavras/audio_service.py](../soletracao_palavras/audio_service.py)

### 4. Transcrição

Hoje existem dois caminhos:

#### A. Transcrição no navegador

É o caminho mais prático e o principal no estado atual do projeto.

A tela usa:

- `SpeechRecognition`
- `webkitSpeechRecognition`

#### B. Transcrição provisória no backend

Existe uma rota HTTP que responde com texto fixo de teste para validar a arquitetura ponta a ponta.

Arquivo:

- [soletracao_palavras/transcription_service.py](../soletracao_palavras/transcription_service.py)

## 🗂️ Recursos locais usados

### GIFs

Pasta:

- [soletracao_palavras/gifs](../soletracao_palavras/gifs)

Uso:

- um GIF por letra
- nomes como `O.gif`, `I.gif`, `A.gif`

### Áudios

Pasta:

- [soletracao_palavras/audios](../soletracao_palavras/audios)

Uso:

- armazena os áudios enviados pela tela

## 🔁 Fluxo lógico do sistema

### Fluxo 1: texto digitado

1. o usuário digita uma palavra ou frase
2. a tela envia o texto para a API
3. o backend separa palavras e letras
4. a tela exibe os GIFs em sequência

### Fluxo 2: áudio enviado ao backend

1. o usuário grava áudio na tela
2. a tela envia o áudio em base64
3. o backend salva o arquivo
4. a rota de transcrição provisória pode ser chamada
5. o texto resultante alimenta a soletração

### Fluxo 3: fala ao vivo no navegador

1. o usuário clica em `Falar e Mostrar`
2. o navegador captura a fala
3. o texto reconhecido preenche o campo
4. a tela dispara a soletração automaticamente
5. os GIFs são reproduzidos por palavra e letra

## 🧾 Estrutura de resposta da soletração

O serviço de soletração retorna, entre outros:

- `texto_original`
- `texto_normalizado`
- `palavras`
- `grupos_palavras`
- `letras`
- `sequencia`
- `status_atual`
- `proximo_status`

### Exemplo simplificado

```json
{
  "texto_original": "oi tudo bem",
  "texto_normalizado": "OITUDOBEM",
  "palavras": ["OI", "TUDO", "BEM"]
}
```

## ⏱️ Controle de reprodução

O estado da reprodução funciona assim:

- `hold`: ainda está exibindo letras ou pausas
- `continue`: terminou a sequência atual

Também existem:

- duração por letra
- duração de pausa entre palavras
- status consultável por rota HTTP

## 🎛️ Controles da tela web

Na interface [soletracao_palavras/tela.html](../soletracao_palavras/tela.html), o usuário pode:

- digitar texto e clicar em `Mostrar`
- gravar áudio
- parar gravação
- enviar áudio
- transcrever no backend
- transcrever e mostrar
- usar reconhecimento de fala do navegador com:
  - `Falar e Mostrar`
  - `So Transcrever`

## 🧪 Fluxos de teste recomendados

### Fluxo 1: teste por texto

1. suba a API:

```powershell
python api_server.py
```

2. abra:

```text
http://127.0.0.1:8000/soletracao-palavras/tela
```

3. digite:

```text
oi tudo bem
```

4. clique em `Mostrar`

5. verifique:

- separação por palavras
- destaque letra por letra
- pausas entre palavras

### Fluxo 2: teste com voz no navegador

1. abra a tela web
2. clique em `Falar e Mostrar`
3. fale uma frase curta
4. verifique:

- texto reconhecido
- preenchimento do input
- início automático da reprodução

### Fluxo 3: teste com gravação e envio de áudio

1. clique em `Gravar audio`
2. fale algo curto
3. clique em `Parar gravacao`
4. clique em `Enviar audio`
5. confirme se o arquivo foi salvo em:

- [soletracao_palavras/audios](../soletracao_palavras/audios)

### Fluxo 4: teste da transcrição provisória

1. envie um áudio
2. clique em `Transcrever`
3. verifique se o campo recebe o texto de teste retornado pelo backend

## ⚠️ Observações técnicas

- o fluxo de transcrição mais útil hoje é o do navegador
- a transcrição do backend ainda é provisória
- a reprodução depende da existência dos GIFs no diretório local
- se um GIF não existir, ele não entra na fila de reprodução
- a tela já organiza frases em blocos por palavra, não apenas em letras soltas

[⬅️ Voltar para o README principal](../README.md)
