# Validacao de Maos e Sinais

[Voltar para o README principal](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/README.md)

Este documento abre a nova trilha do projeto dedicada a validacao de maos e ao reconhecimento progressivo de sinais em LIBRAS.

## Principio Central

- visao = reconhecer
- temporal = estabilizar
- LLM = explicar, validar e orientar

## Roadmap

### Bloco A: Dataset

Objetivo:

- construir um dataset especifico de maos e sinais para LIBRAS

Escopo:

- coletar fotos e frames de video
- variar iluminacao, fundo, distancia, angulo, pessoas e lateralidade da mao
- organizar por classe ou sinal
- definir padrao de nome e anotacao

Entregaveis:

- estrutura de pastas do dataset
- convencao de labels
- primeira base anotada
- conjunto de treino, validacao e teste

Criterio de sucesso:

- dataset limpo, balanceado e reutilizavel

### Bloco B: Visao Base

Objetivo:

- manter o MediaPipe como base do pipeline de visao

Escopo:

- detectar landmarks da mao
- extrair features geometricas
- manter o pipeline atual funcionando
- melhorar robustez da captura e do pre-processamento

Entregaveis:

- pipeline estavel de extracao de landmarks
- features por frame
- ferramenta para inspecionar landmarks e classes

Criterio de sucesso:

- frames bem detectados de forma consistente

### Bloco C: Reconhecimento

Objetivo:

- transformar a visao em reconhecimento real de sinais

Escopo:

- comparar regras geometricas, classificador tradicional e modelo leve supervisionado
- treinar com o dataset
- validar por classe
- medir acuracia, precisao e confusao entre sinais

Entregaveis:

- primeiro classificador funcional
- metricas de validacao
- relatorio dos erros mais comuns

Criterio de sucesso:

- reconhecer sinais com estabilidade acima do baseline atual

### Bloco D: Temporal

Objetivo:

- usar sequencia de frames para reduzir ruido

Escopo:

- janela temporal
- suavizacao de predicao
- confirmacao por estabilidade
- transicao entre sinais
- deteccao de inicio e fim do gesto

Entregaveis:

- reconhecedor temporal
- reducao de falsos positivos
- saida mais estavel em tempo real

Criterio de sucesso:

- menos oscilacoes e melhor desempenho em video real

### Bloco E: Producao Real

Objetivo:

- garantir funcionamento fora do ambiente de teste

Escopo:

- validar com webcam ao vivo
- testar cenarios reais
- medir latencia e robustez

Entregaveis:

- fluxo em tempo real validado
- checklist de desempenho real
- lista de limitacoes praticas

Criterio de sucesso:

- funcionamento aceitavel em uso real com webcam

### Bloco F: Gloss e Linguagem

Objetivo:

- criar uma camada intermediaria entre reconhecimento e interpretacao

Escopo:

- montar gloss base
- tratar sequencia de sinais
- mapear reconhecimento bruto para unidades linguisticas

Entregaveis:

- camada intermediaria entre visao e linguagem
- representacao padronizada da saida

Criterio de sucesso:

- saida compreensivel para outras camadas do sistema

### Bloco G: LLM como Camada Auxiliar

Objetivo:

- usar LLM para explicar, validar e orientar, sem substituir a visao

Escopo:

- explicar o que foi reconhecido
- validar consistencia
- orientar correcoes
- apoiar feedback pedagogico

Entregaveis:

- interface entre reconhecedor e LLM
- prompts iniciais de explicacao, validacao e orientacao

Criterio de sucesso:

- LLM agrega clareza sem comprometer a precisao

### Bloco H: LLM Multimodal

Objetivo:

- usar multimodal apenas depois da base de visao estar madura

Escopo:

- analisar casos ambiguos
- comparar gesto esperado e executado
- enriquecer explicacoes visuais

Entregaveis:

- prova de conceito multimodal
- comparacao entre visao tradicional e apoio multimodal

Criterio de sucesso:

- multimodal ajuda nos casos dificeis sem virar dependencia central

## Relacao com o Codigo Atual

- `hand_tracking_service.py` e o pipeline online atual
- `letter_classifier.py` e o baseline por regras
- `voice_to_libras/gloss_mapper.py` antecipa o futuro Bloco F
- a nova pasta `validacao_maos/` concentra dados, artefatos e scripts dessa trilha

## Proximo Passo Recomendado

Comecar pelo Bloco A com uma primeira rodada pequena, controlada e bem anotada de coleta para 3 a 5 classes.

[Voltar para o README principal](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/README.md)
