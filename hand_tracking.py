import asyncio
import base64
import json
import subprocess
import threading

import cv2
import numpy as np
from websockets.asyncio.client import connect


SERVER_URL = "ws://127.0.0.1:8765/alfabeto"


def draw_text_block(image, lines, start_x, start_y, line_height=28, scale=0.62, color=(255, 255, 255), thickness=2):
    y = start_y
    for line in lines:
        cv2.putText(
            image,
            str(line),
            (start_x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            color,
            thickness,
        )
        y += line_height


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
                deteccao = (estado.get("deteccoes") or [{}])[0]
                dedos = deteccao.get("dedos", [])
                metricas_debug = deteccao.get("metricas_debug", {})

                frame = cv2.resize(frame, (960, 720))
                painel = np.full((720, 520, 3), (22, 28, 40), dtype=np.uint8)
                canvas = np.hstack((frame, painel))

                draw_text_block(
                    canvas,
                    [
                        "Rota: /alfabeto",
                        f"Letra atual: {estado.get('letra', '')}",
                        f"Letra estavel: {letra}",
                        f"Palavra: {estado.get('palavra', '')}",
                        f"Maos detectadas: {estado.get('maos_detectadas', 0)}",
                        f"Dedos: {dedos}",
                        "",
                        "Metricas C/P/Q",
                    ],
                    990,
                    40,
                    line_height=34,
                    scale=0.72,
                )

                metric_lines = [
                    f"{chave}: {valor}"
                    for chave, valor in metricas_debug.items()
                ]
                draw_text_block(
                    canvas,
                    metric_lines[:10],
                    990,
                    315,
                    line_height=28,
                    scale=0.6,
                    color=(200, 255, 200),
                )
                draw_text_block(
                    canvas,
                    [
                        "",
                        "Controles",
                        "ESPACO confirma",
                        "C limpa",
                        "P fala",
                        "ESC sai",
                    ],
                    990,
                    620,
                    line_height=26,
                    scale=0.58,
                    color=(255, 220, 180),
                )

                cv2.imshow("Hand Tracking - Alfabeto", canvas)
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
