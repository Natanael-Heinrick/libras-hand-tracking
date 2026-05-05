import asyncio
import base64
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from websockets.asyncio.client import connect


SERVER_URL = "ws://127.0.0.1:8765/exercicios"
PROJECT_ROOT = Path(__file__).resolve().parent
CHALLENGE_WINDOW = "Desafio por Imagem"
WINDOW_NAME = "Hand Tracking - Exercicios"
FRAME_WIDTH = 1400
FRAME_HEIGHT = 820
CAMERA_WIDTH = 900
PANEL_X = CAMERA_WIDTH + 22
PANEL_WIDTH = FRAME_WIDTH - PANEL_X - 22
SKY_HEIGHT = 520

COLOR_SKY_TOP = (255, 178, 78)
COLOR_SKY_BOTTOM = (237, 226, 150)
COLOR_CLOUD = (246, 246, 255)
COLOR_CLOUD_SHADOW = (214, 224, 244)
COLOR_HILL = (62, 120, 62)
COLOR_GRASS = (68, 146, 78)
COLOR_GRASS_TOP = (96, 190, 92)
COLOR_GRASS_SHADOW = (56, 108, 50)
COLOR_WOOD_DARK = (102, 70, 40)
COLOR_WOOD = (132, 93, 55)
COLOR_WOOD_LIGHT = (160, 118, 72)
COLOR_WOOD_SOFT = (180, 138, 90)
COLOR_BORDER = (252, 232, 150)
COLOR_BORDER_SOFT = (255, 245, 170)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_SOFT = (246, 238, 224)
COLOR_MUTED = (236, 228, 210)
COLOR_ACCENT = (104, 216, 250)
COLOR_ACCENT_BORDER = (142, 190, 240)
COLOR_SUCCESS = (164, 238, 142)
COLOR_WARNING = (255, 240, 160)
COLOR_CAMERA_BANNER = (66, 104, 150)
COLOR_CAMERA_BANNER_BORDER = (171, 206, 255)
COLOR_STATUS_BG = (44, 84, 62)
COLOR_CONTROLS = (88, 78, 52)


def draw_text(canvas, text, position, scale=0.8, color=COLOR_TEXT, thickness=2):
    cv2.putText(
        canvas,
        str(text),
        position,
        cv2.FONT_HERSHEY_DUPLEX,
        scale,
        color,
        thickness,
        cv2.LINE_AA,
    )


def draw_card(canvas, top_left, bottom_right, title="", fill_color=COLOR_WOOD, border_color=COLOR_BORDER, title_color=COLOR_TEXT):
    x1, y1 = top_left
    x2, y2 = bottom_right
    cv2.rectangle(canvas, (x1 + 6, y1 + 6), (x2 + 6, y2 + 6), COLOR_WOOD_DARK, -1)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), fill_color, -1)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), border_color, 3)
    if title:
        draw_text(canvas, title, (x1 + 18, y1 + 30), scale=0.58, color=title_color, thickness=2)


def draw_badge(canvas, x, y, text, fill_color, text_color=COLOR_TEXT):
    (text_width, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, 0.48, 1)
    width = text_width + 28
    cv2.rectangle(canvas, (x, y), (x + width, y + 30), fill_color, -1)
    cv2.rectangle(canvas, (x, y), (x + width, y + 30), COLOR_BORDER_SOFT, 2)
    draw_text(canvas, text, (x + 14, y + 21), scale=0.48, color=text_color, thickness=1)
    return width


def draw_stat_value(canvas, label, value, x, y, value_color=COLOR_TEXT):
    draw_text(canvas, label, (x, y), scale=0.5, color=COLOR_MUTED, thickness=1)
    draw_text(canvas, value, (x, y + 42), scale=0.92, color=value_color, thickness=3)


