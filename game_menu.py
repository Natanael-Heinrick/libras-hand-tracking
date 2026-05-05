from __future__ import annotations

from pathlib import Path
import socket
import subprocess
import sys
import time

import cv2
import numpy as np

from loja.state import get_points_label


WINDOW_NAME = "Menu de Jogos LIBRAS"
PROJECT_ROOT = Path(__file__).resolve().parent
PYTHON_EXECUTABLE = sys.executable
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8765
CANVAS_WIDTH = 960
CANVAS_HEIGHT = 540
BUTTON_WIDTH = 420
BUTTON_HEIGHT = 48
BUTTON_SPACING = 16
BUTTON_START_Y = 164
SKY_HEIGHT = 340
FOOTER_HEIGHT = 46

ARROW_UP_KEYS = {2490368}
ARROW_DOWN_KEYS = {2621440}
ENTER_KEYS = {10, 13}

BUTTONS = [
    {
        "label": "Fotos",
        "description": "Mostra imagens de objetos e voce soletra o nome.",
        "entry_type": "script",
        "entry": "websocket_exercicios_client.py",
        "args": ["fotos"],
        "requires_server": True,
    },
    {
        "label": "Palavras",
        "description": "Treino classico com palavras alvo vindas do CSV.",
        "entry_type": "script",
        "entry": "websocket_exercicios_client.py",
        "args": ["palavras"],
        "requires_server": True,
    },
    {
        "label": "Imagens de Letras",
        "description": "Sequencia de imagens de maos e resposta por texto.",
        "entry_type": "module",
        "entry": "quiz_visual_libras.quiz_visual_game",
        "args": [],
        "requires_server": False,
    },
    {
        "label": "Loja",
        "description": "Use seus pontos para comprar e equipar looks do personagem.",
        "entry_type": "module",
        "entry": "loja.shop_app",
        "args": [],
        "requires_server": False,
    },
    {
        "label": "Duelo de Tempo",
        "description": "Competicao local entre dois jogadores em uma mesma camera.",
        "entry_type": "script",
        "entry": "websocket_duelo_client.py",
        "args": [],
        "requires_server": True,
    },
]

selected_index: int = 0


def is_server_running() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((SERVER_HOST, SERVER_PORT)) == 0


def start_server_if_needed():
    if is_server_running():
        return

    subprocess.Popen(
        [PYTHON_EXECUTABLE, "websocket_server.py"],
        cwd=str(PROJECT_ROOT),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )
    time.sleep(1.5)


def launch_button(button: dict):
    if button["requires_server"]:
        start_server_if_needed()

    if button.get("entry_type") == "module":
        command = [PYTHON_EXECUTABLE, "-m", button["entry"], *button["args"]]
    else:
        command = [PYTHON_EXECUTABLE, button["entry"], *button["args"]]

    subprocess.Popen(
        command,
        cwd=str(PROJECT_ROOT),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )


def get_button_rect(index: int) -> tuple[int, int, int, int]:
    x = (CANVAS_WIDTH - BUTTON_WIDTH) // 2
    y = BUTTON_START_Y + index * (BUTTON_HEIGHT + BUTTON_SPACING)
    return x, y, x + BUTTON_WIDTH, y + BUTTON_HEIGHT


def draw_panel(
    canvas: np.ndarray,
    top_left: tuple[int, int],
    bottom_right: tuple[int, int],
    fill_color: tuple[int, int, int],
    border_color: tuple[int, int, int],
    border_thickness: int = 3,
):
    x1, y1 = top_left
    x2, y2 = bottom_right
    cv2.rectangle(canvas, (x1, y1), (x2, y2), fill_color, -1)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), border_color, border_thickness)


def draw_pixel_cloud(canvas: np.ndarray, x: int, y: int, size: int):
    color_main = (246, 246, 255)
    color_shadow = (214, 224, 244)
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
        cv2.rectangle(canvas, (x1, y1), (x1 + size, y1 + size), color_main, -1)
        cv2.rectangle(
            canvas,
            (x1, y1 + size - 4),
            (x1 + size, y1 + size),
            color_shadow,
            -1,
        )


