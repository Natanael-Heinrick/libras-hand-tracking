import asyncio
import base64
import json
import queue

import cv2
import numpy as np
from websockets.asyncio.client import connect

from ui_decor import get_floating_hands_css, get_floating_hands_markup

try:
    import webview
except ImportError:
    webview = None


SERVER_URL = "ws://127.0.0.1:8765/duelo"
WINDOW_NAME = "Duelo de Tempo LIBRAS"
NAME_WINDOW = "Registro dos Jogadores"
FRAME_WIDTH = 1460
FRAME_HEIGHT = 720
CAMERA_WIDTH = 820
PANEL_X = 846
PANEL_WIDTH = 586
SKY_HEIGHT = 470

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
COLOR_WOOD_SOFT = (178, 138, 92)
COLOR_BORDER = (252, 232, 150)
COLOR_BORDER_SOFT = (255, 245, 170)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_SOFT = (246, 238, 224)
COLOR_MUTED = (236, 228, 210)
COLOR_ACCENT = (104, 216, 250)
COLOR_ACCENT_BORDER = (142, 190, 240)
COLOR_SUCCESS = (164, 238, 142)
COLOR_WARNING = (255, 240, 160)
COLOR_STATUS_BG = (44, 84, 62)
COLOR_CONTROLS = (88, 78, 52)
COLOR_CAMERA_BANNER = (66, 104, 150)
COLOR_CAMERA_BANNER_BORDER = (171, 206, 255)
PLAYER_ONE_COLOR = (255, 200, 120)
PLAYER_TWO_COLOR = (140, 220, 255)
PLAYER_ONE_FILL = (166, 108, 58)
PLAYER_TWO_FILL = (72, 114, 160)
PLAYER_ONE_ID = "oponente_1"
PLAYER_TWO_ID = "oponente_2"


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


def draw_text_right(
    canvas, text, x_right, baseline_y, scale=0.8, color=COLOR_TEXT, thickness=2
):
    text = str(text)
    (text_width, _), _ = cv2.getTextSize(
        text, cv2.FONT_HERSHEY_DUPLEX, scale, thickness
    )
    draw_text(
        canvas,
        text,
        (x_right - text_width, baseline_y),
        scale=scale,
        color=color,
        thickness=thickness,
    )


def draw_panel(
    canvas,
    top_left,
    bottom_right,
    fill_color,
    border_color,
    border_thickness=3,
    shadow=True,
):
    x1, y1 = top_left
    x2, y2 = bottom_right
    if shadow:
        cv2.rectangle(canvas, (x1 + 6, y1 + 6), (x2 + 6, y2 + 6), COLOR_WOOD_DARK, -1)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), fill_color, -1)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), border_color, border_thickness)


def draw_card(canvas, top_left, bottom_right, title, fill_color=COLOR_WOOD, border_color=COLOR_BORDER, title_color=COLOR_TEXT):
    draw_panel(canvas, top_left, bottom_right, fill_color, border_color, 3)
    if title:
        draw_text(
            canvas,
            title,
            (top_left[0] + 18, top_left[1] + 30),
            scale=0.56,
            color=title_color,
            thickness=2,
        )


def draw_badge(canvas, x, y, text, fill_color, text_color=COLOR_TEXT):
    (text_width, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, 0.46, 1)
    width = text_width + 24
    cv2.rectangle(canvas, (x, y), (x + width, y + 28), fill_color, -1)
    cv2.rectangle(canvas, (x, y), (x + width, y + 28), COLOR_BORDER_SOFT, 2)
    draw_text(canvas, text, (x + 12, y + 20), 0.46, text_color, 1)
    return width


def draw_pixel_cloud(canvas, x, y, size):
    blocks = [
        (0, 1), (1, 0), (1, 1), (2, 0), (2, 1), (3, 1), (4, 1),
        (1, 2), (2, 2), (3, 2),
    ]
    for col, row in blocks:
        x1 = x + col * size
        y1 = y + row * size
        cv2.rectangle(canvas, (x1, y1), (x1 + size, y1 + size), COLOR_CLOUD, -1)
        cv2.rectangle(canvas, (x1, y1 + size - 4), (x1 + size, y1 + size), COLOR_CLOUD_SHADOW, -1)


