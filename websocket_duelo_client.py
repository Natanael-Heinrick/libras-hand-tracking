import asyncio
import base64
import json

import cv2
import numpy as np
from websockets.asyncio.client import connect


SERVER_URL = "ws://127.0.0.1:8765/duelo"
WINDOW_NAME = "Duelo de Tempo LIBRAS"
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
CAMERA_WIDTH = 760
PANEL_X = 790
PANEL_WIDTH = 460
COLOR_BG = (20, 26, 38)
COLOR_PANEL = (28, 37, 54)
COLOR_BORDER = (105, 160, 235)
COLOR_TEXT = (245, 248, 255)
COLOR_MUTED = (184, 198, 220)
COLOR_ACCENT = (96, 224, 255)
COLOR_SUCCESS = (145, 235, 165)
COLOR_WARNING = (130, 190, 255)
COLOR_DANGER = (160, 180, 255)
PLAYER_ONE_COLOR = (255, 120, 0)
PLAYER_TWO_COLOR = (0, 140, 255)


def draw_text(canvas, text, position, scale=0.8, color=COLOR_TEXT, thickness=2):
    cv2.putText(
        canvas,
        str(text),
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        color,
        thickness,
        cv2.LINE_AA,
    )


def draw_card(canvas, top_left, bottom_right, title, border_color=COLOR_BORDER):
    x1, y1 = top_left
    x2, y2 = bottom_right
    cv2.rectangle(canvas, (x1, y1), (x2, y2), COLOR_PANEL, -1)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), border_color, 2)
    draw_text(canvas, title, (x1 + 18, y1 + 32), scale=0.68, color=(230, 236, 255), thickness=2)


def draw_lives(canvas, label, current, max_lives, start_x, y, color):
    draw_text(canvas, label, (start_x, y), scale=0.62, color=color, thickness=2)
    x = start_x
    for index in range(max_lives):
        filled = index < current
        fill_color = color if filled else (80, 90, 110)
        cv2.circle(canvas, (x + 18, y + 34), 10, fill_color, -1)
        cv2.circle(canvas, (x + 18, y + 34), 10, (235, 240, 248), 1)
        x += 30


def wrap_text(text, max_chars=34):
    words = (text or "").split()
    if not words:
        return []

    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def encode_frame(frame, quality=70):
    ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise RuntimeError("Nao foi possivel codificar o frame")

    return base64.b64encode(buffer.tobytes()).decode("utf-8")


def fmt_time(value):
    if value is None:
        return "--"
    return f"{value:.2f}s"


def get_phase_label(phase):
    labels = {
        "aguardando_inicio": "Aguardando inicio",
        "jogando": "Rodada em andamento",
        "troca_jogador": "Troca de jogador",
        "resultado": "Resultado da rodada",
    }
    return labels.get(phase, phase or "")


def create_layout(frame):
    resized = cv2.resize(frame, (CAMERA_WIDTH, FRAME_HEIGHT))
    canvas = np.full((FRAME_HEIGHT, FRAME_WIDTH, 3), COLOR_BG, dtype=np.uint8)
    canvas[:, :CAMERA_WIDTH] = resized

    # Gradient overlay over the camera view for readability.
    overlay = canvas.copy()
    cv2.rectangle(overlay, (0, 0), (CAMERA_WIDTH, 120), (12, 18, 30), -1)
    cv2.rectangle(overlay, (0, FRAME_HEIGHT - 140), (CAMERA_WIDTH, FRAME_HEIGHT), (12, 18, 30), -1)
    cv2.addWeighted(overlay, 0.25, canvas, 0.75, 0, canvas)

    cv2.rectangle(canvas, (CAMERA_WIDTH, 0), (FRAME_WIDTH, FRAME_HEIGHT), (16, 22, 34), -1)
    cv2.rectangle(canvas, (CAMERA_WIDTH + 6, 14), (FRAME_WIDTH - 14, FRAME_HEIGHT - 14), (40, 56, 84), 2)
    return canvas