def draw_pixel_background(canvas: np.ndarray):
    for y in range(SKY_HEIGHT):
        ratio = y / max(1, SKY_HEIGHT - 1)
        color = (
            int(255 - 18 * ratio),
            int(178 + 48 * ratio),
            int(78 + 72 * ratio),
        )
        cv2.line(canvas, (0, y), (CANVAS_WIDTH, y), color, 1)

    draw_pixel_cloud(canvas, 90, 54, 16)
    draw_pixel_cloud(canvas, 448, 36, 12)
    draw_pixel_cloud(canvas, 680, 74, 14)

    hill_color = (62, 120, 62)
    cv2.circle(canvas, (120, SKY_HEIGHT + 36), 110, hill_color, -1)
    cv2.circle(canvas, (350, SKY_HEIGHT + 48), 155, hill_color, -1)
    cv2.circle(canvas, (790, SKY_HEIGHT + 36), 138, hill_color, -1)

    cv2.rectangle(
        canvas, (0, SKY_HEIGHT), (CANVAS_WIDTH, CANVAS_HEIGHT), (68, 146, 78), -1
    )
    cv2.rectangle(
        canvas, (0, SKY_HEIGHT), (CANVAS_WIDTH, SKY_HEIGHT + 14), (96, 190, 92), -1
    )
    cv2.rectangle(
        canvas, (0, SKY_HEIGHT + 14), (CANVAS_WIDTH, SKY_HEIGHT + 28), (56, 108, 50), -1
    )

    platform_top = SKY_HEIGHT - 58
    cv2.rectangle(
        canvas, (140, platform_top), (820, platform_top + 22), (102, 70, 40), -1
    )
    cv2.rectangle(
        canvas, (140, platform_top + 22), (820, platform_top + 44), (132, 93, 55), -1
    )
    for x in range(140, 820, 32):
        cv2.line(
            canvas, (x, platform_top + 22), (x, platform_top + 44), (90, 60, 38), 2
        )

    for x in range(0, CANVAS_WIDTH, 40):
        cv2.rectangle(
            canvas, (x, CANVAS_HEIGHT - 18), (x + 20, CANVAS_HEIGHT), (88, 78, 52), -1
        )
    cv2.rectangle(
        canvas, (0, CANVAS_HEIGHT - 18), (CANVAS_WIDTH, CANVAS_HEIGHT), (114, 92, 60), 2
    )


def draw_button(canvas: np.ndarray, idx: int, button: dict, is_selected: bool):
    x1, y1, x2, y2 = get_button_rect(idx)
    if is_selected:
        fill = (104, 216, 250)
        border = (255, 245, 170)
        shadow = (36, 88, 118)
        text_color = (22, 42, 64)
    else:
        fill = (47, 76, 112)
        border = (142, 190, 240)
        shadow = (22, 36, 62)
        text_color = (240, 245, 255)

    cv2.rectangle(canvas, (x1 + 6, y1 + 6), (x2 + 6, y2 + 6), shadow, -1)
    draw_panel(canvas, (x1, y1), (x2, y2), fill, border, 3)

    cv2.putText(
        canvas,
        str(idx + 1),
        (x1 + 16, y1 + 33),
        cv2.FONT_HERSHEY_DUPLEX,
        0.72,
        text_color,
        2,
    )
    cv2.putText(
        canvas,
        button["label"].upper(),
        (x1 + 56, y1 + 33),
        cv2.FONT_HERSHEY_DUPLEX,
        0.8,
        text_color,
        2,
    )

    if is_selected:
        cv2.rectangle(
            canvas, (x1 - 24, y1 + 10), (x1 - 10, y1 + 24), (255, 240, 160), -1
        )
        cv2.rectangle(
            canvas, (x2 + 10, y1 + 10), (x2 + 24, y1 + 24), (255, 240, 160), -1
        )


