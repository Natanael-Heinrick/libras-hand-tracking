import asyncio
import base64
import json

import cv2
from websockets.asyncio.client import connect


SERVER_URL = "ws://127.0.0.1:8765/duelo"
WINDOW_NAME = "Duelo de Tempo LIBRAS"


def draw_text(canvas, text, position, scale=0.8, color=(255, 255, 255), thickness=2):
    cv2.putText(
        canvas,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        color,
        thickness,
        cv2.LINE_AA,
    )


def encode_frame(frame, quality=70):
    ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise RuntimeError("Nao foi possivel codificar o frame")

    return base64.b64encode(buffer.tobytes()).decode("utf-8")


def fmt_time(value):
    if value is None:
        return "--"
    return f"{value:.2f}s"


def draw_panel(frame, duelo, estado):
    player_color = tuple(duelo.get("jogador_atual_cor_bgr", [255, 255, 255]))
    draw_text(frame, "Rota: /duelo", (30, 35), scale=0.8)
    draw_text(frame, "Duelo de Tempo LIBRAS", (30, 75), scale=1.0, thickness=3)
    draw_text(frame, f"Palavra alvo: {duelo.get('palavra_alvo', '')}", (30, 120), scale=0.9, color=(0, 220, 255), thickness=2)
    draw_text(frame, f"Sua palavra: {estado.get('palavra', '')}", (30, 160), scale=0.9, color=(255, 255, 0), thickness=2)
    draw_text(frame, f"Letra atual: {estado.get('letra_estavel') or estado.get('letra') or ''}", (30, 200), scale=0.82, color=(180, 255, 180))
    draw_text(frame, f"Jogador atual: {duelo.get('jogador_atual_label', '')}", (30, 245), scale=0.95, color=player_color, thickness=3)
    draw_text(frame, f"Fase: {duelo.get('fase', '')}", (30, 285), scale=0.75, color=(210, 210, 210))
    draw_text(frame, f"Tempo atual: {fmt_time(duelo.get('tempo_atual'))}", (30, 325), scale=0.8)
    draw_text(frame, f"Tempo Oponente 1: {fmt_time(duelo.get('tempo_oponente_1'))}", (30, 365), scale=0.8, color=(255, 120, 0))
    draw_text(frame, f"Tempo Oponente 2: {fmt_time(duelo.get('tempo_oponente_2'))}", (30, 405), scale=0.8, color=(0, 140, 255))
    draw_text(frame, f"Tempo a bater: {fmt_time(duelo.get('tempo_a_bater'))}", (30, 445), scale=0.8, color=(140, 220, 255))
    draw_text(
        frame,
        f"Vidas: O1 {duelo.get('vidas_oponente_1', 0)}/{duelo.get('vidas_maximas', 0)} | O2 {duelo.get('vidas_oponente_2', 0)}/{duelo.get('vidas_maximas', 0)}",
        (30, 485),
        scale=0.76,
    )
    draw_text(frame, f"CSV: {duelo.get('fonte_dados', '')}", (30, 525), scale=0.58, color=(190, 230, 255))
    draw_text(frame, f"Palavras validas: {duelo.get('total_palavras_validas', 0)}", (30, 555), scale=0.7, color=(190, 230, 255))
    draw_text(frame, f"Feedback: {duelo.get('feedback', '')}", (30, 595), scale=0.67, color=(200, 255, 200))
    draw_text(frame, f"Troca: {duelo.get('mensagem_transicao', '')}", (30, 630), scale=0.62, color=(255, 220, 180))
    draw_text(frame, f"Resultado: {duelo.get('motivo_vitoria', '')}", (30, 655), scale=0.62, color=(255, 200, 200))
    draw_text(frame, "S inicia | ESPACO confirma letra | ENTER valida | C limpa", (30, 685), scale=0.56)
    draw_text(frame, "T troca jogador | N proxima palavra | R reinicia duelo | ESC sai", (30, 710), scale=0.56)


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
                duelo = response.get("duelo", {})
                draw_panel(frame, duelo, estado)

                cv2.imshow(WINDOW_NAME, frame)
                key = cv2.waitKey(1) & 0xFF

                if key == ord("s"):
                    await websocket.send(json.dumps({"acao": "iniciar_duelo"}))
                    response = json.loads(await websocket.recv())
                elif key == ord(" "):
                    await websocket.send(json.dumps({"acao": "confirmar_letra"}))
                    response = json.loads(await websocket.recv())
                elif key in (10, 13):
                    await websocket.send(json.dumps({"acao": "validar_palavra_duelo"}))
                    response = json.loads(await websocket.recv())
                elif key == ord("t"):
                    await websocket.send(json.dumps({"acao": "trocar_jogador_duelo"}))
                    response = json.loads(await websocket.recv())
                elif key == ord("n"):
                    await websocket.send(json.dumps({"acao": "proxima_palavra"}))
                    response = json.loads(await websocket.recv())
                elif key == ord("r"):
                    await websocket.send(json.dumps({"acao": "reiniciar_duelo"}))
                    response = json.loads(await websocket.recv())
                elif key == ord("c"):
                    await websocket.send(json.dumps({"acao": "limpar_palavra"}))
                    response = json.loads(await websocket.recv())
                elif key == 27:
                    break
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    asyncio.run(main())