def draw_pixel_background(canvas, width, height, sky_height):
    for y in range(height):
        ratio = min(1.0, y / max(1, sky_height))
        color = (
            int(COLOR_SKY_TOP[0] + (COLOR_SKY_BOTTOM[0] - COLOR_SKY_TOP[0]) * ratio),
            int(COLOR_SKY_TOP[1] + (COLOR_SKY_BOTTOM[1] - COLOR_SKY_TOP[1]) * ratio),
            int(COLOR_SKY_TOP[2] + (COLOR_SKY_BOTTOM[2] - COLOR_SKY_TOP[2]) * ratio),
        )
        cv2.line(canvas, (0, y), (width, y), color, 1)

    draw_pixel_cloud(canvas, 90, 50, 16)
    draw_pixel_cloud(canvas, 500, 40, 12)
    draw_pixel_cloud(canvas, 1100, 72, 14)

    cv2.circle(canvas, (120, sky_height + 40), 120, COLOR_HILL, -1)
    cv2.circle(canvas, (420, sky_height + 54), 164, COLOR_HILL, -1)
    cv2.circle(canvas, (1040, sky_height + 48), 150, COLOR_HILL, -1)

    cv2.rectangle(canvas, (0, sky_height), (width, height), COLOR_GRASS, -1)
    cv2.rectangle(canvas, (0, sky_height), (width, sky_height + 14), COLOR_GRASS_TOP, -1)
    cv2.rectangle(canvas, (0, sky_height + 14), (width, sky_height + 30), COLOR_GRASS_SHADOW, -1)

    for x in range(0, width, 40):
        cv2.rectangle(canvas, (x, height - 18), (x + 20, height), COLOR_CONTROLS, -1)
    cv2.rectangle(canvas, (0, height - 18), (width, height), COLOR_WOOD, 2)


def normalize_player_name(value, fallback):
    normalized = " ".join((value or "").strip().split())
    return normalized[:18] or fallback


def replace_player_labels(text, player_names):
    text = str(text or "")
    return (
        text.replace("Oponente 1", player_names[PLAYER_ONE_ID])
        .replace("Oponente 2", player_names[PLAYER_TWO_ID])
    )


def enrich_duel_labels(duelo, player_names):
    duelo_local = dict(duelo or {})
    current_player = duelo_local.get("jogador_atual", "")
    winner_player = duelo_local.get("vencedor", "")

    duelo_local["jogador_atual_nome"] = player_names.get(
        current_player, duelo_local.get("jogador_atual_label", "")
    )
    duelo_local["vencedor_nome"] = player_names.get(
        winner_player, duelo_local.get("vencedor_label", "")
    )
    duelo_local["feedback"] = replace_player_labels(
        duelo_local.get("feedback", ""), player_names
    )
    duelo_local["mensagem_transicao"] = replace_player_labels(
        duelo_local.get("mensagem_transicao", ""), player_names
    )
    duelo_local["motivo_vitoria"] = replace_player_labels(
        duelo_local.get("motivo_vitoria", ""), player_names
    )
    return duelo_local


