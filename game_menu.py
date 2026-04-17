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
CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 980

BUTTONS = [
    {
        "label": "1. Fotos",
        "description": "Mostra imagens de objetos e voce soletra o nome.",
        "entry_type": "script",
        "entry": "websocket_exercicios_client.py",
        "args": ["fotos"],
        "requires_server": True,
        "x1": 80,
        "y1": 170,
        "x2": 560,
        "y2": 320,
    },
    {
        "label": "2. Palavras",
        "description": "Treino classico com palavras alvo vindas do CSV.",
        "entry_type": "script",
        "entry": "websocket_exercicios_client.py",
        "args": ["palavras"],
        "requires_server": True,
        "x1": 80,
        "y1": 360,
        "x2": 560,
        "y2": 510,
    },
    {
        "label": "3. Imagens de Letras",
        "description": "Sequencia de imagens de maos e resposta por texto.",
        "entry_type": "module",
        "entry": "quiz_visual_libras.quiz_visual_game",
        "args": [],
        "requires_server": False,
        "x1": 80,
        "y1": 550,
        "x2": 560,
        "y2": 700,
    },
    {
        "label": "4. Loja",
        "description": "Use seus pontos para comprar e equipar looks do personagem.",
        "entry_type": "module",
        "entry": "loja.shop_app",
        "args": [],
        "requires_server": False,
        "x1": 80,
        "y1": 740,
        "x2": 560,
        "y2": 890,
    },
    {
        "label": "5. Duelo de Tempo",
        "description": "Competicao local entre dois jogadores em uma mesma camera.",
        "entry_type": "script",
        "entry": "websocket_duelo_client.py",
        "args": [],
        "requires_server": True,
        "x1": 620,
        "y1": 170,
        "x2": 1100,
        "y2": 320,
    },
]

selected_script: str | None = None


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


def wrap_text(text: str, max_chars: int) -> list[str]:
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


def draw_text_block(
    canvas: np.ndarray,
    lines: list[str],
    start_x: int,
    start_y: int,
    scale: float = 0.58,
    color: tuple[int, int, int] = (235, 235, 235),
    thickness: int = 2,
    line_height: int = 28,
):
    y = start_y
    for line in lines:
        cv2.putText(
            canvas,
            line,
            (start_x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            color,
            thickness,
        )
        y += line_height


def draw_menu() -> np.ndarray:
    canvas = np.full((CANVAS_HEIGHT, CANVAS_WIDTH, 3), (16, 22, 32), dtype=np.uint8)
    cv2.rectangle(canvas, (0, 0), (CANVAS_WIDTH, 140), (29, 44, 70), -1)
    cv2.rectangle(canvas, (620, 360), (1210, 890), (28, 36, 52), -1)

    cv2.putText(canvas, "Central de Jogos LIBRAS", (70, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
    cv2.putText(canvas, "Clique em uma opcao ou pressione 1, 2, 3, 4 ou 5.", (70, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (220, 220, 220), 2)
    cv2.putText(canvas, f"Pontos acumulados: {get_points_label()}", (900, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (120, 255, 180), 2)

    for button in BUTTONS:
        cv2.rectangle(canvas, (button["x1"], button["y1"]), (button["x2"], button["y2"]), (55, 93, 145), -1)
        cv2.rectangle(canvas, (button["x1"], button["y1"]), (button["x2"], button["y2"]), (120, 180, 255), 2)
        cv2.putText(canvas, button["label"], (button["x1"] + 25, button["y1"] + 45), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        draw_text_block(
            canvas,
            wrap_text(button["description"], max_chars=40)[:3],
            button["x1"] + 25,
            button["y1"] + 88,
            scale=0.56,
            color=(235, 235, 235),
            thickness=2,
            line_height=28,
        )

    cv2.putText(canvas, "Como funciona", (650, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 220, 140), 2)
    info_lines = [
        "Duelo: base do novo modo 1x1 por tempo na mesma camera.",
        "Fotos: abre o jogo de imagens de objetos.",
        "Palavras: abre o jogo com palavras do CSV.",
        "Imagens de Letras: quiz visual local com vidas.",
        "Loja: compra e equipa looks com os pontos salvos.",
        "O servidor WebSocket sobe sozinho quando necessario.",
        "ESC fecha o menu.",
    ]
    wrapped_info_lines = []
    for line in info_lines:
        wrapped_info_lines.extend(wrap_text(line, max_chars=45))
    draw_text_block(
        canvas,
        wrapped_info_lines,
        650,
        440,
        scale=0.60,
        color=(255, 255, 255),
        thickness=2,
        line_height=34,
    )
    return canvas


def handle_mouse(event, x, y, flags, param):
    global selected_script
    if event != cv2.EVENT_LBUTTONDOWN:
        return

    for button in BUTTONS:
        if button["x1"] <= x <= button["x2"] and button["y1"] <= y <= button["y2"]:
            selected_script = button["label"]
            launch_button(button)
            break


def main():
    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, handle_mouse)

    while True:
        canvas = draw_menu()
        if selected_script:
            cv2.putText(canvas, f"Aberto: {selected_script}", (650, 910), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (150, 255, 150), 2)
            cv2.putText(canvas, "Voce pode voltar aqui e abrir outro jogo.", (650, 945), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (220, 220, 220), 2)

        cv2.imshow(WINDOW_NAME, canvas)
        key = cv2.waitKey(30) & 0xFF

        if key == 27:
            break
        if key in (ord("1"), ord("2"), ord("3"), ord("4"), ord("5")):
            button = BUTTONS[int(chr(key)) - 1]
            launch_button(button)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
