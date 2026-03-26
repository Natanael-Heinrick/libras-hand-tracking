import asyncio
import base64
import json

import cv2
import numpy as np
from websockets.asyncio.server import serve

from hand_tracking_service import HandTrackingService


HOST = "127.0.0.1"
PORT = 8765


def decode_frame(frame_base64):
    frame_bytes = base64.b64decode(frame_base64)
    buffer = np.frombuffer(frame_bytes, dtype=np.uint8)
    frame = cv2.imdecode(buffer, cv2.IMREAD_COLOR)

    if frame is None:
        raise ValueError("Nao foi possivel decodificar o frame recebido")

    return frame


def get_websocket_path(websocket):
    request = getattr(websocket, "request", None)
    if request is not None and hasattr(request, "path"):
        return request.path

    return getattr(websocket, "path", "")


def build_state_payload(service, maos_detectadas=0, deteccoes=None):
    return {
        "letra": service.letra,
        "letra_estavel": service.letra_estavel,
        "palavra": service.palavra,
        "maos_detectadas": maos_detectadas,
        "deteccoes": deteccoes or [],
    }


async def handle_connection(websocket):
    path = get_websocket_path(websocket)

    if path != "/alfabeto":
        await websocket.send(
            json.dumps(
                {
                    "tipo": "erro",
                    "mensagem": f"Rota WebSocket nao suportada: {path}",
                },
                ensure_ascii=False,
            )
        )
        await websocket.close()
        return

    service = HandTrackingService()
    print(f"Cliente conectado em {path}")

    try:
        async for message in websocket:
            try:
                payload = json.loads(message)
                action = payload.get("acao")

                if action == "confirmar_letra":
                    service.confirm_letter()
                    state = build_state_payload(service)
                elif action == "limpar_palavra":
                    service.clear_word()
                    state = build_state_payload(service)
                else:
                    frame_base64 = payload["frame"]
                    frame = decode_frame(frame_base64)
                    state, _ = service.process_frame(frame, draw_landmarks=False)

                await websocket.send(
                    json.dumps(
                        {
                            "tipo": "resultado",
                            "estado": state,
                        },
                        ensure_ascii=False,
                    )
                )
            except Exception as exc:
                await websocket.send(
                    json.dumps(
                        {
                            "tipo": "erro",
                            "mensagem": str(exc),
                        },
                        ensure_ascii=False,
                    )
                )
    finally:
        service.close()
        print(f"Cliente desconectado de {path}")


async def main():
    async with serve(handle_connection, HOST, PORT, max_size=2**22):
        print(f"WebSocket ativo em ws://{HOST}:{PORT}")
        print("Rota disponivel: ws://127.0.0.1:8765/alfabeto")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