def collect_player_names():
    values = {
        PLAYER_ONE_ID: "",
        PLAYER_TWO_ID: "",
    }
    labels = {
        PLAYER_ONE_ID: "Jogador 1",
        PLAYER_TWO_ID: "Jogador 2",
    }
    placeholders = {
        PLAYER_ONE_ID: "Digite o nome do jogador 1",
        PLAYER_TWO_ID: "Digite o nome do jogador 2",
    }
    order = [PLAYER_ONE_ID, PLAYER_TWO_ID]
    active_index = 0

    cv2.namedWindow(NAME_WINDOW)
    try:
        while True:
            canvas = np.zeros((560, 960, 3), dtype=np.uint8)
            draw_pixel_background(canvas, 960, 560, 360)

            draw_panel(canvas, (184, 26), (776, 94), COLOR_CAMERA_BANNER, COLOR_BORDER, 4)
            draw_text(canvas, "REGISTRO DO DUELO", (258, 68), scale=1.0, color=COLOR_TEXT, thickness=3)
            draw_text(
                canvas,
                "Prepare os dois jogadores para a partida.",
                (282, 90),
                scale=0.46,
                color=COLOR_TEXT_SOFT,
                thickness=1,
            )

            draw_panel(canvas, (88, 134), (872, 432), COLOR_WOOD, COLOR_BORDER_SOFT, 4)
            draw_text(
                canvas,
                "Esses nomes valem apenas para esta abertura do duelo.",
                (122, 170),
                scale=0.54,
                color=COLOR_TEXT_SOFT,
                thickness=1,
            )

            for index, player_id in enumerate(order):
                box_y1 = 206 + index * 106
                box_y2 = box_y1 + 66
                is_active = index == active_index
                label_color = PLAYER_ONE_COLOR if player_id == PLAYER_ONE_ID else PLAYER_TWO_COLOR
                fill = PLAYER_ONE_FILL if player_id == PLAYER_ONE_ID else PLAYER_TWO_FILL
                border = COLOR_WARNING if is_active else COLOR_BORDER_SOFT
                shadow_fill = COLOR_WOOD_DARK if is_active else COLOR_WOOD

                draw_text(
                    canvas,
                    labels[player_id],
                    (126, box_y1 - 12),
                    scale=0.6,
                    color=label_color,
                    thickness=2,
                )
                cv2.rectangle(canvas, (112, box_y1 + 6), (852, box_y2 + 6), shadow_fill, -1)
                draw_panel(canvas, (108, box_y1), (848, box_y2), fill, border, 3, shadow=False)
                if is_active:
                    cv2.rectangle(canvas, (92, box_y1 + 16), (104, box_y1 + 30), COLOR_WARNING, -1)
                    cv2.rectangle(canvas, (852, box_y1 + 16), (864, box_y1 + 30), COLOR_WARNING, -1)
                    cv2.rectangle(canvas, (108, box_y1), (848, box_y2), COLOR_BORDER, 1)

                current_text = values[player_id]
                if current_text:
                    display = current_text
                    color = COLOR_TEXT
                else:
                    display = placeholders[player_id]
                    color = COLOR_TEXT_SOFT

                draw_text(canvas, display, (132, box_y1 + 41), scale=0.64, color=color, thickness=2)

            ready = all(values[player_id].strip() for player_id in order)
            status_fill = COLOR_STATUS_BG if ready else COLOR_WOOD_SOFT
            status_border = COLOR_SUCCESS if ready else COLOR_WARNING
            status_text = "Pressione ENTER para continuar" if ready else "Preencha os dois nomes para continuar"
            draw_panel(canvas, (118, 374), (842, 414), status_fill, status_border, 3)
            draw_text(canvas, status_text, (148, 401), scale=0.56, color=COLOR_TEXT, thickness=2)

            cv2.rectangle(canvas, (104, 462), (856, 504), COLOR_CONTROLS, -1)
            cv2.rectangle(canvas, (104, 462), (856, 504), COLOR_BORDER_SOFT, 3)
            draw_text(
                canvas,
                "[ENTER] Confirmar   [TAB] Trocar campo   [BACKSPACE] Apagar   [ESC] Cancelar",
                (124, 489),
                scale=0.4,
                color=COLOR_TEXT,
                thickness=1,
            )

            cv2.imshow(NAME_WINDOW, canvas)
            key = cv2.waitKey(30) & 0xFF

            if key == 27:
                return None
            if key == 9:
                active_index = (active_index + 1) % len(order)
                continue
            if key in (10, 13):
                if ready:
                    return {
                        PLAYER_ONE_ID: normalize_player_name(values[PLAYER_ONE_ID], "Jogador 1"),
                        PLAYER_TWO_ID: normalize_player_name(values[PLAYER_TWO_ID], "Jogador 2"),
                    }
                active_index = (active_index + 1) % len(order)
                continue
            if key in (8, 127):
                player_id = order[active_index]
                values[player_id] = values[player_id][:-1]
                continue
            if 32 <= key <= 126:
                player_id = order[active_index]
                if len(values[player_id]) < 18:
                    values[player_id] += chr(key)
    finally:
        cv2.destroyWindow(NAME_WINDOW)


def draw_lives(canvas, current, max_lives, start_x, y, color):
    x = start_x
    for index in range(max_lives):
        filled = index < current
        fill_color = color if filled else COLOR_WOOD_DARK
        cv2.circle(canvas, (x + 10, y), 11, fill_color, -1)
        cv2.circle(canvas, (x + 10, y), 11, COLOR_BORDER_SOFT, 1)
        if filled:
            cv2.circle(canvas, (x + 7, y - 3), 3, COLOR_BORDER_SOFT, -1)
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
    canvas = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
    draw_pixel_background(canvas, FRAME_WIDTH, FRAME_HEIGHT, SKY_HEIGHT)

    resized = cv2.resize(frame, (CAMERA_WIDTH, FRAME_HEIGHT - 36))
    camera_x1 = 18
    camera_y1 = 18
    camera_x2 = camera_x1 + CAMERA_WIDTH
    camera_y2 = camera_y1 + resized.shape[0]

    draw_panel(canvas, (camera_x1, camera_y1), (camera_x2, camera_y2), COLOR_BORDER_SOFT, COLOR_BORDER_SOFT, 4)
    canvas[camera_y1:camera_y2, camera_x1:camera_x2] = resized

    overlay = canvas.copy()
    cv2.rectangle(overlay, (camera_x1, camera_y1), (camera_x2, camera_y1 + 134), (170, 212, 255), -1)
    cv2.rectangle(overlay, (camera_x1, camera_y2 - 144), (camera_x2, camera_y2), (116, 180, 255), -1)
    cv2.addWeighted(overlay, 0.2, canvas, 0.8, 0, canvas)
    cv2.rectangle(canvas, (camera_x1, camera_y1), (camera_x2, camera_y2), COLOR_BORDER_SOFT, 4)

    draw_panel(canvas, (42, 26), (414, 110), COLOR_CAMERA_BANNER, COLOR_CAMERA_BANNER_BORDER, 3)
    draw_panel(canvas, (PANEL_X, 26), (PANEL_X + PANEL_WIDTH, 702), COLOR_WOOD, COLOR_BORDER, 4)
    return canvas