def draw_stat_card(canvas, top_left, size, label, value, value_color=COLOR_TEXT):
    x, y = top_left
    width, height = size
    cv2.rectangle(canvas, (x + 5, y + 5), (x + width + 5, y + height + 5), COLOR_WOOD_DARK, -1)
    cv2.rectangle(canvas, (x, y), (x + width, y + height), COLOR_WOOD_LIGHT, -1)
    cv2.rectangle(canvas, (x, y), (x + width, y + height), COLOR_BORDER_SOFT, 2)
    draw_text(canvas, label, (x + 14, y + 24), scale=0.46, color=COLOR_MUTED, thickness=1)
    draw_text(canvas, value, (x + 14, y + 62), scale=0.86, color=value_color, thickness=3)


def draw_pixel_cloud(canvas, x, y, size):
    blocks = [
        (0, 1),
        (1, 0),
        (1, 1),
        (2, 0),
        (2, 1),
        (3, 1),
        (4, 1),
        (1, 2),
        (2, 2),
        (3, 2),
    ]
    for col, row in blocks:
        x1 = x + col * size
        y1 = y + row * size
        cv2.rectangle(canvas, (x1, y1), (x1 + size, y1 + size), COLOR_CLOUD, -1)
        cv2.rectangle(
            canvas,
            (x1, y1 + size - 4),
            (x1 + size, y1 + size),
            COLOR_CLOUD_SHADOW,
            -1,
        )


def draw_pixel_background(canvas):
    for y in range(FRAME_HEIGHT):
        ratio = min(1.0, y / max(1, SKY_HEIGHT))
        color = (
            int(COLOR_SKY_TOP[0] + (COLOR_SKY_BOTTOM[0] - COLOR_SKY_TOP[0]) * ratio),
            int(COLOR_SKY_TOP[1] + (COLOR_SKY_BOTTOM[1] - COLOR_SKY_TOP[1]) * ratio),
            int(COLOR_SKY_TOP[2] + (COLOR_SKY_BOTTOM[2] - COLOR_SKY_TOP[2]) * ratio),
        )
        cv2.line(canvas, (0, y), (FRAME_WIDTH, y), color, 1)

    draw_pixel_cloud(canvas, 90, 56, 18)
    draw_pixel_cloud(canvas, 520, 46, 14)
    draw_pixel_cloud(canvas, 1080, 80, 16)

    cv2.circle(canvas, (140, SKY_HEIGHT + 54), 132, COLOR_HILL, -1)
    cv2.circle(canvas, (430, SKY_HEIGHT + 70), 190, COLOR_HILL, -1)
    cv2.circle(canvas, (980, SKY_HEIGHT + 60), 170, COLOR_HILL, -1)
    cv2.circle(canvas, (1290, SKY_HEIGHT + 72), 150, COLOR_HILL, -1)

    cv2.rectangle(canvas, (0, SKY_HEIGHT), (FRAME_WIDTH, FRAME_HEIGHT), COLOR_GRASS, -1)
    cv2.rectangle(canvas, (0, SKY_HEIGHT), (FRAME_WIDTH, SKY_HEIGHT + 16), COLOR_GRASS_TOP, -1)
    cv2.rectangle(canvas, (0, SKY_HEIGHT + 16), (FRAME_WIDTH, SKY_HEIGHT + 34), COLOR_GRASS_SHADOW, -1)

    for x in range(0, FRAME_WIDTH, 44):
        cv2.rectangle(canvas, (x, FRAME_HEIGHT - 18), (x + 22, FRAME_HEIGHT), COLOR_CONTROLS, -1)
    cv2.rectangle(canvas, (0, FRAME_HEIGHT - 18), (FRAME_WIDTH, FRAME_HEIGHT), COLOR_WOOD, 2)


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
    cv2.rectangle(overlay, (12, 12), (overlay.shape[1] - 12, 82), COLOR_CAMERA_BANNER, -1)
    cv2.addWeighted(overlay, 0.82, image, 0.18, 0, image)
    cv2.rectangle(image, (12, 12), (image.shape[1] - 12, 82), COLOR_BORDER_SOFT, 2)
    draw_text(image, f"Dica: {hint_text}", (28, 55), scale=0.6, color=COLOR_TEXT, thickness=2)


