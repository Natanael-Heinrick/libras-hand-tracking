# 🔌 WebSocket

[⬅️ Voltar para o README principal](../README.md)

Este documento descreve o fluxo WebSocket do projeto, incluindo:

- servidor
- rotas
- clientes
- formato das mensagens
- ações suportadas
- exemplos de uso

## 📌 Visão Geral

Arquivo principal do servidor:

- [websocket_server.py](../websocket_server.py)

Endereço base:

```text
ws://127.0.0.1:8765
```

O servidor atende duas rotas:

- `ws://127.0.0.1:8765/alfabeto`
- `ws://127.0.0.1:8765/exercicios`

## ▶️ Como subir o servidor

No terminal:

```powershell
python websocket_server.py
```

Ao iniciar, ele libera as rotas de hand tracking em tempo real.

## 🧭 Rotas Disponíveis

### `ws://127.0.0.1:8765/alfabeto`

Rota usada para:

- reconhecimento de letras
- montagem manual de palavras
- limpeza da palavra montada

Cliente relacionado:

- [websocket_client.py](../websocket_client.py)

### `ws://127.0.0.1:8765/exercicios`

Rota usada para:

- jogo de soletração por LIBRAS
- validação de palavra alvo
- controle de dificuldade
- pontuação e nível

Cliente relacionado:

- [websocket_exercicios_client.py](../websocket_exercicios_client.py)

## 🧱 Componentes Envolvidos

### Servidor

- [websocket_server.py](../websocket_server.py)

### Processamento de mão

- [hand_tracking_service.py](../hand_tracking_service.py)
- [letter_classifier.py](../letter_classifier.py)
- [hand_geometry.py](../hand_geometry.py)

### Clientes

- [websocket_client.py](../websocket_client.py)
- [websocket_exercicios_client.py](../websocket_exercicios_client.py)

### Modo exercícios

- [exercicios_libras/service.py](../exercicios_libras/service.py)

## 📨 Formato Geral das Mensagens

O cliente envia mensagens JSON.

O servidor responde com JSON em dois formatos principais:

- `resultado`
- `erro`

### Resposta de sucesso

```json
{
  "tipo": "resultado",
  "estado": {
    "letra": "O",
    "letra_estavel": "O",
    "palavra": "OI",
    "maos_detectadas": 1,
    "deteccoes": []
  }
}
```

### Resposta de erro

```json
{
  "tipo": "erro",
  "mensagem": "Rota WebSocket nao suportada: /rota-invalida"
}
```

## 🎥 Envio de frame

### Finalidade

O frame da webcam é codificado em JPEG e enviado em base64 para o servidor.

### Formato enviado pelo cliente

```json
{
  "frame": "<frame_em_base64>"
}
```

### O que o servidor faz

1. decodifica o frame
2. processa a mão com `HandTrackingService`
3. classifica a letra atual
4. devolve o estado atualizado

## 🔤 Ações da rota `/alfabeto`

### 1. Confirmar letra

#### Envio

```json
{
  "acao": "confirmar_letra"
}
```

#### Efeito

- adiciona `letra_estavel` na palavra atual

### 2. Limpar palavra

#### Envio

```json
{
  "acao": "limpar_palavra"
}
```

#### Efeito

- limpa a palavra montada

## 🎮 Ações da rota `/exercicios`

Além das ações de alfabeto, a rota de exercícios também aceita ações específicas.

### 1. Confirmar letra

#### Envio

```json
{
  "acao": "confirmar_letra"
}
```

#### Efeito

- confirma a letra atual
- atualiza a palavra do usuário
- valida se acertou a palavra alvo
- soma pontos se houver acerto
- pode avançar automaticamente para a próxima palavra

### 2. Limpar palavra

#### Envio

```json
{
  "acao": "limpar_palavra"
}
```

#### Efeito

- limpa a palavra montada pelo usuário

### 3. Reiniciar exercício

#### Envio

```json
{
  "acao": "reiniciar_exercicio"
}
```

#### Efeito

- reinicia a rodada atual
- mantém pontuação, dificuldade e nível

### 4. Próxima palavra manual

#### Envio

```json
{
  "acao": "proxima_palavra"
}
```

#### Efeito

- força a troca manual da palavra alvo

### 5. Definir dificuldade

#### Envio

```json
{
  "acao": "definir_dificuldade",
  "dificuldade": "medio"
}
```

#### Valores aceitos

- `facil`
- `medio`
- `dificil`

#### Efeito

- troca o filtro de palavras do exercício
- atualiza a pontuação por acerto
- carrega uma nova palavra da dificuldade escolhida

## 🧾 Estrutura do campo `estado`

Campos comuns retornados no `estado`:

- `letra`
- `letra_estavel`
- `palavra`
- `maos_detectadas`
- `deteccoes`

### Exemplo

```json
{
  "letra": "I",
  "letra_estavel": "I",
  "palavra": "OI",
  "maos_detectadas": 1,
  "deteccoes": [
    {
      "dedos": [0, 0, 0, 0, 1],
      "letra_detectada": "I"
    }
  ]
}
```

## 🧾 Estrutura do campo `exercicio`

Quando a rota é `/exercicios`, o servidor também devolve um bloco `exercicio`.

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
  "pontuacao": 3,
  "nivel": 1,
  "palavra_usuario": "OI",
  "acertou": true,
  "feedback": "Acertou OI. Carregando a proxima palavra."
}
```

## 🖥️ Clientes de teste

### Cliente do modo alfabeto

Arquivo:

- [websocket_client.py](../websocket_client.py)

Como executar:

```powershell
python websocket_client.py
```

Controles:

- `ESPACO`: confirma a letra atual
- `C`: limpa a palavra
- `ESC`: sai

### Cliente do modo exercícios

Arquivo:

- [websocket_exercicios_client.py](../websocket_exercicios_client.py)

Como executar:

```powershell
python websocket_exercicios_client.py
```

Controles:

- `ESPACO`: confirma a letra atual
- `C`: limpa a palavra atual
- `R`: reinicia a rodada
- `N`: avança manualmente para outra palavra
- `1`: dificuldade fácil
- `2`: dificuldade média
- `3`: dificuldade difícil
- `ESC`: sai

## 🧪 Fluxos de teste recomendados

### Fluxo 1: modo alfabeto

1. Suba o servidor:

```powershell
python websocket_server.py
```

2. Em outro terminal, rode:

```powershell
python websocket_client.py
```

3. Faça um gesto de letra.
4. Confirme com `ESPACO`.
5. Veja a palavra sendo montada na tela.

### Fluxo 2: modo exercícios

1. Suba o servidor:

```powershell
python websocket_server.py
```

2. Em outro terminal, rode:

```powershell
python websocket_exercicios_client.py
```

3. Monte a palavra alvo com os gestos.
4. Confirme as letras com `ESPACO`.
5. Observe:

- pontuação
- nível
- dificuldade
- última palavra concluída
- próxima palavra escolhida

## ⚠️ Observações técnicas

- O servidor usa `websockets.asyncio.server.serve`.
- O processamento do frame acontece no servidor, não no cliente.
- O cliente apenas captura a webcam, codifica o frame e envia ao servidor.
- A rota `/exercicios` reutiliza a base de hand tracking e adiciona o estado do jogo.
- Rotas WebSocket inválidas devolvem uma mensagem de erro e fecham a conexão.

[⬅️ Voltar para o README principal](../README.md)//
