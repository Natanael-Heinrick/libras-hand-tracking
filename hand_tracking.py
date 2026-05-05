import asyncio
import base64
import json
import subprocess
import threading

import cv2
import numpy as np
from websockets.asyncio.client import connect


SERVER_URL = "ws://127.0.0.1:8765/alfabeto"
WINDOW_NAME = "Hand Tracking - Alfabeto"
FRAME_WIDTH = 860
FRAME_HEIGHT = 720
PANEL_WIDTH = 420
CANVAS_WIDTH = FRAME_WIDTH + PANEL_WIDTH
CANVAS_HEIGHT = FRAME_HEIGHT

COLOR_BG = (18, 24, 36)
COLOR_PANEL = (28, 38, 56)
COLOR_PANEL_ALT = (35, 49, 72)
COLOR_BORDER = (104, 168, 245)
COLOR_TEXT = (244, 247, 255)
COLOR_MUTED = (176, 190, 215)
COLOR_ACCENT = (110, 227, 255)
COLOR_SUCCESS = (134, 232, 165)
COLOR_WARNING = (255, 215, 120)
COLOR_CAMERA_SHADE = (12, 18, 30)


def draw_text_block(
    image,
    lines,
    start_x,
    start_y,
    line_height=28,
    scale=0.62,
    color=COLOR_TEXT,
    thickness=2,
):
    y = start_y
    for line in lines:
        cv2.putText(
            image,
            str(line),
            (start_x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            color,
            thickness,
            cv2.LINE_AA,
        )
        y += line_height


def draw_text(
    image,
    text,
    position,
    scale=0.72,
    color=COLOR_TEXT,
    thickness=2,
):
    cv2.putText(
        image,
        str(text),
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        color,
        thickness,
        cv2.LINE_AA,
    )


def draw_card(
    canvas, top_left, bottom_right, title, fill=COLOR_PANEL, border=COLOR_BORDER
):
    x1, y1 = top_left
    x2, y2 = bottom_right
    cv2.rectangle(canvas, (x1, y1), (x2, y2), fill, -1)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), border, 2)
    if title:
        draw_text(
            canvas,
            title,
            (x1 + 18, y1 + 32),
            scale=0.58,
            color=COLOR_MUTED,
            thickness=2,
        )


def encode_frame(frame, quality=70):
    ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise RuntimeError("Nao foi possivel codificar o frame")

    return base64.b64encode(buffer.tobytes()).decode("utf-8")


def falar_texto(texto):
    texto = (texto or "").strip()
    if not texto:
        return

    texto_seguro = texto.replace("'", "''")
    comando = (
        "Add-Type -AssemblyName System.Speech; "
        "$voz = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        f"$voz.Speak('{texto_seguro}')"
    )

    def _executar():
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", comando],
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

    threading.Thread(target=_executar, daemon=True).start()


def build_round_label(estado):
    return estado.get("rodada") or estado.get("fase") or "Modo livre"


def build_points_label(estado):
    points = estado.get("pontos")
    if points is None:
        return "--"
    return str(points)


def build_progress_label(estado):
    palavra = estado.get("palavra", "")
    maos = estado.get("maos_detectadas", 0)
    return f"{len(palavra)} letras montadas  |  {maos} mao(s) detectada(s)"


def create_layout(frame):
    resized = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
    canvas = np.full((CANVAS_HEIGHT, CANVAS_WIDTH, 3), COLOR_BG, dtype=np.uint8)
    canvas[:, :FRAME_WIDTH] = resized

    overlay = canvas.copy()
    cv2.rectangle(overlay, (0, 0), (FRAME_WIDTH, 110), COLOR_CAMERA_SHADE, -1)
    cv2.rectangle(
        overlay,
        (0, FRAME_HEIGHT - 72),
        (FRAME_WIDTH, FRAME_HEIGHT),
        COLOR_CAMERA_SHADE,
        -1,
    )
    cv2.addWeighted(overlay, 0.34, canvas, 0.66, 0, canvas)

    cv2.rectangle(
        canvas, (FRAME_WIDTH, 0), (CANVAS_WIDTH, CANVAS_HEIGHT), (20, 28, 42), -1
    )
    cv2.rectangle(
        canvas,
        (FRAME_WIDTH + 8, 12),
        (CANVAS_WIDTH - 14, CANVAS_HEIGHT - 14),
        (44, 62, 92),
        2,
    )
    return canvas


def draw_camera_overlay(canvas, letra_atual, letra_estavel):
    draw_text(canvas, "LIBRAS HERO", (28, 50), scale=1.0, color=COLOR_TEXT, thickness=3)
    draw_text(
        canvas,
        "Reconheca a letra, confirme e monte sua palavra.",
        (28, 84),
        scale=0.6,
        color=COLOR_MUTED,
        thickness=1,
    )

    display_letter = letra_estavel or letra_atual or "--"
    draw_text(
        canvas, "LETRA ATUAL", (28, 642), scale=0.56, color=COLOR_MUTED, thickness=2
    )
    draw_text(
        canvas, display_letter, (28, 695), scale=1.55, color=COLOR_WARNING, thickness=4
    )