def wrap_text(text, max_chars=38):
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
    canvas = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
    draw_pixel_background(canvas)

    camera_view = cv2.resize(frame, (CAMERA_WIDTH, FRAME_HEIGHT))
    camera_x1 = 18
    camera_y1 = 18
    camera_x2 = camera_x1 + CAMERA_WIDTH
    camera_y2 = camera_y1 + FRAME_HEIGHT - 36
    camera_height = camera_y2 - camera_y1
    resized_camera = cv2.resize(camera_view, (CAMERA_WIDTH, camera_height))

    cv2.rectangle(canvas, (camera_x1 + 8, camera_y1 + 8), (camera_x2 + 8, camera_y2 + 8), COLOR_WOOD_DARK, -1)
    cv2.rectangle(canvas, (camera_x1, camera_y1), (camera_x2, camera_y2), COLOR_BORDER_SOFT, 4)
    canvas[camera_y1:camera_y2, camera_x1:camera_x2] = resized_camera

    overlay = canvas.copy()
    cv2.rectangle(overlay, (camera_x1, camera_y1), (camera_x2, camera_y1 + 130), (170, 212, 255), -1)
    cv2.rectangle(overlay, (camera_x1, camera_y2 - 140), (camera_x2, camera_y2), (116, 180, 255), -1)
    cv2.addWeighted(overlay, 0.22, canvas, 0.78, 0, canvas)
    cv2.rectangle(canvas, (camera_x1, camera_y1), (camera_x2, camera_y2), COLOR_BORDER_SOFT, 4)

    draw_card(
        canvas,
        (36, 28),
        (404, 118),
        "",
        fill_color=COLOR_CAMERA_BANNER,
        border_color=COLOR_CAMERA_BANNER_BORDER,
    )

    return canvas


def draw_camera_header(canvas, estado, exercicio, modo_jogo):
    modo_label = {
        "fotos": "Modo Fotos",
        "palavras": "Modo Palavras",
        "misto": "Modo Misto",
    }.get(modo_jogo, "Modo Livre")
    draw_text(canvas, "DESAFIO DE LIBRAS", (58, 66), scale=0.92, color=COLOR_TEXT, thickness=3)
    draw_text(canvas, modo_label, (58, 100), scale=0.62, color=COLOR_WARNING, thickness=2)


def draw_embedded_challenge(canvas, exercicio, current_image_frame, show_hint):
    card_right = PANEL_X + PANEL_WIDTH
    image_top = 328
    image_bottom = 600
    draw_card(
        canvas,
        (PANEL_X, image_top),
        (card_right, image_bottom),
        "IMAGEM DO DESAFIO",
        fill_color=COLOR_WOOD_LIGHT,
        border_color=COLOR_BORDER_SOFT,
        title_color=COLOR_TEXT,
    )

    area_x1 = PANEL_X + 16
    area_y1 = image_top + 40
    area_x2 = card_right - 16
    area_y2 = image_bottom - 14
    cv2.rectangle(canvas, (area_x1, area_y1), (area_x2, area_y2), (244, 236, 220), -1)
    cv2.rectangle(canvas, (area_x1, area_y1), (area_x2, area_y2), COLOR_CAMERA_BANNER_BORDER, 2)

    if current_image_frame is None:
        draw_text(canvas, "Imagem indisponivel", (PANEL_X + 96, 490), scale=0.68, color=COLOR_WOOD_DARK, thickness=2)
        return

    image_y = area_y1 + ((area_y2 - area_y1) - current_image_frame.shape[0]) // 2
    image_x = area_x1 + ((area_x2 - area_x1) - current_image_frame.shape[1]) // 2
    canvas[
        image_y : image_y + current_image_frame.shape[0],
        image_x : image_x + current_image_frame.shape[1],
    ] = current_image_frame

    if show_hint and exercicio.get("dica", ""):
        hint_box = canvas[
            image_y : image_y + current_image_frame.shape[0],
            image_x : image_x + current_image_frame.shape[1],
        ]
        draw_hint_overlay(hint_box, exercicio.get("dica", ""))