def draw_header(canvas, duelo, estado):
    player_color = tuple(duelo.get("jogador_atual_cor_bgr", [255, 255, 255]))
    draw_text(canvas, "Duelo de Tempo LIBRAS", (28, 54), scale=1.0, thickness=3)
    draw_text(canvas, f"Palavra alvo: {duelo.get('palavra_alvo', '')}", (28, 95), scale=0.82, color=COLOR_ACCENT)
    draw_text(canvas, f"Sua palavra: {estado.get('palavra', '') or '_'}", (28, 132), scale=0.88, color=(255, 240, 120), thickness=2)
    draw_text(canvas, f"Jogador atual: {duelo.get('jogador_atual_label', '')}", (28, 170), scale=0.78, color=player_color, thickness=3)


def draw_right_panel(canvas, duelo, estado):
    phase = duelo.get("fase", "")
    player_color = tuple(duelo.get("jogador_atual_cor_bgr", [255, 255, 255]))

    draw_card(canvas, (PANEL_X, 26), (1248, 116), "STATUS DA RODADA", border_color=player_color)
    draw_text(canvas, get_phase_label(phase), (PANEL_X + 18, 72), scale=0.85, color=player_color, thickness=3)
    draw_text(canvas, f"Letra atual: {estado.get('letra_estavel') or estado.get('letra') or '--'}", (PANEL_X + 18, 103), scale=0.68, color=COLOR_SUCCESS)

    draw_card(canvas, (PANEL_X, 136), (1248, 280), "PLACAR")
    draw_text(canvas, "Oponente 1", (PANEL_X + 18, 177), scale=0.72, color=PLAYER_ONE_COLOR, thickness=3)
    draw_text(canvas, fmt_time(duelo.get("tempo_oponente_1")), (PANEL_X + 270, 178), scale=0.9, color=PLAYER_ONE_COLOR, thickness=3)
    draw_lives(canvas, "Vidas", duelo.get("vidas_oponente_1", 0), duelo.get("vidas_maximas", 0), PANEL_X + 18, 190, PLAYER_ONE_COLOR)

    draw_text(canvas, "Oponente 2", (PANEL_X + 18, 238), scale=0.72, color=PLAYER_TWO_COLOR, thickness=3)
    draw_text(canvas, fmt_time(duelo.get("tempo_oponente_2")), (PANEL_X + 270, 239), scale=0.9, color=PLAYER_TWO_COLOR, thickness=3)
    draw_lives(canvas, "Vidas", duelo.get("vidas_oponente_2", 0), duelo.get("vidas_maximas", 0), PANEL_X + 18, 251, PLAYER_TWO_COLOR)

    draw_card(canvas, (PANEL_X, 300), (1248, 414), "CRONOMETRO")
    draw_text(canvas, "Tempo atual", (PANEL_X + 18, 343), scale=0.62, color=COLOR_MUTED)
    draw_text(canvas, fmt_time(duelo.get("tempo_atual")), (PANEL_X + 18, 388), scale=1.2, color=COLOR_TEXT, thickness=3)
    draw_text(canvas, "Tempo a bater", (PANEL_X + 242, 343), scale=0.62, color=COLOR_MUTED)
    draw_text(canvas, fmt_time(duelo.get("tempo_a_bater")), (PANEL_X + 242, 388), scale=1.0, color=COLOR_WARNING, thickness=3)

    draw_card(canvas, (PANEL_X, 434), (1248, 586), "MENSAGENS")
    feedback_lines = wrap_text(duelo.get("feedback", ""), max_chars=37)
    for index, line in enumerate(feedback_lines[:3]):
        draw_text(canvas, line, (PANEL_X + 18, 476 + index * 28), scale=0.62, color=COLOR_SUCCESS)

    transition_lines = wrap_text(duelo.get("mensagem_transicao", ""), max_chars=37)
    for index, line in enumerate(transition_lines[:2]):
        draw_text(canvas, line, (PANEL_X + 18, 553 + index * 24), scale=0.58, color=(255, 220, 170))

    draw_card(canvas, (PANEL_X, 606), (1248, 694), "CONTROLES")
    draw_text(canvas, "S inicia  |  ESPACO confirma  |  ENTER valida", (PANEL_X + 18, 647), scale=0.56, color=COLOR_TEXT)
    draw_text(canvas, "T troca  |  N nova palavra  |  R reinicia  |  C limpa", (PANEL_X + 18, 676), scale=0.56, color=COLOR_TEXT)

    draw_text(canvas, f"CSV: {duelo.get('fonte_dados', '')}", (PANEL_X, 714), scale=0.5, color=(150, 170, 205))


