# Soletracao de Palavras

Esta pasta guarda a base local de GIFs usada pela rota `/soletracao-palavras`.

## Estrutura

- `gifs/`: "banco de dados" local com um GIF por letra
- `audios/`: audios enviados pela tela durante os testes
- `service.py`: monta a sequencia de letras e resolve os caminhos dos GIFs

## Convencao dos arquivos

Salve os GIFs com o nome exato da letra em maiusculo:

- `O.gif`
- `I.gif`

Exemplo de teste:

- texto enviado: `oi`
- retorno esperado: `["O", "I"]`

## Captura de audio

- a tela de teste permite gravar audio pelo navegador
- os arquivos enviados ficam em `audios/`
- a rota usada para salvar e `POST /soletracao-palavras/audio`

## Transcricao provisoria

- a rota `POST /soletracao-palavras/transcrever` usa o ultimo audio salvo
- por enquanto ela devolve um texto fixo de teste para validar o fluxo
- o objetivo e trocar depois so o miolo pela transcricao real
