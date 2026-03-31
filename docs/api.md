# API HTTP

[Voltar para o README principal](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/README.md)

Este documento detalha o fluxo HTTP do projeto.

## Arquivo principal

- [api_server.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/api_server.py)

## Porta

- `http://127.0.0.1:8000`

## Rotas principais

- `GET /`
- `GET /alfabeto`
- `GET /estado`
- `GET /camera/iniciar`
- `GET /camera/parar`
- `GET /camera/stream`
- `GET /teste/a`
- `GET /teste/letra/A`
- `GET /soletracao-palavras?texto=oi`
- `GET /soletracao-palavras/iniciar?texto=oi`
- `GET /soletracao-palavras/status`
- `GET /soletracao-palavras/tela`
- `GET /soletracao-palavras/gifs/<arquivo>`
- `GET /soletracao-palavras/audios/<arquivo>`
- `POST /soletracao-palavras/audio`
- `POST /soletracao-palavras/transcrever`

## Observacao

Detalhamento maior pode ser expandido nos proximos blocos.