def draw_phase_overlay(canvas, duelo):
    phase = duelo.get("fase", "")
    if phase == "jogando":
        return

    if phase == "aguardando_inicio":
        title = "Rodada pronta"
        subtitle = "Pressione S para iniciar o tempo do Oponente 1"
        accent = tuple(duelo.get("jogador_atual_cor_bgr", [255, 255, 255]))
    elif phase == "troca_jogador":
        title = "Troca de jogador"
        subtitle = duelo.get("mensagem_transicao", "") or "Pressione T para iniciar a vez do Oponente 2"
        accent = PLAYER_TWO_COLOR
    else:
        winner = duelo.get("vencedor_label") or "Empate"
        title = f"Resultado: {winner}"
        subtitle = duelo.get("motivo_vitoria", "") or "Pressione N para nova palavra"
        accent = COLOR_SUCCESS if duelo.get("vencedor") else COLOR_WARNING

    overlay = canvas.copy()
    cv2.rectangle(overlay, (100, 180), (730, 520), (10, 14, 24), -1)
    cv2.addWeighted(overlay, 0.7, canvas, 0.3, 0, canvas)
    cv2.rectangle(canvas, (100, 180), (730, 520), accent, 3)
    draw_text(canvas, title, (135, 255), scale=1.2, color=accent, thickness=3)

    y = 320
    for line in wrap_text(subtitle, max_chars=34)[:3]:
        draw_text(canvas, line, (135, y), scale=0.76, color=COLOR_TEXT)
        y += 40

    if phase == "resultado":
        draw_text(
            canvas,
            f"O1: {fmt_time(duelo.get('tempo_oponente_1'))}   O2: {fmt_time(duelo.get('tempo_oponente_2'))}",
            (135, 445),
            scale=0.8,
            color=COLOR_ACCENT,
            thickness=2,
        )
    elif phase == "troca_jogador":
        draw_text(canvas, "Pressione T para liberar a vez do Oponente 2", (135, 445), scale=0.72, color=PLAYER_TWO_COLOR, thickness=2)
    else:
        draw_text(canvas, "Use a mesma camera e prepare o primeiro jogador", (135, 445), scale=0.72, color=COLOR_MUTED)


def draw_panel(frame, duelo, estado):
    canvas = create_layout(frame)
    draw_header(canvas, duelo, estado)
    draw_right_panel(canvas, duelo, estado)
    draw_phase_overlay(canvas, duelo)
    return canvas


async def send_action(websocket, action):
    await websocket.send(json.dumps({"acao": action}))
    return json.loads(await websocket.recv())


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
                canvas = draw_panel(frame, duelo, estado)

                cv2.imshow(WINDOW_NAME, canvas)
                key = cv2.waitKey(1) & 0xFF

                if key == ord("s"):
                    response = await send_action(websocket, "iniciar_duelo")
                elif key == ord(" "):
                    response = await send_action(websocket, "confirmar_letra")
                elif key in (10, 13):
                    response = await send_action(websocket, "validar_palavra_duelo")
                elif key == ord("t"):
                    response = await send_action(websocket, "trocar_jogador_duelo")
                elif key == ord("n"):
                    response = await send_action(websocket, "proxima_palavra")
                elif key == ord("r"):
                    response = await send_action(websocket, "reiniciar_duelo")
                elif key == ord("c"):
                    response = await send_action(websocket, "limpar_palavra")
                elif key == 27:
                    break
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    asyncio.run(main())
