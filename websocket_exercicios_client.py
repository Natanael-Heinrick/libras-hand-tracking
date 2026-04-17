import asyncio
import base64
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from websockets.asyncio.client import connect


SERVER_URL = "ws://127.0.0.1:8765/exercicios"
PROJECT_ROOT = Path(__file__).resolve().parent
CHALLENGE_WINDOW = "Desafio por Imagem"
WINDOW_NAME = "Hand Tracking - Exercicios"
FRAME_WIDTH = 1460
FRAME_HEIGHT = 820
CAMERA_WIDTH = 860
PANEL_X = 890
PANEL_WIDTH = 540
COLOR_BG = (17, 24, 36)
COLOR_PANEL = (29, 38, 56)
COLOR_BORDER = (95, 155, 235)
COLOR_TEXT = (245, 248, 255)
COLOR_MUTED = (180, 196, 220)
COLOR_ACCENT = (100, 225, 255)
COLOR_SUCCESS = (150, 240, 170)
COLOR_WARNING = (125, 195, 255)
COLOR_GOLD = (105, 220, 255)


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


def draw_text_right(canvas, text, x_right, baseline_y, scale=0.8, color=COLOR_TEXT, thickness=2):
    text = str(text)
    (text_width, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
    draw_text(canvas, text, (x_right - text_width, baseline_y), scale=scale, color=color, thickness=thickness)


def draw_card(canvas, top_left, bottom_right, title="", border_color=COLOR_BORDER):
    x1, y1 = top_left
    x2, y2 = bottom_right
    cv2.rectangle(canvas, (x1, y1), (x2, y2), COLOR_PANEL, -1)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), border_color, 2)
    if title:
        draw_text(canvas, title, (x1 + 18, y1 + 30), scale=0.58, color=(230, 236, 255), thickness=2)


def encode_frame(frame, quality=70):
    ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise RuntimeError("Nao foi possivel codificar o frame")

    return base64.b64encode(buffer.tobytes()).decode("utf-8")


def close_challenge_window():
    try:
        cv2.destroyWindow(CHALLENGE_WINDOW)
    except cv2.error:
        pass


def draw_hint_overlay(image, hint_text):
    overlay = image.copy()
    cv2.rectangle(overlay, (10, 10), (overlay.shape[1] - 10, 74), (35, 45, 75), -1)
    cv2.addWeighted(overlay, 0.78, image, 0.22, 0, image)
    draw_text(image, f"Dica: {hint_text}", (20, 50), scale=0.63, color=(220, 235, 255), thickness=2)


def wrap_text(text, max_chars=42):
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


def get_initial_game_mode():
    valid_modes = {"fotos", "palavras", "misto"}
    if len(sys.argv) < 2:
        return "misto"

    selected_mode = (sys.argv[1] or "").strip().lower()
    return selected_mode if selected_mode in valid_modes else "misto"


def fit_image(image, max_width, max_height):
    height, width = image.shape[:2]
    scale = min(max_width / max(width, 1), max_height / max(height, 1))
    size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return cv2.resize(image, size)


def create_layout(frame):
    camera_view = cv2.resize(frame, (CAMERA_WIDTH, FRAME_HEIGHT))
    canvas = np.full((FRAME_HEIGHT, FRAME_WIDTH, 3), COLOR_BG, dtype=np.uint8)
    canvas[:, :CAMERA_WIDTH] = camera_view

    overlay = canvas.copy()
    cv2.rectangle(overlay, (0, 0), (CAMERA_WIDTH, 160), (11, 18, 30), -1)
    cv2.rectangle(overlay, (0, FRAME_HEIGHT - 170), (CAMERA_WIDTH, FRAME_HEIGHT), (11, 18, 30), -1)
    cv2.addWeighted(overlay, 0.28, canvas, 0.72, 0, canvas)

    cv2.rectangle(canvas, (CAMERA_WIDTH, 0), (FRAME_WIDTH, FRAME_HEIGHT), (16, 22, 34), -1)
    cv2.rectangle(canvas, (CAMERA_WIDTH + 8, 14), (FRAME_WIDTH - 14, FRAME_HEIGHT - 14), (38, 54, 82), 2)
    return canvas


