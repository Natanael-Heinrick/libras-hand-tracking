# Exercicios LIBRAS

Base inicial do modo exercicio via WebSocket.

## Bloco 1

- rota WebSocket: `/exercicios`
- palavra alvo fixa: `OI`
- dificuldade inicial: `facil`
- pontuacao por acerto: `1`

## Bloco 2

- leitura do CSV `dados/palavras_libras_filtrado.csv`
- carregamento inicial da palavra `OI` quando ela existir no arquivo
- suporte para avancar manualmente para a proxima palavra durante o teste

## Bloco 3

- filtro de palavras por dificuldade
- pontuacao por dificuldade:
  - `facil`: 1
  - `medio`: 2
  - `dificil`: 3
- nivel calculado a partir da pontuacao
- troca manual de dificuldade durante o teste

## Objetivo do teste

Montar a palavra alvo com os gestos das letras e confirmar cada letra.
