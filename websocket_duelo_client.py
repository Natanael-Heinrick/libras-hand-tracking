import asyncio
import base64
import json

import cv2
import numpy as np
from websockets.asyncio.client import connect


SERVER_URL = "ws://127.0.0.1:8765/duelo"
WINDOW_NAME = "Duelo de Tempo LIBRAS"
NAME_WINDOW = "Registro dos Jogadores"
FRAME_WIDTH = 1460
FRAME_HEIGHT = 720
CAMERA_WIDTH = 820
PANEL_X = 850
PANEL_WIDTH = 580
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
PLAYER_ONE_ID = "oponente_1"
PLAYER_TWO_ID = "oponente_2"


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


def draw_text_right(
    canvas, text, x_right, baseline_y, scale=0.8, color=COLOR_TEXT, thickness=2
):
    text = str(text)
    (text_width, _), _ = cv2.getTextSize(
        text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness
    )
    draw_text(
        canvas,
        text,
        (x_right - text_width, baseline_y),
        scale=scale,
        color=color,
        thickness=thickness,
    )


def draw_card(canvas, top_left, bottom_right, title, border_color=COLOR_BORDER):
    x1, y1 = top_left
    x2, y2 = bottom_right
    cv2.rectangle(canvas, (x1, y1), (x2, y2), COLOR_PANEL, -1)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), border_color, 2)
    draw_text(
        canvas,
        title,
        (x1 + 18, y1 + 32),
        scale=0.58,
        color=(230, 236, 255),
        thickness=2,
    )


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
            canvas = np.full((520, 940, 3), COLOR_BG, dtype=np.uint8)
            cv2.rectangle(canvas, (24, 24), (916, 496), (26, 36, 54), -1)
            cv2.rectangle(canvas, (24, 24), (916, 496), COLOR_BORDER, 2)

            draw_text(canvas, "Registro do Duelo", (60, 88), scale=1.0, thickness=3)
            draw_text(
                canvas,
                "Esses nomes valem apenas para esta abertura do jogo.",
                (60, 128),
                scale=0.66,
                color=COLOR_MUTED,
            )
            draw_text(
                canvas,
                "ENTER confirma | TAB troca campo | BACKSPACE apaga | ESC cancela",
                (60, 166),
                scale=0.52,
                color=COLOR_TEXT,
            )

            for index, player_id in enumerate(order):
                box_y1 = 220 + index * 130
                box_y2 = box_y1 + 82
                is_active = index == active_index
                border = PLAYER_ONE_COLOR if player_id == PLAYER_ONE_ID else PLAYER_TWO_COLOR
                if not is_active:
                    border = (90, 110, 145)

                draw_text(
                    canvas,
                    labels[player_id],
                    (60, box_y1 - 18),
                    scale=0.66,
                    color=PLAYER_ONE_COLOR if player_id == PLAYER_ONE_ID else PLAYER_TWO_COLOR,
                    thickness=2,
                )
                cv2.rectangle(canvas, (56, box_y1), (884, box_y2), (19, 28, 44), -1)
                cv2.rectangle(canvas, (56, box_y1), (884, box_y2), border, 2)

                current_text = values[player_id]
                if current_text:
                    display = current_text
                    color = COLOR_TEXT
                else:
                    display = placeholders[player_id]
                    color = (120, 136, 164)

                draw_text(canvas, display, (78, box_y1 + 49), scale=0.72, color=color, thickness=2)

            ready = all(values[player_id].strip() for player_id in order)
            footer_color = COLOR_SUCCESS if ready else COLOR_WARNING
            footer_text = "Pressione ENTER para continuar" if ready else "Preencha os dois nomes para continuar"
            draw_text(canvas, footer_text, (60, 456), scale=0.7, color=footer_color, thickness=2)

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


def draw_lives(canvas, label, current, max_lives, start_x, y, color):
    draw_text(canvas, label, (start_x, y), scale=0.62, color=color, thickness=2)
    x = start_x + 72
    for index in range(max_lives):
        filled = index < current
        fill_color = color if filled else (80, 90, 110)
        cv2.circle(canvas, (x + 10, y - 8), 9, fill_color, -1)
        cv2.circle(canvas, (x + 10, y - 8), 9, (235, 240, 248), 1)
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
    cv2.rectangle(
        overlay, (0, FRAME_HEIGHT - 140), (CAMERA_WIDTH, FRAME_HEIGHT), (12, 18, 30), -1
    )
    cv2.addWeighted(overlay, 0.25, canvas, 0.75, 0, canvas)

    cv2.rectangle(
        canvas, (CAMERA_WIDTH, 0), (FRAME_WIDTH, FRAME_HEIGHT), (16, 22, 34), -1
    )
    cv2.rectangle(
        canvas,
        (CAMERA_WIDTH + 6, 14),
        (FRAME_WIDTH - 14, FRAME_HEIGHT - 14),
        (40, 56, 84),
        2,
    )
    return canvas


def draw_header(canvas, duelo, estado):
    player_color = tuple(duelo.get("jogador_atual_cor_bgr", [255, 255, 255]))
    draw_text(canvas, "Duelo de Tempo LIBRAS", (28, 54), scale=1.0, thickness=3)
    draw_text(
        canvas,
        f"Palavra alvo: {duelo.get('palavra_alvo', '')}",
        (28, 95),
        scale=0.82,
        color=COLOR_ACCENT,
    )
    draw_text(
        canvas,
        f"Sua palavra: {estado.get('palavra', '') or '_'}",
        (28, 132),
        scale=0.88,
        color=(255, 240, 120),
        thickness=2,
    )
    draw_text(
        canvas,
        f"Jogador atual: {duelo.get('jogador_atual_nome', duelo.get('jogador_atual_label', ''))}",
        (28, 170),
        scale=0.78,
        color=player_color,
        thickness=3,
    )