def draw_camera_header(canvas, estado, exercicio, modo_jogo):
    tipo_desafio = exercicio.get("tipo_desafio", "palavra")
    modo_label = {
        "fotos": "Modo Fotos",
        "palavras": "Modo Palavras",
        "misto": "Modo Misto",
    }.get(modo_jogo, "Modo Livre")
    prompt = "Adivinhe o nome da imagem" if tipo_desafio == "imagem" else "Soletracao por palavra alvo"

    draw_text(canvas, "Desafio de LIBRAS", (28, 56), scale=1.0, thickness=3)
    draw_text(canvas, modo_label, (28, 98), scale=0.76, color=COLOR_GOLD, thickness=2)
    draw_text(canvas, prompt, (28, 136), scale=0.72, color=COLOR_ACCENT, thickness=2)
    draw_text(canvas, f"Sua palavra: {estado.get('palavra', '') or '_'}", (28, 178), scale=0.88, color=(255, 242, 120), thickness=2)
    draw_text(canvas, f"Letra atual: {estado.get('letra_estavel') or estado.get('letra') or '--'}", (28, 216), scale=0.76, color=COLOR_SUCCESS, thickness=2)


def draw_right_panel(canvas, exercicio, estado, modo_jogo, show_hint):
    tipo_desafio = exercicio.get("tipo_desafio", "palavra")
    card_right = PANEL_X + PANEL_WIDTH
    split_x = PANEL_X + 275
    border_color = COLOR_GOLD if tipo_desafio == "imagem" else COLOR_BORDER

    draw_card(canvas, (PANEL_X, 26), (card_right, 170), "DESAFIO", border_color=border_color)
    if tipo_desafio == "imagem":
        draw_text(canvas, "Objeto/Imagem", (PANEL_X + 18, 68), scale=0.64, color=COLOR_GOLD, thickness=2)
        draw_text(canvas, "Descubra a palavra pela imagem exibida", (PANEL_X + 18, 102), scale=0.54, color=COLOR_TEXT)
        draw_text(canvas, f"Dica: {'ON' if show_hint else 'OFF'}", (PANEL_X + 18, 138), scale=0.56, color=COLOR_WARNING)
    else:
        draw_text(canvas, "Palavra alvo", (PANEL_X + 18, 68), scale=0.64, color=COLOR_ACCENT, thickness=2)
        draw_text(canvas, exercicio.get("palavra_alvo", ""), (PANEL_X + 18, 114), scale=0.98, color=COLOR_TEXT, thickness=3)
        draw_text(canvas, "Sem imagem nesta rodada", (PANEL_X + 18, 146), scale=0.5, color=COLOR_MUTED)

    draw_card(canvas, (PANEL_X, 190), (card_right, 310), "PROGRESSO")
    draw_text(canvas, "Pontos", (PANEL_X + 18, 234), scale=0.54, color=COLOR_MUTED)
    draw_text(canvas, str(exercicio.get("pontuacao", 0)), (PANEL_X + 18, 280), scale=1.02, color=COLOR_TEXT, thickness=3)
    draw_text(canvas, "Nivel", (split_x, 234), scale=0.54, color=COLOR_MUTED)
    draw_text(canvas, str(exercicio.get("nivel", 1)), (split_x, 280), scale=1.02, color=COLOR_TEXT, thickness=3)
    draw_text(canvas, f"Dificuldade: {exercicio.get('dificuldade', '')}", (PANEL_X + 18, 302), scale=0.52, color=COLOR_GOLD)

    draw_card(canvas, (PANEL_X, 330), (card_right, 470), "RODADA")
    draw_text(canvas, "Modo", (PANEL_X + 18, 374), scale=0.54, color=COLOR_MUTED)
    draw_text(canvas, modo_jogo, (PANEL_X + 18, 418), scale=0.72, color=COLOR_TEXT, thickness=2)
    draw_text(canvas, "Desafio", (split_x, 374), scale=0.54, color=COLOR_MUTED)
    draw_text(
        canvas,
        f"{exercicio.get('indice_palavra', 0) + 1}/{exercicio.get('total_palavras', 0)}",
        (split_x, 418),
        scale=0.72,
        color=COLOR_TEXT,
        thickness=2,
    )
    draw_text(
        canvas,
        f"Pontos por acerto: {exercicio.get('pontos_por_acerto', 1)}",
        (PANEL_X + 18, 450),
        scale=0.52,
        color=COLOR_MUTED,
    )

    draw_card(canvas, (PANEL_X, 490), (card_right, 672), "MENSAGENS")
    feedback_lines = wrap_text(exercicio.get("feedback", ""), max_chars=40)
    for index, line in enumerate(feedback_lines[:4]):
        draw_text(canvas, line, (PANEL_X + 18, 532 + index * 28), scale=0.58, color=COLOR_SUCCESS)

    ultima = exercicio.get("ultima_palavra_concluida", "")
    if ultima:
        draw_text(canvas, f"Ultima concluida: {ultima}", (PANEL_X + 18, 646), scale=0.54, color=COLOR_ACCENT, thickness=2)

    draw_card(canvas, (PANEL_X, 692), (card_right, 788), "")
    draw_text(canvas, "ESPACO confirma | C limpa | R reinicia | N proxima", (PANEL_X + 18, 730), scale=0.47, color=COLOR_TEXT)
    draw_text(canvas, "1 facil | 2 medio | 3 dificil | F fotos | P palavras | M misto", (PANEL_X + 18, 754), scale=0.44, color=COLOR_TEXT)
    draw_text(canvas, "H dica | ESC sai", (PANEL_X + 18, 778), scale=0.44, color=COLOR_TEXT)

    draw_text(canvas, f"CSV: {exercicio.get('fonte_dados', '')}", (PANEL_X, 808), scale=0.4, color=(150, 170, 205), thickness=1)