def draw_menu() -> np.ndarray:
    canvas = np.zeros((CANVAS_HEIGHT, CANVAS_WIDTH, 3), dtype=np.uint8)
    draw_pixel_background(canvas)

    draw_panel(canvas, (180, 20), (780, 92), (44, 74, 124), (252, 232, 150), 4)
    cv2.putText(
        canvas,
        "LIBRAS QUEST",
        (294, 64),
        cv2.FONT_HERSHEY_DUPLEX,
        1.35,
        (255, 255, 255),
        3,
    )
    cv2.putText(
        canvas,
        "Selecione uma aventura",
        (318, 87),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.56,
        (221, 234, 255),
        1,
    )

    draw_panel(canvas, (56, 118), (264, 170), (66, 104, 150), (171, 206, 255), 3)
    cv2.putText(
        canvas,
        "ATALHOS",
        (80, 142),
        cv2.FONT_HERSHEY_DUPLEX,
        0.7,
        (255, 245, 230),
        2,
    )
    cv2.putText(
        canvas,
        "1-5 abre direto",
        (80, 162),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (230, 238, 255),
        1,
    )

    points_text = f"PONTOS {get_points_label()}"
    draw_panel(canvas, (700, 110), (904, 160), (44, 84, 62), (164, 238, 142), 3)
    cv2.putText(
        canvas,
        points_text,
        (724, 143),
        cv2.FONT_HERSHEY_DUPLEX,
        0.72,
        (236, 255, 224),
        2,
    )

    for idx, button in enumerate(BUTTONS):
        draw_button(canvas, idx, button, idx == selected_index)

    selected_button = BUTTONS[selected_index]
    draw_panel(canvas, (140, 452), (820, 506), (35, 55, 88), (145, 194, 255), 3)
    cv2.putText(
        canvas,
        selected_button["description"],
        (164, 485),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (246, 248, 255),
        1,
    )

    cv2.rectangle(
        canvas,
        (0, CANVAS_HEIGHT - FOOTER_HEIGHT),
        (CANVAS_WIDTH, CANVAS_HEIGHT),
        (26, 34, 48),
        -1,
    )
    cv2.putText(
        canvas,
        "SETAS navegam  |  ENTER abre  |  ESC sai  |  1-5 atalhos",
        (210, CANVAS_HEIGHT - 16),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.58,
        (210, 220, 245),
        1,
    )

    return canvas


def handle_mouse(event, x, y, flags, param):
    global selected_index
    if event != cv2.EVENT_LBUTTONDOWN:
        return

    for idx, button in enumerate(BUTTONS):
        x1, y1, x2, y2 = get_button_rect(idx)
        if x1 <= x <= x2 and y1 <= y <= y2:
            selected_index = idx
            launch_button(button)
            break


def main():
    global selected_index
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, CANVAS_WIDTH, CANVAS_HEIGHT)
    cv2.setMouseCallback(WINDOW_NAME, handle_mouse)

    while True:
        canvas = draw_menu()
        cv2.imshow(WINDOW_NAME, canvas)
        key = cv2.waitKeyEx(30)

        if key == 27:
            break
        if key in ARROW_UP_KEYS or key in (ord("w"), ord("W"), ord("a"), ord("A")):
            selected_index = (selected_index - 1) % len(BUTTONS)
            continue
        if key in ARROW_DOWN_KEYS or key in (ord("s"), ord("S"), ord("d"), ord("D")):
            selected_index = (selected_index + 1) % len(BUTTONS)
            continue
        if key in ENTER_KEYS:
            launch_button(BUTTONS[selected_index])
            continue
        if key in (ord("1"), ord("2"), ord("3"), ord("4"), ord("5")):
            button_idx = int(chr(key)) - 1
            if button_idx < len(BUTTONS):
                selected_index = button_idx
                launch_button(BUTTONS[button_idx])

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