def draw_right_panel(canvas, exercicio, estado, modo_jogo, show_hint, success_word, current_image_frame):
    tipo_desafio = exercicio.get("tipo_desafio", "palavra")
    card_right = PANEL_X + PANEL_WIDTH
    border_color = COLOR_BORDER_SOFT if tipo_desafio == "imagem" else COLOR_BORDER
    target_word = exercicio.get("palavra_alvo", "")
    points_value = str(exercicio.get("pontuacao", 0))
    round_value = f"{exercicio.get('indice_palavra', 0) + 1}/{exercicio.get('total_palavras', 0)}"
    status_lines = wrap_text(exercicio.get("feedback", ""), max_chars=36)
    status_text = status_lines[0] if status_lines else "Aguardando sua proxima jogada."
    current_word = estado.get("palavra", "") or "_"
    current_letter = estado.get("letra_estavel") or estado.get("letra") or "--"

    draw_card(
        canvas,
        (PANEL_X, 26),
        (card_right, 198),
        "OBJETIVO DA RODADA",
        fill_color=COLOR_WOOD,
        border_color=border_color,
        title_color=COLOR_TEXT,
    )

    if tipo_desafio == "imagem":
        draw_text(canvas, "Descubra a palavra pela imagem", (PANEL_X + 18, 82), scale=0.68, color=COLOR_TEXT, thickness=2)
        draw_text(canvas, "Use os sinais na ordem correta.", (PANEL_X + 18, 120), scale=0.5, color=COLOR_TEXT_SOFT, thickness=1)
        draw_text(canvas, f"Dica {('ativada' if show_hint else 'desativada')}", (PANEL_X + 18, 164), scale=0.56, color=COLOR_ACCENT, thickness=2)
    else:
        draw_text(canvas, "Palavra alvo", (PANEL_X + 18, 82), scale=0.56, color=COLOR_WARNING, thickness=2)
        draw_text(canvas, target_word or "--", (PANEL_X + 18, 150), scale=1.3, color=COLOR_TEXT, thickness=4)
        draw_text(canvas, "Reproduza essa palavra usando os sinais.", (PANEL_X + 18, 182), scale=0.46, color=COLOR_TEXT_SOFT, thickness=1)

    response_bottom = 316
    response_split = PANEL_X + 300
    draw_card(
        canvas,
        (PANEL_X, 222),
        (response_split, response_bottom),
        "SUA PALAVRA",
        fill_color=COLOR_WOOD_LIGHT,
        border_color=COLOR_BORDER_SOFT,
        title_color=COLOR_TEXT,
    )
    draw_text(canvas, current_word, (PANEL_X + 18, 286), scale=1.1, color=COLOR_WARNING, thickness=3)

    draw_card(
        canvas,
        (response_split + 12, 222),
        (card_right, response_bottom),
        "LETRA ATUAL",
        fill_color=COLOR_STATUS_BG,
        border_color=COLOR_SUCCESS,
        title_color=COLOR_TEXT,
    )
    draw_text(canvas, current_letter, (response_split + 62, 286), scale=1.02, color=COLOR_TEXT, thickness=3)

    if tipo_desafio == "imagem":
        draw_embedded_challenge(canvas, exercicio, current_image_frame, show_hint)
        progress_top = 620
    else:
        progress_top = 342

    draw_card(
        canvas,
        (PANEL_X, progress_top),
        (card_right, 700),
        "PROGRESSO",
        fill_color=COLOR_WOOD,
        border_color=COLOR_BORDER,
        title_color=COLOR_TEXT,
    )

    stat_y = progress_top + 50
    stat_width = 126
    stat_height = 76
    draw_stat_card(canvas, (PANEL_X + 18, stat_y), (stat_width, stat_height), "Pontos", points_value, value_color=COLOR_WARNING)
    draw_stat_card(canvas, (PANEL_X + 160, stat_y), (stat_width, stat_height), "Rodada", round_value, value_color=COLOR_TEXT)
    draw_stat_card(canvas, (PANEL_X + 302, stat_y), (stat_width, stat_height), "Nivel", str(exercicio.get("nivel", 1)), value_color=COLOR_ACCENT)

    badge_x = PANEL_X + 18
    badge_y = progress_top + 144
    badge_x += draw_badge(canvas, badge_x, badge_y, f"Dificuldade {exercicio.get('dificuldade', '')}", COLOR_CAMERA_BANNER) + 8
    badge_x += draw_badge(canvas, badge_x, badge_y, f"Modo {modo_jogo}", COLOR_STATUS_BG) + 8
    if tipo_desafio != "imagem":
        draw_badge(canvas, badge_x, badge_y, f"{exercicio.get('tamanho_palavra', 0)} letras", COLOR_WOOD_SOFT, text_color=COLOR_TEXT)

    if success_word:
        draw_text(canvas, "ACERTOU!", (PANEL_X + 18, progress_top + 218), scale=0.68, color=COLOR_SUCCESS, thickness=2)
        draw_text(canvas, success_word, (PANEL_X + 160, progress_top + 218), scale=0.7, color=COLOR_TEXT, thickness=2)
    else:
        draw_text(canvas, "Status", (PANEL_X + 18, progress_top + 214), scale=0.5, color=COLOR_MUTED, thickness=1)
        draw_text(canvas, status_text, (PANEL_X + 18, progress_top + 246), scale=0.56, color=COLOR_TEXT_SOFT, thickness=2)

    cv2.rectangle(canvas, (PANEL_X, 730), (card_right, 792), COLOR_CONTROLS, -1)
    cv2.rectangle(canvas, (PANEL_X, 730), (card_right, 792), COLOR_BORDER_SOFT, 3)
    draw_text(
        canvas,
        "[ESPACO] Confirmar | [C] Limpar | [N] Proxima | [ESC] Sair",
        (PANEL_X + 16, 756),
        scale=0.42,
        color=COLOR_TEXT,
        thickness=1,
    )
    draw_text(
        canvas,
        "[R] Reiniciar | [1/2/3] Dificuldade | [F/P/M] Modo | [H/4] Dica",
        (PANEL_X + 16, 780),
        scale=0.39,
        color=COLOR_TEXT_SOFT,
        thickness=1,
    )