def draw_side_panel(canvas, estado, letra_atual, letra_estavel, show_debug):
    panel_x = FRAME_WIDTH + 22
    panel_right = CANVAS_WIDTH - 26

    draw_card(
        canvas,
        (panel_x, 24),
        (panel_right, 124),
        "OBJETIVO DA RODADA",
        fill=COLOR_PANEL_ALT,
        border=COLOR_ACCENT,
    )
    draw_text(
        canvas,
        "Monte sua palavra em LIBRAS",
        (panel_x + 18, 72),
        scale=0.86,
        color=COLOR_TEXT,
        thickness=2,
    )
    draw_text(
        canvas,
        f"Letra estavel: {letra_estavel or '--'}",
        (panel_x + 18, 104),
        scale=0.64,
        color=COLOR_SUCCESS,
        thickness=2,
    )

    draw_card(
        canvas,
        (panel_x, 146),
        (panel_right, 256),
        "SUA PALAVRA",
        fill=COLOR_PANEL,
        border=COLOR_BORDER,
    )
    palavra = estado.get("palavra", "") or "_"
    draw_text(
        canvas,
        palavra,
        (panel_x + 18, 214),
        scale=1.18,
        color=COLOR_ACCENT,
        thickness=3,
    )

    draw_card(
        canvas,
        (panel_x, 278),
        (panel_right, 430),
        "PROGRESSO",
        fill=COLOR_PANEL_ALT,
        border=COLOR_BORDER,
    )
    draw_text(
        canvas,
        "Rodada",
        (panel_x + 18, 330),
        scale=0.54,
        color=COLOR_MUTED,
        thickness=2,
    )
    draw_text(
        canvas,
        build_round_label(estado),
        (panel_x + 18, 362),
        scale=0.82,
        color=COLOR_TEXT,
        thickness=2,
    )
    draw_text(
        canvas,
        "Pontos",
        (panel_x + 18, 402),
        scale=0.54,
        color=COLOR_MUTED,
        thickness=2,
    )
    draw_text(
        canvas,
        build_points_label(estado),
        (panel_x + 118, 402),
        scale=0.92,
        color=COLOR_WARNING,
        thickness=3,
    )
    draw_text(
        canvas,
        build_progress_label(estado),
        (panel_x + 18, 424),
        scale=0.5,
        color=COLOR_SUCCESS,
        thickness=1,
    )

    draw_card(
        canvas,
        (panel_x, 452),
        (panel_right, 566),
        "CONTROLES",
        fill=COLOR_PANEL,
        border=COLOR_BORDER,
    )
    draw_text_block(
        canvas,
        [
            "ESPACO confirma a letra",
            "C limpa a palavra",
            "P fala a resposta montada",
            "TAB mostra debug",
            "ESC sai",
        ],
        panel_x + 18,
        494,
        line_height=22,
        scale=0.51,
        color=COLOR_TEXT,
        thickness=1,
    )

    status_text = (
        "Aguardando leitura da mao"
        if not letra_atual
        else f"Leitura instantanea: {letra_atual}"
    )
    status_color = COLOR_MUTED if not letra_atual else COLOR_SUCCESS
    draw_card(
        canvas,
        (panel_x, 588),
        (panel_right, 680),
        "STATUS",
        fill=COLOR_PANEL_ALT,
        border=COLOR_BORDER,
    )
    draw_text(
        canvas,
        status_text,
        (panel_x + 18, 636),
        scale=0.64,
        color=status_color,
        thickness=2,
    )

    if show_debug:
        draw_card(
            canvas,
            (36, 118),
            (364, 330),
            "DEBUG",
            fill=(16, 24, 36),
            border=(92, 126, 170),
        )
        deteccao = (estado.get("deteccoes") or [{}])[0]
        dedos = deteccao.get("dedos", [])
        metricas_debug = deteccao.get("metricas_debug", {})
        metric_lines = [
            f"Dedos: {dedos}",
            f"Maos: {estado.get('maos_detectadas', 0)}",
            "",
        ]
        metric_lines.extend(
            f"{chave}: {valor}" for chave, valor in list(metricas_debug.items())[:6]
        )
        draw_text_block(
            canvas,
            metric_lines,
            54,
            156,
            line_height=24,
            scale=0.48,
            color=(214, 233, 255),
            thickness=1,
        )


def render_interface(frame, estado, show_debug):
    letra_atual = estado.get("letra", "")
    letra_estavel = estado.get("letra_estavel") or letra_atual or ""
    canvas = create_layout(frame)
    draw_camera_overlay(canvas, letra_atual, letra_estavel)
    draw_side_panel(canvas, estado, letra_atual, letra_estavel, show_debug)
    return canvas


async def main():
    show_debug = False
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
                canvas = render_interface(frame, estado, show_debug)

                cv2.imshow(WINDOW_NAME, canvas)
                key = cv2.waitKeyEx(1)

                if key == ord(" "):
                    await websocket.send(json.dumps({"acao": "confirmar_letra"}))
                    response = json.loads(await websocket.recv())
                    if response.get("tipo") == "erro":
                        raise RuntimeError(
                            response.get("mensagem", "Erro ao confirmar letra")
                        )
                elif key == ord("c"):
                    await websocket.send(json.dumps({"acao": "limpar_palavra"}))
                    response = json.loads(await websocket.recv())
                    if response.get("tipo") == "erro":
                        raise RuntimeError(
                            response.get("mensagem", "Erro ao limpar palavra")
                        )
                elif key == ord("p"):
                    falar_texto(estado.get("palavra", ""))
                elif key == 9:
                    show_debug = not show_debug
                elif key == 27:
                    break
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    asyncio.run(main())