def draw_success_badge(canvas, exercicio):
    if not exercicio.get("ultima_palavra_concluida"):
        return

    overlay = canvas.copy()
    cv2.rectangle(overlay, (28, FRAME_HEIGHT - 165), (390, FRAME_HEIGHT - 48), (28, 70, 42), -1)
    cv2.addWeighted(overlay, 0.82, canvas, 0.18, 0, canvas)
    cv2.rectangle(canvas, (28, FRAME_HEIGHT - 165), (390, FRAME_HEIGHT - 48), (120, 255, 180), 2)
    draw_text(canvas, "ACERTOU!", (54, FRAME_HEIGHT - 118), scale=0.96, color=(120, 255, 180), thickness=3)
    draw_text(canvas, exercicio.get("ultima_palavra_concluida", ""), (54, FRAME_HEIGHT - 78), scale=0.76, color=COLOR_TEXT, thickness=2)


def build_exercise_canvas(frame, estado, exercicio, modo_jogo, show_hint):
    canvas = create_layout(frame)
    draw_camera_header(canvas, estado, exercicio, modo_jogo)
    draw_right_panel(canvas, exercicio, estado, modo_jogo, show_hint)
    draw_success_badge(canvas, exercicio)
    return canvas


async def send_action(websocket, payload):
    await websocket.send(json.dumps(payload))
    response = json.loads(await websocket.recv())
    if response.get("tipo") == "erro":
        raise RuntimeError(response.get("mensagem", "Erro na acao enviada"))
    return response


