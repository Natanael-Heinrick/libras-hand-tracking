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

## Bloco 4

- progressao automatica para a proxima palavra ao acertar
- registro da ultima palavra concluida
- manutencao de pontuacao e nivel entre rodadas
- opcao de avancar manualmente continua disponivel para teste

## Bloco 5

- selecao aleatoria de palavras dentro da dificuldade atual
- evita repetir imediatamente a mesma palavra quando houver mais de uma opcao
- mantem a dificuldade selecionada e o restante do progresso

## Objetivo do teste

Montar a palavra alvo com os gestos das letras e confirmar cada letra.
