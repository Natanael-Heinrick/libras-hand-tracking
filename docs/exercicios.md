# 🎮 Modo Exercícios

[⬅️ Voltar para o README principal](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/README.md)

Este documento descreve o modo exercícios do projeto, que funciona via WebSocket e reaproveita o reconhecimento de letras por hand tracking.

## 📌 Visão Geral

O modo exercícios foi criado para treinar a soletração de palavras em LIBRAS com:

- palavra alvo
- dificuldade
- pontuação
- nível
- progressão automática
- seleção aleatória de palavras

Esse modo usa a webcam para detectar letras, e o usuário confirma cada letra manualmente até montar a palavra alvo.

## 🧱 Arquivos principais

- [websocket_server.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/websocket_server.py)
  Servidor WebSocket que expõe a rota `/exercicios`.
- [websocket_exercicios_client.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/websocket_exercicios_client.py)
  Cliente de teste com webcam e interface OpenCV.
- [exercicios_libras/service.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/exercicios_libras/service.py)
  Serviço com a lógica do jogo.
- [exercicios_libras/dados/palavras_libras_filtrado.csv](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/exercicios_libras/dados/palavras_libras_filtrado.csv)
  Base de palavras usada pelo modo exercícios.

## ▶️ Como executar

### Terminal 1

```powershell
python websocket_server.py
```

### Terminal 2

```powershell
python websocket_exercicios_client.py
```

## 🔌 Rota usada

Rota WebSocket:

```text
ws://127.0.0.1:8765/exercicios
```

## 🧾 Base de dados do jogo

Arquivo:

- [palavras_libras_filtrado.csv](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/exercicios_libras/dados/palavras_libras_filtrado.csv)

Estrutura atual do CSV:

- `palavra`
- `nivel`
- `tamanho`

### Exemplo de linhas

```csv
palavra,nivel,tamanho
oi,facil,2
pai,facil,3
mae,facil,3
```

### Como o CSV é usado

O serviço:

1. lê o arquivo CSV
2. normaliza as palavras
3. filtra por dificuldade
4. escolhe uma palavra alvo
5. controla a rodada atual

## 🕹️ Regras do modo exercícios

### Palavra alvo

- o sistema define uma palavra alvo
- o usuário precisa formar essa palavra letra por letra
- cada letra deve ser confirmada manualmente

### Dificuldades

Dificuldades aceitas:

- `facil`
- `medio`
- `dificil`

### Pontuação por dificuldade

- `facil`: 1 ponto
- `medio`: 2 pontos
- `dificil`: 3 pontos

### Nível

O nível é calculado automaticamente a partir da pontuação acumulada.

Regra atual:

```text
nivel = max(1, (pontuacao // 5) + 1)
```

### Progressão

Quando o usuário acerta:

- a pontuação é atualizada
- o nível pode subir
- a última palavra concluída é registrada
- uma nova palavra é carregada automaticamente

### Seleção de palavras

A seleção atual funciona assim:

- respeita a dificuldade selecionada
- escolhe uma palavra aleatória dentro daquele grupo
- evita repetir imediatamente a mesma palavra quando houver mais de uma opção

## 🧠 Estado interno do jogo

O serviço [exercicios_libras/service.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/exercicios_libras/service.py) mantém, entre outros, os seguintes campos:

- `target_word`
- `difficulty`
- `selected_difficulty`
- `score`
- `level`
- `completed`
- `last_completed_word`
- `last_feedback`
- `current_index`
- `filtered_words`

## 📨 Dados retornados no campo `exercicio`

Quando o cliente está conectado na rota `/exercicios`, o servidor devolve um objeto `exercicio`.

Campos principais:

- `modo`
- `palavra_alvo`
- `dificuldade`
- `dificuldade_selecionada`
- `tamanho_palavra`
- `pontos_por_acerto`
- `pontuacao`
- `nivel`
- `indice_palavra`
- `total_palavras`
- `total_palavras_csv`
- `palavra_usuario`
- `acertou`
- `ultima_palavra_concluida`
- `feedback`
- `fonte_dados`

### Exemplo

```json
{
  "modo": "exercicios",
  "palavra_alvo": "OI",
  "dificuldade": "facil",
  "dificuldade_selecionada": "facil",
  "tamanho_palavra": 2,
  "pontos_por_acerto": 1,
  "pontuacao": 3,
  "nivel": 1,
  "palavra_usuario": "OI",
  "acertou": true,
  "ultima_palavra_concluida": "OI",
  "feedback": "Acertou OI. Carregando a proxima palavra."
}
```

## ⌨️ Controles do cliente

No cliente [websocket_exercicios_client.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/websocket_exercicios_client.py):

- `ESPACO`: confirma a letra atual
- `C`: limpa a palavra atual
- `R`: reinicia a rodada atual
- `N`: avança manualmente para outra palavra
- `1`: define dificuldade `facil`
- `2`: define dificuldade `medio`
- `3`: define dificuldade `dificil`
- `ESC`: sai

## 🔁 Fluxo lógico da rodada

1. o cliente conecta na rota `/exercicios`
2. o servidor cria o estado do jogo
3. o sistema escolhe uma palavra alvo de acordo com a dificuldade atual
4. o usuário faz os gestos de cada letra
5. o cliente confirma cada letra com `ESPACO`
6. a palavra montada é comparada com a palavra alvo
7. se houver acerto:
   - soma pontos
   - recalcula nível
   - registra a última palavra
   - carrega uma nova palavra

## 🧪 Fluxos de teste recomendados

### Fluxo 1: teste básico de acerto

1. suba o servidor WebSocket
2. rode o cliente de exercícios
3. monte a palavra alvo atual
4. confirme as letras com `ESPACO`
5. verifique:
   - atualização da pontuação
   - atualização do feedback
   - mudança da palavra alvo

### Fluxo 2: teste de dificuldade

1. pressione `1`, `2` e `3`
2. observe a mudança de dificuldade
3. confira se os pontos por acerto mudam
4. veja se a palavra alvo muda para outra do mesmo grupo

### Fluxo 3: teste de progressão automática

1. acerte a palavra atual
2. confirme se o sistema:
   - registra a palavra concluída
   - avança automaticamente
   - mantém a dificuldade

### Fluxo 4: teste de sorteio

1. acerte várias palavras na mesma dificuldade
2. observe se as próximas palavras não seguem sempre a ordem fixa do CSV
3. confira se a mesma palavra não se repete imediatamente

## ⚠️ Observações técnicas

- o modo exercícios não implementa tentativas máximas ou vidas no estado atual
- o avanço manual com `N` existe como apoio de teste
- a escolha de palavras depende totalmente do CSV carregado
- se o CSV não existir, o sistema usa um fallback mínimo com a palavra `OI`

[⬅️ Voltar para o README principal](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/README.md)