def draw_header(canvas, duelo, estado):
    player_color = tuple(duelo.get("jogador_atual_cor_bgr", [255, 255, 255]))
    draw_text(canvas, "DUELO DE TEMPO LIBRAS", (62, 64), scale=0.92, color=COLOR_TEXT, thickness=3)
    draw_text(canvas, duelo.get("jogador_atual_nome", ""), (62, 94), scale=0.52, color=COLOR_WARNING, thickness=2)

    draw_text(canvas, "Palavra alvo", (38, 148), scale=0.54, color=COLOR_MUTED, thickness=1)
    draw_text(
        canvas,
        duelo.get("palavra_alvo", "--"),
        (38, 192),
        scale=1.08,
        color=COLOR_WARNING,
        thickness=3,
    )
    draw_text(canvas, "Sua palavra", (38, 236), scale=0.54, color=COLOR_MUTED, thickness=1)
    draw_text(
        canvas,
        estado.get("palavra", "") or "_",
        (38, 278),
        scale=0.96,
        color=COLOR_TEXT,
        thickness=3,
    )
    draw_text(canvas, "Jogador atual", (38, 322), scale=0.54, color=COLOR_MUTED, thickness=1)
    draw_badge(
        canvas,
        38,
        336,
        duelo.get("jogador_atual_nome", duelo.get("jogador_atual_label", "")),
        COLOR_CAMERA_BANNER,
        player_color,
    )


def draw_right_panel(canvas, duelo, estado):
    phase = duelo.get("fase", "")
    player_color = tuple(duelo.get("jogador_atual_cor_bgr", [255, 255, 255]))
    card_right = PANEL_X + PANEL_WIDTH - 18

    draw_card(canvas, (PANEL_X + 18, 46), (card_right, 140), "STATUS DA RODADA", fill_color=COLOR_WOOD_LIGHT, border_color=player_color, title_color=COLOR_TEXT)
    draw_text(canvas, get_phase_label(phase), (PANEL_X + 40, 96), scale=0.66, color=player_color, thickness=2)
    draw_badge(
        canvas,
        PANEL_X + 40,
        106,
        f"Letra {estado.get('letra_estavel') or estado.get('letra') or '--'}",
        COLOR_STATUS_BG,
        COLOR_TEXT,
    )

    draw_card(canvas, (PANEL_X + 18, 154), (card_right, 338), "PLACAR", fill_color=COLOR_WOOD_SOFT, border_color=COLOR_BORDER_SOFT)
    player_one_active = duelo.get("jogador_atual") == PLAYER_ONE_ID
    player_two_active = duelo.get("jogador_atual") == PLAYER_TWO_ID

    draw_panel(
        canvas,
        (PANEL_X + 34, 192),
        (card_right - 16, 250),
        PLAYER_ONE_FILL if player_one_active else COLOR_WOOD_LIGHT,
        COLOR_WARNING if player_one_active else COLOR_BORDER_SOFT,
        2,
    )
    draw_text(canvas, duelo.get("nome_oponente_1", "Oponente 1"), (PANEL_X + 52, 226), scale=0.58, color=PLAYER_ONE_COLOR, thickness=2)
    draw_text_right(canvas, fmt_time(duelo.get("tempo_oponente_1")), card_right - 36, 226, scale=0.64, color=COLOR_TEXT, thickness=2)
    draw_lives(canvas, duelo.get("vidas_oponente_1", 0), duelo.get("vidas_maximas", 0), PANEL_X + 50, 242, PLAYER_ONE_COLOR)
    if player_one_active:
        draw_badge(canvas, card_right - 126, 202, "VEZ", COLOR_STATUS_BG, COLOR_TEXT)

    draw_panel(
        canvas,
        (PANEL_X + 34, 266),
        (card_right - 16, 324),
        PLAYER_TWO_FILL if player_two_active else COLOR_WOOD_LIGHT,
        COLOR_WARNING if player_two_active else COLOR_BORDER_SOFT,
        2,
    )
    draw_text(canvas, duelo.get("nome_oponente_2", "Oponente 2"), (PANEL_X + 52, 300), scale=0.58, color=PLAYER_TWO_COLOR, thickness=2)
    draw_text_right(canvas, fmt_time(duelo.get("tempo_oponente_2")), card_right - 36, 290, scale=0.64, color=COLOR_TEXT, thickness=2)
    draw_lives(canvas, duelo.get("vidas_oponente_2", 0), duelo.get("vidas_maximas", 0), PANEL_X + 50, 316, PLAYER_TWO_COLOR)
    if player_two_active:
        draw_badge(canvas, card_right - 126, 276, "VEZ", COLOR_STATUS_BG, COLOR_TEXT)

    draw_card(canvas, (PANEL_X + 18, 360), (card_right, 486), "CRONOMETRO", fill_color=COLOR_WOOD_LIGHT, border_color=COLOR_BORDER_SOFT)
    draw_text(canvas, "Tempo atual", (PANEL_X + 40, 402), scale=0.5, color=COLOR_MUTED, thickness=1)
    draw_text(canvas, fmt_time(duelo.get("tempo_atual")), (PANEL_X + 40, 454), scale=1.18, color=COLOR_WARNING, thickness=3)
    draw_text(canvas, "Tempo a bater", (PANEL_X + 328, 404), scale=0.48, color=COLOR_MUTED, thickness=1)
    draw_text(canvas, fmt_time(duelo.get("tempo_a_bater")), (PANEL_X + 328, 442), scale=0.72, color=COLOR_ACCENT, thickness=2)

    draw_card(canvas, (PANEL_X + 18, 506), (card_right, 620), "MENSAGENS", fill_color=COLOR_WOOD_SOFT, border_color=COLOR_BORDER_SOFT)
    feedback_lines = wrap_text(duelo.get("feedback", ""), max_chars=37)
    for index, line in enumerate(feedback_lines[:2]):
        draw_text(canvas, line, (PANEL_X + 40, 554 + index * 28), scale=0.54, color=COLOR_SUCCESS, thickness=2)

    transition_lines = wrap_text(duelo.get("mensagem_transicao", ""), max_chars=40)
    for index, line in enumerate(transition_lines[:2]):
        draw_text(canvas, line, (PANEL_X + 40, 602 + index * 20), scale=0.46, color=COLOR_TEXT_SOFT, thickness=1)

    cv2.rectangle(canvas, (PANEL_X + 18, 640), (card_right, 696), COLOR_CONTROLS, -1)
    cv2.rectangle(canvas, (PANEL_X + 18, 640), (card_right, 696), COLOR_BORDER_SOFT, 3)
    draw_text(canvas, "[S] Iniciar | [ESPACO] Confirmar | [ENTER] Validar", (PANEL_X + 30, 664), scale=0.39, color=COLOR_TEXT, thickness=1)
    draw_text(canvas, "[T] Trocar | [N] Nova palavra | [R] Reiniciar | [C] Limpar", (PANEL_X + 30, 686), scale=0.37, color=COLOR_TEXT_SOFT, thickness=1)


