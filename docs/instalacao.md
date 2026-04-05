# 🛠️ Instalação

[⬅️ Voltar para o README principal](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/README.md)

Este documento reúne os passos para preparar o ambiente e executar o projeto localmente.

## 📋 Pré-requisitos

Antes de instalar, verifique se você possui:

- Python 3.11 ou superior
- Windows com PowerShell
- webcam funcional
- navegador moderno para o fluxo HTTP
- Chrome ou Edge para melhor suporte ao reconhecimento de fala no navegador

## 🐍 Verificar versão do Python

No terminal:

```powershell
python --version
```

Resultado esperado:

```text
Python 3.11.x
```

## 📁 Estrutura esperada

O projeto utiliza:

- ambiente virtual local em `venv/`
- cache Python em `__pycache__/`

O `.gitignore` atual já ignora:

- `venv/`
- `__pycache__/`
- `*.pyc`

## 🔧 Criar o ambiente virtual

No diretório raiz do projeto:

```powershell
python -m venv venv
```

## ▶️ Ativar o ambiente virtual

No PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Se o ambiente estiver ativo corretamente, o terminal normalmente passa a exibir algo como:

```text
(venv)
```

## 📦 Instalar dependências

Instale as bibliotecas principais com:

```powershell
pip install opencv-python mediapipe numpy websockets
```

## 📚 Bibliotecas utilizadas

Dependências principais:

- `opencv-python`
- `mediapipe`
- `numpy`
- `websockets`

## ✅ Validar a instalação

Depois da instalação, você pode validar rapidamente se o ambiente está pronto.

### Teste 1: importar bibliotecas

```powershell
@'
import cv2
import mediapipe
import numpy
import websockets
print("Ambiente OK")
'@ | python -
```

Resultado esperado:

```text
Ambiente OK
```

### Teste 2: testar webcam

```powershell
python test_camera.py
```

Se abrir a webcam corretamente, o ambiente está apto para os fluxos com câmera.

## 🚀 Próximos passos após instalar

Depois da instalação, você pode seguir um dos fluxos abaixo.

### Fluxo HTTP de soletração por voz

```powershell
python api_server.py
```

Depois abra:

```text
http://127.0.0.1:8000/soletracao-palavras/tela
```

### Fluxo WebSocket do modo alfabeto

Terminal 1:

```powershell
python websocket_server.py
```

Terminal 2:

```powershell
python websocket_client.py
```

Observacao:

- o cliente do alfabeto conecta na rota `ws://127.0.0.1:8765/alfabeto`
- se a URL ficar apenas como `ws://127.0.0.1:8765`, o servidor fecha a conexao normalmente e o cliente pode mostrar `ConnectionClosedOK`

### Fluxo WebSocket do modo exercícios

Terminal 1:

```powershell
python websocket_server.py
```

Terminal 2:

```powershell
python websocket_exercicios_client.py
```

## ⚠️ Problemas comuns

### 1. O PowerShell bloqueia a ativação do ambiente virtual

Se ocorrer erro de política de execução, você pode abrir o PowerShell como administrador e ajustar a política para o usuário atual:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Depois tente ativar novamente:

```powershell
.\venv\Scripts\Activate.ps1
```

### 2. A webcam não abre

Tente:

- fechar outros aplicativos que estejam usando a câmera
- testar com [test_camera.py](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/test_camera.py)
- verificar permissões da câmera no Windows

### 3. O navegador não reconhece voz

Recomendações:

- usar Chrome ou Edge
- permitir acesso ao microfone
- testar o fluxo em:

```text
http://127.0.0.1:8000/soletracao-palavras/tela
```

### 4. O WebSocket não conecta

Verifique se:

- `websocket_server.py` está rodando antes do cliente
- a porta `8765` está livre
- você está usando a rota correta

### 5. A API HTTP não responde

Verifique se:

- `api_server.py` está rodando
- a porta `8000` está livre
- você acessou a URL correta no navegador

## 📝 Observações

- O projeto ainda não possui `requirements.txt`
- Atualmente a instalação é feita manualmente via `pip install`
- Como melhoria futura, vale gerar um `requirements.txt` para padronizar o ambiente

[⬅️ Voltar para o README principal](/c:/Users/Natanael/OneDrive/Desktop/hand-tracking-project/README.md)