def draw_right_panel(canvas, duelo, estado):
    phase = duelo.get("fase", "")
    player_color = tuple(duelo.get("jogador_atual_cor_bgr", [255, 255, 255]))
    card_right = PANEL_X + PANEL_WIDTH
    inner_mid = PANEL_X + 300

    draw_card(
        canvas,
        (PANEL_X, 26),
        (card_right, 116),
        "STATUS DA RODADA",
        border_color=player_color,
    )
    draw_text(
        canvas, "-", (PANEL_X + 250, 32), scale=0.58, color=(230, 236, 255), thickness=2
    )
    draw_text(
        canvas,
        get_phase_label(phase),
        (PANEL_X + 270, 32),
        scale=0.54,
        color=player_color,
        thickness=2,
    )
    draw_text(
        canvas,
        f"Letra atual: {estado.get('letra_estavel') or estado.get('letra') or '--'}",
        (PANEL_X + 18, 96),
        scale=0.58,
        color=COLOR_SUCCESS,
    )

    draw_card(canvas, (PANEL_X, 136), (card_right, 320), "PLACAR")
    draw_text(
        canvas,
        duelo.get("nome_oponente_1", "Oponente 1"),
        (PANEL_X + 18, 188),
        scale=0.59,
        color=PLAYER_ONE_COLOR,
        thickness=2,
    )
    draw_text_right(
        canvas,
        fmt_time(duelo.get("tempo_oponente_1")),
        inner_mid,
        188,
        scale=0.72,
        color=PLAYER_ONE_COLOR,
        thickness=2,
    )
    draw_lives(
        canvas,
        "Vidas",
        duelo.get("vidas_oponente_1", 0),
        duelo.get("vidas_maximas", 0),
        PANEL_X + 18,
        206,
        PLAYER_ONE_COLOR,
    )

    draw_text(
        canvas,
        duelo.get("nome_oponente_2", "Oponente 2"),
        (PANEL_X + 18, 250),
        scale=0.59,
        color=PLAYER_TWO_COLOR,
        thickness=2,
    )
    draw_text_right(
        canvas,
        fmt_time(duelo.get("tempo_oponente_2")),
        inner_mid,
        250,
        scale=0.72,
        color=PLAYER_TWO_COLOR,
        thickness=2,
    )
    draw_lives(
        canvas,
        "Vidas",
        duelo.get("vidas_oponente_2", 0),
        duelo.get("vidas_maximas", 0),
        PANEL_X + 18,
        280,
        PLAYER_TWO_COLOR,
    )

    draw_card(canvas, (PANEL_X, 306), (card_right, 430), "CRONOMETRO")
    draw_text(canvas, "Tempo atual", (PANEL_X + 18, 362), scale=0.54, color=COLOR_MUTED)
    draw_text(
        canvas,
        fmt_time(duelo.get("tempo_atual")),
        (PANEL_X + 18, 399),
        scale=1.0,
        color=COLOR_TEXT,
        thickness=3,
    )
    draw_text(
        canvas, "Tempo a bater", (inner_mid + 20, 362), scale=0.54, color=COLOR_MUTED
    )
    draw_text(
        canvas,
        fmt_time(duelo.get("tempo_a_bater")),
        (inner_mid + 20, 399),
        scale=0.86,
        color=COLOR_WARNING,
        thickness=2,
    )

    draw_card(canvas, (PANEL_X, 450), (card_right, 620), "MENSAGENS")
    feedback_lines = wrap_text(duelo.get("feedback", ""), max_chars=37)
    for index, line in enumerate(feedback_lines[:3]):
        draw_text(
            canvas,
            line,
            (PANEL_X + 18, 522 + index * 28),
            scale=0.58,
            color=COLOR_SUCCESS,
        )

    transition_lines = wrap_text(duelo.get("mensagem_transicao", ""), max_chars=44)
    for index, line in enumerate(transition_lines[:3]):
        draw_text(
            canvas,
            line,
            (PANEL_X + 18, 592 + index * 18),
            scale=0.50,
            color=(255, 220, 170),
        )

    draw_card(canvas, (PANEL_X, 640), (card_right, 704), "")
    draw_text(
        canvas,
        "S inicia | ESPACO confirma | ENTER valida",
        (PANEL_X + 18, 678),
        scale=0.44,
        color=COLOR_TEXT,
    )
    draw_text(
        canvas,
        "T troca | N nova palavra | R reinicia | C limpa",
        (PANEL_X + 18, 698),
        scale=0.44,
        color=COLOR_TEXT,
    )

    csv_lines = wrap_text(f"CSV: {duelo.get('fonte_dados', '')}", max_chars=58)
    for index, line in enumerate(csv_lines[:2]):
        draw_text(
            canvas,
            line,
            (PANEL_X, 714 + index * 18),
            scale=0.42,
            color=(150, 170, 205),
            thickness=1,
        )


def draw_phase_overlay(canvas, duelo):
    phase = duelo.get("fase", "")
    if phase == "jogando":
        return

    if phase == "aguardando_inicio":
        title = "Rodada pronta"
        subtitle = f"Pressione S para iniciar o tempo de {duelo.get('nome_oponente_1', 'Oponente 1')}"
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
        draw_text(
            canvas,
            f"Pressione T para liberar a vez de {duelo.get('nome_oponente_2', 'Oponente 2')}",
            (135, 445),
            scale=0.72,
            color=PLAYER_TWO_COLOR,
            thickness=2,
        )
    else:
        draw_text(
            canvas,
            f"Use a mesma camera e prepare {duelo.get('nome_oponente_1', 'Oponente 1')}",
            (135, 445),
            scale=0.72,
            color=COLOR_MUTED,
        )


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
