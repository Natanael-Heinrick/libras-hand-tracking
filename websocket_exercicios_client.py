import asyncio
import base64
import json
import queue
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from websockets.asyncio.client import connect

from ui_decor import get_floating_hands_css, get_floating_hands_markup

try:
    import webview
except ImportError:
    webview = None


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


def build_exercise_html() -> str:
    return """
<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Exercicios LIBRAS</title>
    <style>
        :root {
            --bg: #fff8e8;
            --surface: #ffffff;
            --soft: #fff4c9;
            --ink: #1d2735;
            --muted: #65758b;
            --line: #ffd36a;
            --blue: #2577ff;
            --green: #00a978;
            --amber: #ffb000;
            --red: #ef4444;
            --pink: #ff5c8a;
            --purple: #7c5cff;
            --cyan: #00b8d9;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            min-height: 100vh;
            font-family: "Segoe UI", Arial, sans-serif;
            color: var(--ink);
            background:
                linear-gradient(135deg, rgba(255,176,0,.18) 0 18%, transparent 18%),
                linear-gradient(45deg, rgba(0,184,217,.16) 0 15%, transparent 15%),
                linear-gradient(160deg, #fff8e8 0%, #e9f8ff 52%, #fff0f6 100%);
        }
        .app {
            min-height: 100vh;
            display: grid;
            grid-template-columns: minmax(360px, 42vw) 1fr;
            gap: 22px;
            padding: 22px;
            position: relative;
            z-index: 1;
        }
        .panel {
            background: var(--surface);
            border: 2px solid var(--line);
            border-radius: 8px;
            box-shadow: 0 16px 40px rgba(29,45,68,.1);
        }
        .camera-panel { align-self: start; padding: 16px; border-color: var(--cyan); }
        .camera-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            color: var(--muted);
            font-weight: 800;
        }
        .dot {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--green);
            margin-right: 8px;
        }
        #camera {
            display: block;
            width: 100%;
            aspect-ratio: 4 / 3;
            object-fit: cover;
            border-radius: 6px;
            background: #172033;
        }
        .info {
            padding: 22px;
            display: grid;
            gap: 14px;
            align-content: start;
        }
        h1 { margin: 0; font-size: 2rem; letter-spacing: 0; }
        .lead { margin: 4px 0 2px; color: var(--muted); line-height: 1.45; }
        .grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
        }
        .card {
            min-height: 104px;
            padding: 15px;
            border: 2px solid var(--card-color, var(--line));
            border-radius: 8px;
            background: linear-gradient(180deg, #ffffff 0%, var(--soft) 100%);
        }
        .card:nth-child(1) { --card-color: var(--blue); }
        .card:nth-child(2) { --card-color: var(--amber); }
        .card:nth-child(3) { --card-color: var(--green); }
        .card:nth-child(4) { --card-color: var(--pink); }
        .card:nth-child(5) { --card-color: var(--purple); }
        .card:nth-child(6) { --card-color: var(--cyan); }
        .wide { grid-column: 1 / -1; }
        .span2 { grid-column: span 2; }
        .label {
            color: var(--muted);
            font-size: .76rem;
            text-transform: uppercase;
            font-weight: 800;
            letter-spacing: .04em;
        }
        .value {
            margin-top: 9px;
            font-size: 1.7rem;
            font-weight: 850;
            word-break: break-word;
        }
        .target { color: var(--blue); font-size: 2.2rem; }
        .letter { color: var(--amber); font-size: 3.2rem; line-height: 1; }
        .word { color: var(--green); }
        .challenge {
            display: grid;
            grid-template-columns: 220px 1fr;
            gap: 14px;
            align-items: center;
        }
        #challenge-image {
            width: 100%;
            aspect-ratio: 1 / 1;
            object-fit: contain;
            border-radius: 8px;
            border: 1px solid var(--line);
            background: white;
            display: none;
        }
        .badges { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
        .badge {
            display: inline-flex;
            min-height: 30px;
            align-items: center;
            border-radius: 999px;
            padding: 0 11px;
            border: 1px solid var(--line);
            background: white;
            color: var(--muted);
            font-weight: 800;
            font-size: .82rem;
        }
        .actions { display: flex; flex-wrap: wrap; gap: 9px; }
        button {
            min-height: 40px;
            border: 1px solid var(--line);
            border-radius: 8px;
            background: white;
            color: var(--ink);
            padding: 0 12px;
            font: inherit;
            font-weight: 800;
            cursor: pointer;
        }
        button.primary { background: var(--blue); border-color: var(--blue); color: white; }
        button.good { background: var(--green); border-color: var(--green); color: white; }
        button.warn { background: var(--red); border-color: var(--red); color: white; }
        button:nth-child(5), button:nth-child(8) { border-color: var(--amber); background: #fff2bd; }
        button:nth-child(6), button:nth-child(9) { border-color: var(--cyan); background: #dff8ff; }
        button:nth-child(7), button:nth-child(10) { border-color: var(--pink); background: #ffe4ec; }
        @media (max-width: 980px) {
            .app { grid-template-columns: 1fr; padding: 14px; }
            .grid { grid-template-columns: 1fr; }
            .span2 { grid-column: 1; }
            .challenge { grid-template-columns: 1fr; }
        }
        __FLOATING_HANDS_CSS__
    </style>
</head>
<body>
    __FLOATING_HANDS_MARKUP__
    <div class="app">
        <section class="panel camera-panel">
            <div class="camera-top">
                <span><i class="dot"></i>Camera</span>
                <span id="hands">0 mao(s)</span>
            </div>
            <img id="camera" alt="Camera ao vivo">
        </section>
        <main class="panel info">
            <div>
                <h1>Desafio de LIBRAS</h1>
                <p class="lead" id="mode-label">Modo misto</p>
            </div>
            <section class="grid">
                <article class="card span2">
                    <div class="label">Objetivo</div>
                    <div class="value target" id="target">--</div>
                </article>
                <article class="card">
                    <div class="label">Letra atual</div>
                    <div class="value letter" id="letter">--</div>
                </article>
                <article class="card span2">
                    <div class="label">Sua palavra</div>
                    <div class="value word" id="word">_</div>
                </article>
                <article class="card">
                    <div class="label">Pontos</div>
                    <div class="value" id="points">0</div>
                </article>
                <article class="card wide challenge" id="challenge-card">
                    <img id="challenge-image" alt="Imagem do desafio">
                    <div>
                        <div class="label">Imagem do desafio</div>
                        <div class="value" id="challenge-text">Sem imagem nesta rodada</div>
                        <div class="badges">
                            <span class="badge" id="hint-badge">Dica desativada</span>
                            <span class="badge" id="difficulty">Dificuldade --</span>
                            <span class="badge" id="round">Rodada --</span>
                            <span class="badge" id="level">Nivel --</span>
                        </div>
                    </div>
                </article>
                <article class="card wide">
                    <div class="label">Status</div>
                    <div class="value" id="feedback">Aguardando sua proxima jogada.</div>
                </article>
            </section>
            <div class="actions">
                <button class="primary" onclick="action('confirmar_letra')">Espaco Confirmar</button>
                <button onclick="action('limpar_palavra')">C Limpar</button>
                <button onclick="action('proxima_palavra')">N Proxima</button>
                <button onclick="action('reiniciar_exercicio')">R Reiniciar</button>
                <button onclick="setDifficulty('facil')">1 Facil</button>
                <button onclick="setDifficulty('medio')">2 Medio</button>
                <button onclick="setDifficulty('dificil')">3 Dificil</button>
                <button onclick="setMode('fotos')">F Fotos</button>
                <button onclick="setMode('palavras')">P Palavras</button>
                <button onclick="setMode('misto')">M Misto</button>
                <button class="good" onclick="toggleHint()">H Dica</button>
                <button class="warn" onclick="window.pywebview.api.close()">ESC Sair</button>
            </div>
        </main>
    </div>
    <script>
        function action(name) { window.pywebview.api.action({acao: name}); }
        function setDifficulty(value) { window.pywebview.api.action({acao: "definir_dificuldade", dificuldade: value}); }
        function setMode(value) { window.pywebview.api.action({acao: "definir_modo_jogo", modo_jogo: value}); }
        function toggleHint() { window.pywebview.api.toggle_hint(); }
        function updateGame(cameraBase64, estado, exercicio, ui) {
            document.getElementById("camera").src = "data:image/jpeg;base64," + cameraBase64;
            const letter = estado.letra_estavel || estado.letra || "--";
            const word = estado.palavra || "_";
            const target = exercicio.tipo_desafio === "imagem"
                ? "Descubra pela imagem"
                : (exercicio.palavra_alvo || "--");
            document.getElementById("letter").textContent = letter;
            document.getElementById("word").textContent = word;
            document.getElementById("target").textContent = target;
            document.getElementById("points").textContent = exercicio.pontuacao ?? 0;
            document.getElementById("hands").textContent = (estado.maos_detectadas || 0) + " mao(s)";
            document.getElementById("feedback").textContent = ui.success_word
                ? "Acertou: " + ui.success_word
                : (exercicio.feedback || "Aguardando sua proxima jogada.");
            document.getElementById("mode-label").textContent = "Modo " + (exercicio.modo_jogo || "misto");
            document.getElementById("difficulty").textContent = "Dificuldade " + (exercicio.dificuldade || "--");
            document.getElementById("round").textContent = "Rodada " + ((exercicio.indice_palavra ?? 0) + 1) + "/" + (exercicio.total_palavras ?? 0);
            document.getElementById("level").textContent = "Nivel " + (exercicio.nivel ?? "--");
            document.getElementById("hint-badge").textContent = ui.show_hint ? "Dica ativada" : "Dica desativada";
            const image = document.getElementById("challenge-image");
            const text = document.getElementById("challenge-text");
            if (ui.challenge_image) {
                image.src = "data:image/jpeg;base64," + ui.challenge_image;
                image.style.display = "block";
                text.textContent = ui.show_hint && exercicio.dica ? "Dica: " + exercicio.dica : "Observe a imagem e sinalize a resposta.";
            } else {
                image.removeAttribute("src");
                image.style.display = "none";
                text.textContent = "Sem imagem nesta rodada";
            }
        }
        document.addEventListener("keydown", (event) => {
            const key = event.key.toLowerCase();
            if (event.key === " ") { event.preventDefault(); action("confirmar_letra"); }
            if (key === "c") action("limpar_palavra");
            if (key === "r") action("reiniciar_exercicio");
            if (key === "n") action("proxima_palavra");
            if (key === "f") setMode("fotos");
            if (key === "p") setMode("palavras");
            if (key === "m") setMode("misto");
            if (key === "h" || event.key === "4") toggleHint();
            if (event.key === "1") setDifficulty("facil");
            if (event.key === "2") setDifficulty("medio");
            if (event.key === "3") setDifficulty("dificil");
            if (event.key === "Escape") window.pywebview.api.close();
        });
        function signalReady() {
            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.ready();
                return;
            }
            setTimeout(signalReady, 50);
        }
        window.addEventListener("pywebviewready", signalReady);
        setTimeout(signalReady, 0);
    </script>
</body>
</html>
""".replace("__FLOATING_HANDS_CSS__", get_floating_hands_css()).replace(
        "__FLOATING_HANDS_MARKUP__", get_floating_hands_markup()
    )