def draw_phase_overlay(canvas, duelo):
    phase = duelo.get("fase", "")
    if phase == "jogando":
        return

    if phase == "aguardando_inicio":
        title = "Rodada pronta"
        subtitle = f"Pressione S para iniciar a vez de {duelo.get('nome_oponente_1', 'Oponente 1')}"
        accent = tuple(duelo.get("jogador_atual_cor_bgr", [255, 255, 255]))
    elif phase == "troca_jogador":
        title = "Troca de jogador"
        subtitle = (
            duelo.get("mensagem_transicao", "")
            or f"Pressione T para iniciar a vez de {duelo.get('nome_oponente_2', 'Oponente 2')}"
        )
        accent = PLAYER_TWO_COLOR
    else:
        winner = duelo.get("vencedor_nome") or "Empate"
        title = f"Resultado: {winner}"
        subtitle = duelo.get("motivo_vitoria", "") or "Pressione N para nova palavra"
        accent = COLOR_SUCCESS if duelo.get("vencedor") else COLOR_WARNING

    overlay = canvas.copy()
    cv2.rectangle(overlay, (194, 218), (662, 452), (226, 235, 246), -1)
    cv2.addWeighted(overlay, 0.14, canvas, 0.86, 0, canvas)

    draw_panel(canvas, (204, 228), (652, 442), COLOR_WOOD, COLOR_BORDER_SOFT, 4)
    draw_text(canvas, title, (234, 280), scale=0.96, color=accent, thickness=3)

    y = 330
    for line in wrap_text(subtitle, max_chars=34)[:3]:
        draw_text(canvas, line, (234, y), scale=0.62, color=COLOR_TEXT, thickness=2)
        y += 34

    if phase == "resultado":
        draw_text(
            canvas,
            f"O1 {fmt_time(duelo.get('tempo_oponente_1'))}   O2 {fmt_time(duelo.get('tempo_oponente_2'))}",
            (234, 404),
            scale=0.68,
            color=COLOR_ACCENT,
            thickness=2,
        )
    elif phase == "troca_jogador":
        draw_text(
            canvas,
            f"Prepare {duelo.get('nome_oponente_2', 'Oponente 2')} para continuar.",
            (234, 404),
            scale=0.56,
            color=PLAYER_TWO_COLOR,
            thickness=2,
        )
    else:
        draw_text(
            canvas,
            f"Prepare {duelo.get('nome_oponente_1', 'Oponente 1')} na mesma camera.",
            (234, 404),
            scale=0.56,
            color=COLOR_TEXT_SOFT,
            thickness=1,
        )


