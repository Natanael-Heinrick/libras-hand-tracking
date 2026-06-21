# 🛠️ Instalação

[⬅️ Voltar para o README principal](../README.md)

Este guia apresenta os passos necessários para configurar e executar o projeto localmente.

## 📋 Pré-requisitos

Antes de iniciar, verifique se possui:

* Python 3.11 ou superior
* Sistema operacional Windows
* Webcam funcional
* Navegador moderno
* Acesso ao PowerShell ou Terminal

## 🐍 Verificar a versão do Python

Abra o terminal e execute:

```bash
python --version
```

Saída esperada:

```text
Python 3.11.x
```

## 📁 Criar o ambiente virtual

No diretório raiz do projeto:

```bash
python -m venv venv
```

## ▶️ Ativar o ambiente virtual

### PowerShell

```bash
.\venv\Scripts\Activate.ps1
```

### Git Bash

```bash
source venv/Scripts/activate
```

Quando ativado corretamente, o terminal exibirá:

```text
(venv)
```

## 📦 Instalar as dependências

Instale as bibliotecas necessárias:

```bash
pip install opencv-python mediapipe numpy websockets pywebview
```

## 📚 Bibliotecas Utilizadas

* `opencv-python`
* `mediapipe`
* `numpy`
* `websockets`
* `pywebview`

## ✅ Validar a instalação

Execute o teste abaixo:

```bash
@'
import cv2
import mediapipe
import numpy
import websockets
import webview

print("Ambiente configurado com sucesso")
'@ | python -
```

Resultado esperado:

```text
Ambiente configurado com sucesso
```

## 🎮 Executar o projeto

### Abrir o menu principal

```bash
python game_menu.py
```

O menu abrirá utilizando o PyWebView. Caso a biblioteca não esteja instalada, o sistema utilizará automaticamente a interface baseada em OpenCV.

### Iniciar o servidor WebSocket

```bash
python websocket_server.py
```

### Executar o modo Fotos

```bash
python websocket_exercicios_client.py fotos
```

### Executar o modo Palavras

```bash
python websocket_exercicios_client.py palavras
```

### Executar o modo Duelo

```bash
python websocket_duelo_client.py
```

### Executar o Quiz Visual

```bash
python -m quiz_visual_libras.quiz_visual_game
```

### Abrir a Loja

```bash
python -m loja.shop_app
```

## 📷 Testar a câmera

Para verificar se a webcam está funcionando corretamente:

```bash
python test_camera.py
```

## ⚠️ Problemas comuns

### O ambiente virtual não ativa

Execute no PowerShell como administrador:

```bash
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Em seguida:

```bash
.\venv\Scripts\Activate.ps1
```

### O menu não abre

Verifique se o `pywebview` está instalado:

```bash
pip install pywebview
```

### O WebSocket não conecta

Verifique se:

* `websocket_server.py` está em execução.
* A porta `8765` está disponível.
* O servidor foi iniciado antes do cliente.

### A câmera não abre

* Feche outros programas que utilizam a webcam.
* Teste utilizando:

```bash
python test_camera.py
```

* Verifique as permissões de câmera do sistema operacional.

## 📝 Observações

Recomenda-se gerar um arquivo `requirements.txt` para facilitar futuras instalações:

```bash
pip freeze > requirements.txt
```

Para instalar todas as dependências posteriormente:

```bash
pip install -r requirements.txt
```