class ExerciseApi:
    def __init__(self):
        self._actions = queue.Queue()
        self._window = None
        self._closed = False
        self._ready_for_frames = False
        self._show_hint = False

    def ready(self):
        self._ready_for_frames = True

    def action(self, payload):
        self._actions.put(dict(payload or {}))

    def toggle_hint(self):
        self._show_hint = not self._show_hint

    def close(self):
        self._closed = True
        if self._window:
            self._window.destroy()


async def process_webview_actions(websocket, api):
    while True:
        try:
            payload = api._actions.get_nowait()
        except queue.Empty:
            return

        await send_action(websocket, payload)
        if payload.get("acao") in {
            "reiniciar_exercicio",
            "proxima_palavra",
            "definir_dificuldade",
            "definir_modo_jogo",
        }:
            api._show_hint = False


async def open_websocket_with_retry(api, timeout_seconds=10.0):
    deadline = time.monotonic() + timeout_seconds
    last_error = None

    while not api._closed:
        try:
            connection = connect(SERVER_URL, max_size=2**22)
            websocket = await connection.__aenter__()
            return connection, websocket
        except Exception as exc:
            last_error = exc
            if time.monotonic() >= deadline:
                break
            await asyncio.sleep(0.35)

    if last_error is not None:
        raise last_error
    raise RuntimeError("Janela fechada antes da conexao com o servidor")