def draw_panel_main(frame, duelo, estado):
    canvas = create_layout(frame)
    draw_header(canvas, duelo, estado)
    draw_right_panel(canvas, duelo, estado)
    draw_phase_overlay(canvas, duelo)
    return canvas


def build_duel_html() -> str:
    return """
<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Duelo de Tempo LIBRAS</title>
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
            --p1: #ff7a00;
            --p2: #2577ff;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            min-height: 100vh;
            font-family: "Segoe UI", Arial, sans-serif;
            color: var(--ink);
            background:
                linear-gradient(135deg, rgba(255,176,0,.18) 0 18%, transparent 18%),
                linear-gradient(45deg, rgba(124,92,255,.13) 0 16%, transparent 16%),
                linear-gradient(160deg, #fff8e8 0%, #e9f8ff 52%, #fff0f6 100%);
        }
        .screen {
            min-height: 100vh;
            padding: 22px;
            position: relative;
            z-index: 1;
        }
        .setup {
            min-height: calc(100vh - 44px);
            display: grid;
            place-items: center;
        }
        .setup-card, .panel {
            background: var(--surface);
            border: 2px solid var(--line);
            border-radius: 8px;
            box-shadow: 0 16px 40px rgba(29,45,68,.1);
        }
        .setup-card {
            width: min(720px, 100%);
            padding: 28px;
        }
        h1 { margin: 0; font-size: 2.1rem; letter-spacing: 0; }
        .lead { margin: 8px 0 22px; color: var(--muted); line-height: 1.45; }
        label {
            display: block;
            color: var(--muted);
            font-weight: 800;
            margin: 14px 0 8px;
        }
        input {
            width: 100%;
            min-height: 48px;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 0 14px;
            font: inherit;
            font-weight: 700;
            color: var(--ink);
        }
        .app {
            min-height: calc(100vh - 44px);
            display: none;
            grid-template-columns: minmax(360px, 42vw) 1fr;
            gap: 22px;
        }
        .camera-panel { align-self: start; padding: 16px; }
        .camera-panel { border-color: var(--cyan); }
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
        .grid .card:nth-child(1) { --card-color: var(--amber); }
        .grid .card:nth-child(2) { --card-color: var(--blue); }
        .grid .card:nth-child(3) { --card-color: var(--green); }
        .grid .card:nth-child(4) { --card-color: var(--pink); }
        .grid .card:nth-child(5) { --card-color: var(--purple); }
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
            font-size: 1.6rem;
            font-weight: 850;
            word-break: break-word;
        }
        .target { color: var(--amber); font-size: 2.4rem; }
        .letter { color: var(--blue); font-size: 3rem; line-height: 1; }
        .word { color: var(--green); }
        .players {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }
        .player.active { border-color: var(--blue); box-shadow: inset 0 0 0 2px rgba(47,111,237,.18); }
        #player-one { border-color: var(--p1); }
        #player-two { border-color: var(--p2); }
        .pname { display: flex; justify-content: space-between; gap: 10px; font-weight: 850; }
        .lives { margin-top: 12px; color: var(--red); font-size: 1.35rem; letter-spacing: .08em; }
        .phase {
            border-left: 5px solid var(--blue);
            background: #fff;
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
        button:nth-child(4) { border-color: var(--amber); background: #fff2bd; }
        button:nth-child(5) { border-color: var(--cyan); background: #dff8ff; }
        button:nth-child(6) { border-color: var(--pink); background: #ffe4ec; }
        @media (max-width: 980px) {
            .app { grid-template-columns: 1fr; }
            .grid, .players { grid-template-columns: 1fr; }
            .span2 { grid-column: 1; }
        }
        __FLOATING_HANDS_CSS__
    </style>
</head>
<body>
    __FLOATING_HANDS_MARKUP__
    <div class="screen">
        <section class="setup" id="setup">
            <form class="setup-card" id="name-form">
                <h1>Registro do Duelo</h1>
                <p class="lead">Digite os nomes dos dois jogadores para iniciar a partida.</p>
                <label for="p1">Jogador 1</label>
                <input id="p1" maxlength="18" value="Jogador 1">
                <label for="p2">Jogador 2</label>
                <input id="p2" maxlength="18" value="Jogador 2">
                <div class="actions" style="margin-top:18px">
                    <button class="primary" type="submit">Comecar duelo</button>
                    <button class="warn" type="button" onclick="window.pywebview.api.close()">Cancelar</button>
                </div>
            </form>
        </section>
        <section class="app" id="app">
            <section class="panel camera-panel">
                <div class="camera-top">
                    <span><i class="dot"></i>Camera</span>
                    <span id="hands">0 mao(s)</span>
                </div>
                <img id="camera" alt="Camera ao vivo">
            </section>
            <main class="panel info">
                <div>
                    <h1>Duelo de Tempo</h1>
                    <p class="lead" id="phase-label">Aguardando inicio</p>
                </div>
                <section class="grid">
                    <article class="card span2">
                        <div class="label">Palavra alvo</div>
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
                        <div class="label">Tempo atual</div>
                        <div class="value" id="current-time">--</div>
                    </article>
                    <article class="card wide phase">
                        <div class="label">Mensagem</div>
                        <div class="value" id="feedback">Prepare a rodada.</div>
                    </article>
                </section>
                <section class="players">
                    <article class="card player" id="player-one">
                        <div class="pname"><span id="p1-name">Jogador 1</span><span id="p1-time">--</span></div>
                        <div class="lives" id="p1-lives"></div>
                    </article>
                    <article class="card player" id="player-two">
                        <div class="pname"><span id="p2-name">Jogador 2</span><span id="p2-time">--</span></div>
                        <div class="lives" id="p2-lives"></div>
                    </article>
                </section>
                <div class="actions">
                    <button class="good" onclick="action('iniciar_duelo')">S Iniciar</button>
                    <button class="primary" onclick="action('confirmar_letra')">Espaco Confirmar</button>
                    <button onclick="action('validar_palavra_duelo')">Enter Validar</button>
                    <button onclick="action('trocar_jogador_duelo')">T Trocar</button>
                    <button onclick="action('proxima_palavra')">N Nova palavra</button>
                    <button onclick="action('reiniciar_duelo')">R Reiniciar</button>
                    <button onclick="action('limpar_palavra')">C Limpar</button>
                    <button class="warn" onclick="window.pywebview.api.close()">ESC Sair</button>
                </div>
            </main>
        </section>
    </div>
    <script>
        document.getElementById("name-form").addEventListener("submit", (event) => {
            event.preventDefault();
            window.pywebview.api.set_names(
                document.getElementById("p1").value,
                document.getElementById("p2").value
            );
            document.getElementById("setup").style.display = "none";
            document.getElementById("app").style.display = "grid";
        });
        function action(name) { window.pywebview.api.action(name); }
        function lives(current, max) {
            const filled = "V ".repeat(Math.max(0, current || 0));
            const empty = "- ".repeat(Math.max(0, (max || 0) - (current || 0)));
            return filled + empty;
        }
        function updateDuel(cameraBase64, estado, duelo) {
            document.getElementById("camera").src = "data:image/jpeg;base64," + cameraBase64;
            document.getElementById("hands").textContent = (estado.maos_detectadas || 0) + " mao(s)";
            document.getElementById("target").textContent = duelo.palavra_alvo || "--";
            document.getElementById("letter").textContent = estado.letra_estavel || estado.letra || "--";
            document.getElementById("word").textContent = estado.palavra || "_";
            document.getElementById("current-time").textContent = duelo.tempo_atual == null ? "--" : duelo.tempo_atual.toFixed(2) + "s";
            document.getElementById("phase-label").textContent = duelo.fase_label || duelo.fase || "";
            document.getElementById("feedback").textContent =
                duelo.motivo_vitoria || duelo.mensagem_transicao || duelo.feedback || "Prepare a rodada.";
            document.getElementById("p1-name").textContent = duelo.nome_oponente_1 || "Jogador 1";
            document.getElementById("p2-name").textContent = duelo.nome_oponente_2 || "Jogador 2";
            document.getElementById("p1-time").textContent = duelo.tempo_oponente_1 == null ? "--" : duelo.tempo_oponente_1.toFixed(2) + "s";
            document.getElementById("p2-time").textContent = duelo.tempo_oponente_2 == null ? "--" : duelo.tempo_oponente_2.toFixed(2) + "s";
            document.getElementById("p1-lives").textContent = lives(duelo.vidas_oponente_1, duelo.vidas_maximas);
            document.getElementById("p2-lives").textContent = lives(duelo.vidas_oponente_2, duelo.vidas_maximas);
            document.getElementById("player-one").classList.toggle("active", duelo.jogador_atual === "oponente_1");
            document.getElementById("player-two").classList.toggle("active", duelo.jogador_atual === "oponente_2");
        }
        document.addEventListener("keydown", (event) => {
            const key = event.key.toLowerCase();
            if (document.getElementById("app").style.display !== "grid") return;
            if (key === "s") action("iniciar_duelo");
            if (event.key === " ") { event.preventDefault(); action("confirmar_letra"); }
            if (event.key === "Enter") action("validar_palavra_duelo");
            if (key === "t") action("trocar_jogador_duelo");
            if (key === "n") action("proxima_palavra");
            if (key === "r") action("reiniciar_duelo");
            if (key === "c") action("limpar_palavra");
            if (event.key === "Escape") window.pywebview.api.close();
        });
    </script>
</body>
</html>
""".replace("__FLOATING_HANDS_CSS__", get_floating_hands_css()).replace(
        "__FLOATING_HANDS_MARKUP__", get_floating_hands_markup()
    )


