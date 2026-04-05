import asyncio
import base64
import json

import cv2
from websockets.asyncio.client import connect


SERVER_URL = "ws://127.0.0.1:8765/alfabeto"


def encode_frame(frame, quality=70):
    ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise RuntimeError("Nao foi possivel codificar o frame")

    return base64.b64encode(buffer.tobytes()).decode("utf-8")


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

                encoded_frame = encode_frame(frame)
                await websocket.send(json.dumps({"frame": encoded_frame}))

                response = json.loads(await websocket.recv())
                estado = response.get("estado", {})

                letra = estado.get("letra_estavel") or estado.get("letra") or ""
                cv2.putText(
                    frame,
                    f"Letra: {letra}",
                    (30, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.2,
                    (0, 255, 0),
                    3,
                )

                palavra = estado.get("palavra", "")
                cv2.putText(
                    frame,
                    f"Palavra: {palavra}",
                    (30, 110),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (255, 0, 0),
                    2,
                )

                cv2.imshow("Cliente Hand Tracking", frame)
                key = cv2.waitKey(1) & 0xFF

                if key == ord(" "):
                    await websocket.send(json.dumps({"acao": "confirmar_letra"}))
                elif key == ord("c"):
                    await websocket.send(json.dumps({"acao": "limpar_palavra"}))
                elif key == 27:
                    break
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    asyncio.run(main())
