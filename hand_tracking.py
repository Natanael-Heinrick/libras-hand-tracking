import asyncio
import base64
import json
import subprocess
import threading

import cv2
from websockets.asyncio.client import connect


SERVER_URL = "ws://127.0.0.1:8765/alfabeto"


def encode_frame(frame, quality=70):
    ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise RuntimeError("Nao foi possivel codificar o frame")

    return base64.b64encode(buffer.tobytes()).decode("utf-8")


def falar_texto(texto):
    texto = (texto or "").strip()
    if not texto:
        return

    texto_seguro = texto.replace("'", "''")
    comando = (
        "Add-Type -AssemblyName System.Speech; "
        "$voz = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        f"$voz.Speak('{texto_seguro}')"
    )

    def _executar():
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", comando],
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

    threading.Thread(target=_executar, daemon=True).start()


async def main():
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not camera.isOpened():
        raise RuntimeError("Erro ao acessar webcam local")

    try:
        async with connect(SERVER_URL, max_size=2**22) as websocket:
            while True:
                ok, frame = camera.read()
                if not ok:
                    raise RuntimeError("Erro ao capturar frame da webcam")

                await websocket.send(json.dumps({"frame": encode_frame(frame)}))
                response = json.loads(await websocket.recv())

                if response.get("tipo") == "erro":
                    raise RuntimeError(response.get("mensagem", "Erro desconhecido do servidor"))

                estado = response.get("estado", {})
                letra = estado.get("letra_estavel") or estado.get("letra") or ""

                cv2.putText(
                    frame,
                    f"Rota: /alfabeto",
                    (30, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 255),
                    2,
                )
                cv2.putText(
                    frame,
                    f"Letra: {letra}",
                    (30, 75),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.2,
                    (0, 255, 0),
                    3,
                )
                cv2.putText(
                    frame,
                    f"Palavra: {estado.get('palavra', '')}",
                    (30, 120),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (255, 0, 0),
                    2,
                )
                cv2.putText(
                    frame,
                    "ESPACO confirma | C limpa | P fala",
                    (30, 160),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                )

                cv2.imshow("Hand Tracking - Alfabeto", frame)
                key = cv2.waitKey(1) & 0xFF

                if key == ord(" "):
                    await websocket.send(json.dumps({"acao": "confirmar_letra"}))
                    response = json.loads(await websocket.recv())
                    if response.get("tipo") == "erro":
                        raise RuntimeError(response.get("mensagem", "Erro ao confirmar letra"))
                elif key == ord("c"):
                    await websocket.send(json.dumps({"acao": "limpar_palavra"}))
                    response = json.loads(await websocket.recv())
                    if response.get("tipo") == "erro":
                        raise RuntimeError(response.get("mensagem", "Erro ao limpar palavra"))
                elif key == ord("p"):
                    falar_texto(estado.get("palavra", ""))
                elif key == 27:
                    break
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    asyncio.run(main())