class DuelApi:
    def __init__(self):
        self._actions = queue.Queue()
        self._window = None
        self._closed = False
        self._player_names = None

    def set_names(self, player_one, player_two):
        self._player_names = {
            PLAYER_ONE_ID: normalize_player_name(player_one, "Jogador 1"),
            PLAYER_TWO_ID: normalize_player_name(player_two, "Jogador 2"),
        }

    def action(self, action_name):
        self._actions.put(str(action_name))

    def close(self):
        self._closed = True
        if self._window:
            self._window.destroy()


async def process_duel_webview_actions(websocket, api):
    while True:
        try:
            action_name = api._actions.get_nowait()
        except queue.Empty:
            return
        await send_action(websocket, action_name)


async def run_webview_duel(window, api):
    while api._player_names is None and not api._closed:
        await asyncio.sleep(0.05)
    if api._closed:
        return

    player_names = api._player_names
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not camera.isOpened():
        raise RuntimeError("Erro ao acessar webcam local")

    try:
        async with connect(SERVER_URL, max_size=2**22) as websocket:
            while not api._closed:
                ok, frame = camera.read()
                if not ok:
                    raise RuntimeError("Erro ao capturar frame da webcam")

                await websocket.send(json.dumps({"frame": encode_frame(frame)}))
                response = json.loads(await websocket.recv())
                if response.get("tipo") == "erro":
                    raise RuntimeError(response.get("mensagem", "Erro desconhecido do servidor"))

                estado = response.get("estado", {})
                duelo = enrich_duel_labels(response.get("duelo", {}), player_names)
                duelo["nome_oponente_1"] = player_names[PLAYER_ONE_ID]
                duelo["nome_oponente_2"] = player_names[PLAYER_TWO_ID]
                duelo["fase_label"] = get_phase_label(duelo.get("fase", ""))
                camera_image = encode_frame(cv2.resize(frame, (640, 480)), quality=68)
                window.evaluate_js(
                    "window.updateDuel("
                    + json.dumps(camera_image)
                    + ", "
                    + json.dumps(estado)
                    + ", "
                    + json.dumps(duelo)
                    + ");"
                )
                await process_duel_webview_actions(websocket, api)
                await asyncio.sleep(0.02)
    finally:
        api._closed = True
        camera.release()