async def run_webview_exercises(window, api):
    while not api._ready_for_frames and not api._closed:
        await asyncio.sleep(0.05)
    if api._closed:
        return

    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not camera.isOpened():
        raise RuntimeError("Erro ao acessar webcam local")

    initial_game_mode = get_initial_game_mode()
    current_image_path = None
    current_image_frame = None
    last_success_word = ""
    success_visible_until = 0.0
    last_ui_update = 0.0

    try:
        connection, websocket = await open_websocket_with_retry(api)
        try:
            if initial_game_mode != "misto":
                await send_action(websocket, {"acao": "definir_modo_jogo", "modo_jogo": initial_game_mode})

            while not api._closed:
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
                            current_image_frame = fit_image(challenge_image, 520, 520)
                else:
                    current_image_path = None
                    current_image_frame = None

                challenge_image_b64 = (
                    encode_frame(current_image_frame, quality=78)
                    if current_image_frame is not None
                    else ""
                )
                camera_image = encode_frame(cv2.resize(frame, (640, 480)), quality=68)
                ui_state = {
                    "show_hint": api._show_hint,
                    "success_word": success_word,
                    "challenge_image": challenge_image_b64,
                }
                now = time.monotonic()
                if now - last_ui_update >= 0.08:
                    window.evaluate_js(
                        "window.updateGame("
                        + json.dumps(camera_image)
                        + ", "
                        + json.dumps(estado)
                        + ", "
                        + json.dumps(exercicio)
                        + ", "
                        + json.dumps(ui_state)
                        + ");"
                    )
                    last_ui_update = now
                await process_webview_actions(websocket, api)
                await asyncio.sleep(0.01)
        finally:
            await connection.__aexit__(None, None, None)
    finally:
        api._closed = True
        camera.release()


def start_webview_exercises(window, api):
    try:
        asyncio.run(run_webview_exercises(window, api))
    except Exception as exc:
        print(f"Erro na interface HTML dos exercicios: {exc}")
        api._closed = True


def run_webview_app():
    api = ExerciseApi()
    window = webview.create_window(
        WINDOW_NAME,
        html=build_exercise_html(),
        js_api=api,
        width=1220,
        height=760,
        resizable=True,
    )
    api._window = window
    window.events.closed += lambda: setattr(api, "_closed", True)
    webview.start(start_webview_exercises, (window, api), debug=False)


async def send_action(websocket, payload):
    await websocket.send(json.dumps(payload))
    response = json.loads(await websocket.recv())
    if response.get("tipo") == "erro":
        raise RuntimeError(response.get("mensagem", "Erro na acao enviada"))
    return response


async def run_cv2_exercises():
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


def main():
    if webview is not None:
        run_webview_app()
        return

    print("pywebview nao esta instalado; abrindo exercicios com interface antiga em OpenCV.")
    asyncio.run(run_cv2_exercises())


if __name__ == "__main__":
    main()
