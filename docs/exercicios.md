# 🎮 Modo Exercícios — Libras Hand Tracking

[⬅️ Voltar para o README principal](https://github.com/Natanael-Heinrick/libras-hand-tracking/blob/main/README.md)

> 📖 Este documento descreve o **modo exercícios** do projeto, que funciona via WebSocket e reaproveita o reconhecimento de letras por hand tracking para criar um **jogo de soletração em LIBRAS**.

---

## 📑 Sumário

- [📌 Visão Geral](#-visão-geral)
- [🧱 Arquivos Principais](#-arquivos-principais)
- [▶️ Como Executar](#️-como-executar)
- [🔌 Rota WebSocket](#-rota-websocket)
- [🗄️ Base de Dados do Jogo](#️-base-de-dados-do-jogo)
- [🕹️ Regras do Modo Exercícios](#️-regras-do-modo-exercícios)
- [🧠 Estado Interno do Jogo](#-estado-interno-do-jogo)
- [📨 Dados Retornados (`exercicio`)](#-dados-retornados-exercicio)
- [⌨️ Controles do Cliente](#️-controles-do-cliente)
- [🔁 Fluxo Lógico da Rodada](#-fluxo-lógico-da-rodada)
- [🧪 Fluxos de Teste Recomendados](#-fluxos-de-teste-recomendados)
- [⚠️ Observações Técnicas](#️-observações-técnicas)

---

## 📌 Visão Geral

O modo exercícios foi criado para **treinar a soletração de palavras em LIBRAS** usando a webcam. O sistema funciona como um jogo com:

| 🎯 Feature                  | 📋 Descrição                                              |
| ---------------------------- | ---------------------------------------------------------- |
| 🔤 Palavra alvo              | O sistema define uma palavra que o usuário deve soletrar   |
| 📊 Dificuldade               | Três níveis: `facil`, `medio`, `dificil`                   |
| 🏆 Pontuação                 | Pontos são acumulados a cada acerto                        |
| 📈 Nível                     | Calculado automaticamente com base na pontuação            |
| 🔄 Progressão automática     | Nova palavra é carregada ao acertar                        |
| 🎲 Seleção aleatória         | Palavras são escolhidas aleatoriamente sem repetição imediata |

> 💡 O usuário faz gestos em LIBRAS na webcam e confirma cada letra **manualmente** até montar a palavra alvo.

---

## 🧱 Arquivos Principais

| 📄 Arquivo                                        | 🎯 Função                                     |
| ------------------------------------------------- | ---------------------------------------------- |
| `websocket_server.py`                             | 🔌 Servidor WebSocket — expõe a rota `/exercicios` |
| `websocket_exercicios_client.py`                  | 🎮 Cliente de teste com webcam e interface OpenCV |
| `exercicios_libras/service.py`                    | 🧠 Serviço com a lógica do jogo                |
| `exercicios_libras/dados/palavras_libras_filtrado.csv` | 🗄️ Base de palavras usada pelo modo exercícios |

---

## ▶️ Como Executar

> ⚠️ É necessário abrir **dois terminais** simultaneamente.

### 1️⃣ Terminal 1 — Servidor

```bash
python websocket_server.py
```

### 2️⃣ Terminal 2 — Cliente

```bash
python websocket_exercicios_client.py
```

> 💡 O servidor deve estar rodando **antes** de iniciar o cliente.

---

## 🔌 Rota WebSocket

| 🏷️ Item        | 📋 Valor                          |
| --------------- | --------------------------------- |
| **🛣️ Rota**     | `/exercicios`                     |
| **🌍 Endereço** | `ws://127.0.0.1:8765/exercicios`  |
| **📡 Protocolo**| WebSocket                         |

---

## 🗄️ Base de Dados do Jogo

### 📄 Arquivo

`exercicios_libras/dados/palavras_libras_filtrado.csv`

### 📊 Estrutura do CSV

| Coluna    | Tipo     | Descrição                              |
| --------- | -------- | -------------------------------------- |
| `palavra` | `string` | Palavra a ser soletrada                |
| `nivel`   | `string` | Dificuldade (`facil`, `medio`, `dificil`) |
| `tamanho` | `integer`| Quantidade de letras na palavra        |

### 📝 Exemplo de linhas

```csv
palavra,nivel,tamanho
oi,facil,2
pai,facil,3
mae,facil,3
```

### 🔄 Como o CSV é usado

```
📄 CSV
  │
  │ 1️⃣ Lê o arquivo
  ▼
🔤 Normaliza as palavras (maiúsculas, sem acentos)
  │
  │ 2️⃣ Filtra por dificuldade
  ▼
🎯 Grupo de palavras filtradas
  │
  │ 3️⃣ Escolhe palavra alvo (aleatória)
  ▼
🎮 Controla a rodada atual
```

---

## 🕹️ Regras do Modo Exercícios

### 🎯 Palavra alvo

- O sistema define uma **palavra alvo** para o jogador
- O usuário precisa formar essa palavra **letra por letra**
- Cada letra deve ser **confirmada manualmente** (tecla `ESPAÇO`)

### 📊 Dificuldades

| 🏷️ Dificuldade | 🔤 Valor     | 🏆 Pontos por acerto |
| --------------- | ------------ | --------------------- |
| 🟢 Fácil        | `facil`      | **1 ponto**           |
| 🟡 Médio        | `medio`      | **2 pontos**          |
| 🔴 Difícil      | `dificil`    | **3 pontos**          |

### 📈 Cálculo do Nível

O nível é calculado **automaticamente** a partir da pontuação acumulada:

```
📈 nivel = max(1, (pontuacao // 5) + 1)
```

| 🏆 Pontuação | 📈 Nível |
| ------------- | -------- |
| 0 – 4         | 1        |
| 5 – 9         | 2        |
| 10 – 14       | 3        |
| 15 – 19       | 4        |
| ...           | ...      |

### 🔄 Progressão (ao acertar)

Quando o usuário **acerta a palavra**:

| # | 🎯 Ação                                              |
|---|-------------------------------------------------------|
| 1 | 🏆 Pontuação é atualizada                             |
| 2 | 📈 Nível pode subir                                   |
| 3 | 📝 Última palavra concluída é registrada               |
| 4 | 🔄 Nova palavra é carregada automaticamente            |

### 🎲 Seleção de palavras

| 🎯 Regra                                                    |
| ------------------------------------------------------------ |
| ✅ Respeita a dificuldade selecionada                        |
| 🎲 Escolhe uma palavra **aleatória** dentro do grupo          |
| 🚫 Evita repetir a mesma palavra imediatamente (quando possível) |

---

## 🧠 Estado Interno do Jogo

O serviço `exercicios_libras/service.py` mantém os seguintes campos internos:

| 🏷️ Campo                | Tipo      | 📋 Descrição                                |
| ------------------------ | --------- | ------------------------------------------- |
| `target_word`            | `string`  | 🎯 Palavra alvo atual                       |
| `difficulty`             | `string`  | 📊 Dificuldade da palavra atual              |
| `selected_difficulty`    | `string`  | 📊 Dificuldade selecionada pelo usuário      |
| `score`                  | `integer` | 🏆 Pontuação acumulada                      |
| `level`                  | `integer` | 📈 Nível atual                              |
| `completed`              | `boolean` | ✅ Se a palavra foi completada               |
| `last_completed_word`    | `string`  | 📝 Última palavra concluída                  |
| `last_feedback`          | `string`  | 💬 Último feedback exibido                   |
| `current_index`          | `integer` | 🔢 Índice da letra atual sendo formada       |
| `filtered_words`         | `list`    | 📋 Lista de palavras filtradas por dificuldade |

---

## 📨 Dados Retornados (`exercicio`)

Quando o cliente está conectado na rota `/exercicios`, o servidor devolve um objeto `exercicio` junto com o estado do hand tracking.

### 📤 Campos do objeto `exercicio`

| Campo                      | Tipo      | 📋 Descrição                                   |
| -------------------------- | --------- | ---------------------------------------------- |
| `modo`                     | `string`  | 🎮 Modo atual (`exercicios`)                   |
| `palavra_alvo`             | `string`  | 🎯 Palavra que o usuário deve montar            |
| `dificuldade`              | `string`  | 📊 Dificuldade da palavra atual                 |
| `dificuldade_selecionada`  | `string`  | 📊 Dificuldade escolhida pelo usuário           |
| `tamanho_palavra`          | `integer` | 🔢 Número de letras da palavra alvo             |
| `pontos_por_acerto`        | `integer` | 🏆 Pontos que serão ganhos ao acertar           |
| `pontuacao`                | `integer` | 🏆 Pontuação total acumulada                    |
| `nivel`                    | `integer` | 📈 Nível atual do jogador                       |
| `indice_palavra`           | `integer` | 🔢 Índice da palavra dentro do grupo filtrado   |
| `total_palavras`           | `integer` | 📋 Total de palavras no grupo atual             |
| `total_palavras_csv`       | `integer` | 📋 Total de palavras no CSV completo            |
| `palavra_usuario`          | `string`  | 🔤 Palavra montada até agora pelo usuário       |
| `acertou`                  | `boolean` | ✅ Se a palavra foi acertada                    |
| `ultima_palavra_concluida` | `string`  | 📝 Última palavra completada com sucesso        |
| `feedback`                 | `string`  | 💬 Mensagem de feedback para o jogador          |
| `fonte_dados`              | `string`  | 🗄️ Origem dos dados (CSV ou fallback)           |

### 💻 Exemplo de resposta

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

---

## ⌨️ Controles do Cliente

Teclas disponíveis no cliente `websocket_exercicios_client.py`:

| ⌨️ Tecla    | 🎯 Ação                              |
| ----------- | ------------------------------------- |
| `ESPAÇO`    | ✅ Confirma a letra atual             |
| `C`         | 🗑️ Limpa a palavra atual              |
| `R`         | 🔄 Reinicia a rodada atual            |
| `N`         | ⏭️ Avança para outra palavra           |
| `1`         | 🟢 Define dificuldade `facil`         |
| `2`         | 🟡 Define dificuldade `medio`         |
| `3`         | 🔴 Define dificuldade `dificil`       |
| `ESC`       | 🚪 Sai do programa                    |

---

## 🔁 Fluxo Lógico da Rodada

```
🎮 Cliente conecta em /exercicios
    │
    │ 1️⃣ Servidor cria estado do jogo
    ▼
🎯 Sistema escolhe palavra alvo (conforme dificuldade)
    │
    │ 2️⃣ Usuário faz gestos
    ▼
📷 Webcam captura os gestos
    │
    │ 3️⃣ Servidor reconhece a letra
    ▼
🔤 Letra detectada é exibida
    │
    │ 4️⃣ Usuário confirma com ESPAÇO
    ▼
📝 Letra é adicionada à palavra do usuário
    │
    │ 5️⃣ Compara com a palavra alvo
    ▼
┌─────────────────────────────────────┐
│ ✅ Acertou?                         │
├──────────┬──────────────────────────┤
│ ✅ SIM   │ ❌ NÃO (continua)       │
│          │                          │
│ 🏆 +pts  │ 🔤 Aguarda mais letras  │
│ 📈 nível │                          │
│ 📝 salva │                          │
│ 🔄 nova  │                          │
└──────────┴──────────────────────────┘
```

---

## 🧪 Fluxos de Teste Recomendados

### 🧪 Fluxo 1 — Teste básico de acerto

> 🎯 **Objetivo:** verificar se o acerto funciona corretamente.

| # | 📋 Passo                                              |
|---|--------------------------------------------------------|
| 1 | 🔌 Suba o servidor WebSocket                          |
| 2 | 🎮 Rode o cliente de exercícios                       |
| 3 | 🔤 Monte a palavra alvo atual (gesto por gesto)       |
| 4 | ✅ Confirme as letras com `ESPAÇO`                    |
| 5 | 🔍 Verifique:                                         |

**✅ Verificações:**

| 🔍 O que verificar                     |
| --------------------------------------- |
| 🏆 Pontuação foi atualizada            |
| 💬 Feedback de acerto apareceu         |
| 🔄 Palavra alvo mudou para uma nova    |

---

### 📊 Fluxo 2 — Teste de dificuldade

> 🎯 **Objetivo:** verificar se a troca de dificuldade funciona.

| # | 📋 Passo                                              |
|---|--------------------------------------------------------|
| 1 | ⌨️ Pressione `1`, `2` e `3` alternadamente            |
| 2 | 👀 Observe a mudança de dificuldade                   |
| 3 | 🏆 Confira se os pontos por acerto mudam              |
| 4 | 🔤 Veja se a palavra alvo muda para outra do grupo    |

---

### 🔄 Fluxo 3 — Teste de progressão automática

> 🎯 **Objetivo:** verificar se a progressão funciona após o acerto.

| # | 📋 Passo                                              |
|---|--------------------------------------------------------|
| 1 | ✅ Acerte a palavra atual                              |
| 2 | 🔍 Confirme se o sistema:                             |

**✅ Verificações:**

| 🔍 O que verificar                               |
| ------------------------------------------------- |
| 📝 Registra a palavra concluída                   |
| ⏭️ Avança automaticamente para nova palavra       |
| 📊 Mantém a dificuldade selecionada               |

---

### 🎲 Fluxo 4 — Teste de sorteio

> 🎯 **Objetivo:** verificar se as palavras são escolhidas aleatoriamente.

| # | 📋 Passo                                              |
|---|--------------------------------------------------------|
| 1 | ✅ Acerte várias palavras na mesma dificuldade         |
| 2 | 👀 Observe se as próximas palavras **não seguem** a ordem do CSV |
| 3 | 🔍 Confira se a mesma palavra **não se repete** imediatamente |

---

## ⚠️ Observações Técnicas

- 🚫 O modo exercícios **não implementa** tentativas máximas ou vidas no estado atual.
- 🧪 O avanço manual com `N` existe como **apoio de teste** — não é para uso final.
- 📋 A escolha de palavras depende **totalmente do CSV** carregado.
- 🛡️ Se o CSV não existir, o sistema usa um **fallback mínimo** com a palavra `OI`.

---

[⬅️ Voltar para o README principal](https://github.com/Natanael-Heinrick/libras-hand-tracking/blob/main/README.md)