def start_webview_duel(window, api):
    try:
        asyncio.run(run_webview_duel(window, api))
    except Exception as exc:
        print(f"Erro na interface HTML do duelo: {exc}")
        api._closed = True


def run_webview_app():
    api = DuelApi()
    window = webview.create_window(
        WINDOW_NAME,
        html=build_duel_html(),
        js_api=api,
        width=1220,
        height=760,
        resizable=True,
    )
    api._window = window
    window.events.closed += lambda: setattr(api, "_closed", True)
    webview.start(start_webview_duel, (window, api), debug=False)


async def send_action(websocket, action):
    await websocket.send(json.dumps({"acao": action}))
    return json.loads(await websocket.recv())


async def run_cv2_duel():
    player_names = collect_player_names()
    if player_names is None:
        return

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
                    raise RuntimeError(
                        response.get("mensagem", "Erro desconhecido do servidor")
                    )

                estado = response.get("estado", {})
                duelo = enrich_duel_labels(response.get("duelo", {}), player_names)
                duelo["nome_oponente_1"] = player_names[PLAYER_ONE_ID]
                duelo["nome_oponente_2"] = player_names[PLAYER_TWO_ID]
                canvas = draw_panel_main(frame, duelo, estado)

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


def main():
    if webview is not None:
        run_webview_app()
        return

    print("pywebview nao esta instalado; abrindo duelo com interface antiga em OpenCV.")
    asyncio.run(run_cv2_duel())


if __name__ == "__main__":
    main()
