import asyncio
import base64
import json

import cv2
from websockets.asyncio.client import connect


SERVER_URL = "ws://127.0.0.1:8765/exercicios"


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

                await websocket.send(json.dumps({"frame": encode_frame(frame)}))
                response = json.loads(await websocket.recv())

                if response.get("tipo") == "erro":
                    raise RuntimeError(response.get("mensagem", "Erro desconhecido do servidor"))

                estado = response.get("estado", {})
                exercicio = response.get("exercicio", {})
                letra = estado.get("letra_estavel") or estado.get("letra") or ""

                cv2.putText(frame, "Rota: /exercicios", (30, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                cv2.putText(frame, f"Letra: {letra}", (30, 75), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 0), 3)
                cv2.putText(
                    frame,
                    f"Sua palavra: {estado.get('palavra', '')}",
                    (30, 115),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (255, 255, 0),
                    2,
                )
                cv2.putText(
                    frame,
                    f"Alvo: {exercicio.get('palavra_alvo', '')}",
                    (30, 155),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 200, 255),
                    2,
                )
                cv2.putText(
                    frame,
                    f"Pontos: {exercicio.get('pontuacao', 0)} | Nivel: {exercicio.get('nivel', 1)} | {exercicio.get('dificuldade', '')}",
                    (30, 195),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                )
                cv2.putText(
                    frame,
                    f"Feedback: {exercicio.get('feedback', '')}",
                    (30, 235),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (200, 255, 200),
                    2,
                )
                cv2.putText(
                    frame,
                    f"CSV: {exercicio.get('indice_palavra', 0) + 1}/{exercicio.get('total_palavras', 0)}",
                    (30, 265),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 220, 180),
                    2,
                )
                cv2.putText(
                    frame,
                    "ESPACO confirma | C limpa | R reinicia | N proxima | ESC sai",
                    (30, 300),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                )

                if exercicio.get("acertou"):
                    cv2.putText(
                        frame,
                        "ACERTOU!",
                        (30, 345),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.2,
                        (0, 255, 0),
                        3,
                    )

                cv2.imshow("Hand Tracking - Exercicios", frame)
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
                elif key == ord("r"):
                    await websocket.send(json.dumps({"acao": "reiniciar_exercicio"}))
                    response = json.loads(await websocket.recv())
                    if response.get("tipo") == "erro":
                        raise RuntimeError(response.get("mensagem", "Erro ao reiniciar exercicio"))
                elif key == ord("n"):
                    await websocket.send(json.dumps({"acao": "proxima_palavra"}))
                    response = json.loads(await websocket.recv())
                    if response.get("tipo") == "erro":
                        raise RuntimeError(response.get("mensagem", "Erro ao avancar palavra"))
                elif key == 27:
                    break
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    asyncio.run(main())