async def main():
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not camera.isOpened():
        raise RuntimeError("Erro ao acessar webcam local")

    current_image_path = None
    current_image_frame = None
    show_hint = False
    initial_game_mode = get_initial_game_mode()

    try:
        async with connect(SERVER_URL, max_size=2**22) as websocket:
            if initial_game_mode != "misto":
                await send_action(websocket, {"acao": "definir_modo_jogo", "modo_jogo": initial_game_mode})

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
                tipo_desafio = exercicio.get("tipo_desafio", "palavra")
                imagem_caminho = exercicio.get("imagem_caminho", "")
                modo_jogo = exercicio.get("modo_jogo", "misto")
                dica = exercicio.get("dica", "")

                canvas = build_exercise_canvas(frame, estado, exercicio, modo_jogo, show_hint)

                if tipo_desafio == "imagem" and imagem_caminho:
                    resolved_image_path = (PROJECT_ROOT / imagem_caminho).resolve()
                    if current_image_path != resolved_image_path:
                        challenge_image = cv2.imread(str(resolved_image_path))
                        current_image_path = resolved_image_path
                        current_image_frame = None

                        if challenge_image is not None:
                            current_image_frame = fit_image(challenge_image, 520, 520)

                    if current_image_frame is not None:
                        challenge_view = np.full((620, 620, 3), (18, 24, 38), dtype=np.uint8)
                        cv2.rectangle(challenge_view, (24, 24), (596, 596), (30, 40, 58), -1)
                        cv2.rectangle(challenge_view, (24, 24), (596, 596), (105, 160, 235), 2)
                        image_y = 60 + (500 - current_image_frame.shape[0]) // 2
                        image_x = 60 + (500 - current_image_frame.shape[1]) // 2
                        challenge_view[
                            image_y : image_y + current_image_frame.shape[0],
                            image_x : image_x + current_image_frame.shape[1],
                        ] = current_image_frame
                        draw_text(challenge_view, "Imagem do Desafio", (52, 48), scale=0.74, color=COLOR_TEXT, thickness=2)
                        if show_hint and dica:
                            draw_hint_overlay(challenge_view, dica)
                        cv2.imshow(CHALLENGE_WINDOW, challenge_view)
                else:
                    current_image_path = None
                    current_image_frame = None
                    close_challenge_window()

                cv2.imshow(WINDOW_NAME, canvas)
                key = cv2.waitKey(1) & 0xFF

                if key == ord(" "):
                    await send_action(websocket, {"acao": "confirmar_letra"})
                elif key == ord("c"):
                    await send_action(websocket, {"acao": "limpar_palavra"})
                elif key == ord("r"):
                    await send_action(websocket, {"acao": "reiniciar_exercicio"})
                    show_hint = False
                elif key == ord("n"):
                    await send_action(websocket, {"acao": "proxima_palavra"})
                    show_hint = False
                elif key == ord("1"):
                    await send_action(websocket, {"acao": "definir_dificuldade", "dificuldade": "facil"})
                    show_hint = False
                elif key == ord("2"):
                    await send_action(websocket, {"acao": "definir_dificuldade", "dificuldade": "medio"})
                    show_hint = False
                elif key == ord("3"):
                    await send_action(websocket, {"acao": "definir_dificuldade", "dificuldade": "dificil"})
                    show_hint = False
                elif key == ord("f"):
                    await send_action(websocket, {"acao": "definir_modo_jogo", "modo_jogo": "fotos"})
                    show_hint = False
                elif key == ord("p"):
                    await send_action(websocket, {"acao": "definir_modo_jogo", "modo_jogo": "palavras"})
                    show_hint = False
                elif key == ord("m"):
                    await send_action(websocket, {"acao": "definir_modo_jogo", "modo_jogo": "misto"})
                    show_hint = False
                elif key in (ord("h"), ord("H"), ord("4")):
                    show_hint = not show_hint
                elif key == 27:
                    break
    finally:
        camera.release()
        close_challenge_window()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    asyncio.run(main())
