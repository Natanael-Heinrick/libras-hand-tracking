# Voz Para LIBRAS

Este documento descreve a base da futura trilha:

`voz -> texto -> glosa/estrutura -> avatar LIBRAS`

## Objetivo

Criar uma nova camada do projeto que receba fala em portugues, converta para texto, adapte o conteudo para uma representacao mais adequada para LIBRAS e envie comandos para um avatar.

## Fluxo proposto

1. Captura de audio
2. Transcricao de fala para texto
3. Interpretacao do texto em glosas ou estrutura intermediaria
4. Geracao de comandos para avatar
5. Renderizacao do avatar

## Estrutura inicial

- `voice_to_libras/models.py`
- `voice_to_libras/speech_pipeline.py`
- `voice_to_libras/gloss_mapper.py`
- `voice_to_libras/avatar_bridge.py`

## Observacoes

- Esta base e apenas um esqueleto arquitetural.
- Nenhuma traducao real para LIBRAS foi implementada aqui ainda.
- A camada atual de reconhecimento de letras continua independente.