def build_exercise_canvas(frame, estado, exercicio, modo_jogo, show_hint, success_word, current_image_frame):
    canvas = create_layout(frame)
    draw_camera_header(canvas, estado, exercicio, modo_jogo)
    draw_right_panel(canvas, exercicio, estado, modo_jogo, show_hint, success_word, current_image_frame)
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
    last_success_word = ""
    success_visible_until = 0.0

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
                ultima_concluida = exercicio.get("ultima_palavra_concluida", "")

                if ultima_concluida and ultima_concluida != last_success_word:
                    last_success_word = ultima_concluida
                    success_visible_until = time.monotonic() + 1.75

                success_word = last_success_word if time.monotonic() < success_visible_until else ""

                if tipo_desafio == "imagem" and imagem_caminho:
                    resolved_image_path = (PROJECT_ROOT / imagem_caminho).resolve()
                    if current_image_path != resolved_image_path:
                        challenge_image = cv2.imread(str(resolved_image_path))
                        current_image_path = resolved_image_path
                        current_image_frame = None

                        if challenge_image is not None:
                            current_image_frame = fit_image(challenge_image, 386, 194)
                else:
                    current_image_path = None
                    current_image_frame = None
                    close_challenge_window()

                canvas = build_exercise_canvas(
                    frame,
                    estado,
                    exercicio,
                    modo_jogo,
                    show_hint,
                    success_word,
                    current_image_frame,
                )

                if tipo_desafio == "imagem" and imagem_caminho and current_image_frame is None:
                    fallback = np.full((360, 360, 3), (244, 236, 220), dtype=np.uint8)
                    cv2.rectangle(fallback, (18, 18), (342, 342), COLOR_WOOD_LIGHT, -1)
                    cv2.rectangle(fallback, (18, 18), (342, 342), COLOR_BORDER_SOFT, 3)
                    draw_text(fallback, "Imagem nao carregada", (54, 186), scale=0.62, color=COLOR_WOOD_DARK, thickness=2)
                    if show_hint and dica:
                        draw_hint_overlay(fallback, dica)
                    cv2.imshow(CHALLENGE_WINDOW, fallback)
                else:
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
