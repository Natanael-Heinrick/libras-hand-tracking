from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from loja.state import LOOKS_DIR, get_points_label, load_shop_items, load_state, save_state, spend_points, sync_shop_catalog


WINDOW_NAME = "Loja LIBRAS"
CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 720
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
COLOR_LOCKED = (255, 210, 140)
COLOR_CAMERA_BANNER = (66, 104, 150)
COLOR_CAMERA_BANNER_BORDER = (171, 206, 255)
COLOR_STATUS_BG = (44, 84, 62)
COLOR_CONTROLS = (88, 78, 52)


def fit_image(image: np.ndarray, max_width: int, max_height: int) -> np.ndarray:
    height, width = image.shape[:2]
    scale = min(max_width / width, max_height / height)
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return cv2.resize(image, new_size)


def draw_text(canvas: np.ndarray, text: str, position: tuple[int, int], scale: float, color: tuple[int, int, int], thickness: int = 2):
    cv2.putText(canvas, text, position, cv2.FONT_HERSHEY_DUPLEX, scale, color, thickness, cv2.LINE_AA)


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
    cv2.rectangle(canvas, (x1 + 6, y1 + 6), (x2 + 6, y2 + 6), COLOR_WOOD_DARK, -1)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), fill_color, -1)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), border_color, border_thickness)


def draw_badge(canvas: np.ndarray, x: int, y: int, text: str, fill_color: tuple[int, int, int], text_color: tuple[int, int, int] = COLOR_TEXT):
    (text_width, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, 0.48, 1)
    width = text_width + 28
    cv2.rectangle(canvas, (x, y), (x + width, y + 30), fill_color, -1)
    cv2.rectangle(canvas, (x, y), (x + width, y + 30), COLOR_BORDER_SOFT, 2)
    draw_text(canvas, text, (x + 14, y + 21), 0.48, text_color, 1)
    return width


def draw_selection_glow(canvas: np.ndarray, top_left: tuple[int, int], bottom_right: tuple[int, int]):
    x1, y1 = top_left
    x2, y2 = bottom_right
    cv2.rectangle(canvas, (x1 - 4, y1 - 4), (x2 + 4, y2 + 4), COLOR_WARNING, 2)
    cv2.rectangle(canvas, (x1 - 8, y1 - 8), (x2 + 8, y2 + 8), COLOR_BORDER_SOFT, 1)


def draw_pixel_cloud(canvas: np.ndarray, x: int, y: int, size: int):
    blocks = [
        (0, 1), (1, 0), (1, 1), (2, 0), (2, 1), (3, 1), (4, 1),
        (1, 2), (2, 2), (3, 2),
    ]
    for col, row in blocks:
        x1 = x + col * size
        y1 = y + row * size
        cv2.rectangle(canvas, (x1, y1), (x1 + size, y1 + size), COLOR_CLOUD, -1)
        cv2.rectangle(canvas, (x1, y1 + size - 4), (x1 + size, y1 + size), COLOR_CLOUD_SHADOW, -1)


def draw_pixel_background(canvas: np.ndarray):
    for y in range(CANVAS_HEIGHT):
        ratio = min(1.0, y / max(1, SKY_HEIGHT))
        color = (
            int(COLOR_SKY_TOP[0] + (COLOR_SKY_BOTTOM[0] - COLOR_SKY_TOP[0]) * ratio),
            int(COLOR_SKY_TOP[1] + (COLOR_SKY_BOTTOM[1] - COLOR_SKY_TOP[1]) * ratio),
            int(COLOR_SKY_TOP[2] + (COLOR_SKY_BOTTOM[2] - COLOR_SKY_TOP[2]) * ratio),
        )
        cv2.line(canvas, (0, y), (CANVAS_WIDTH, y), color, 1)

    draw_pixel_cloud(canvas, 84, 48, 16)
    draw_pixel_cloud(canvas, 410, 36, 12)
    draw_pixel_cloud(canvas, 1008, 72, 14)

    cv2.circle(canvas, (120, SKY_HEIGHT + 48), 120, COLOR_HILL, -1)
    cv2.circle(canvas, (390, SKY_HEIGHT + 62), 170, COLOR_HILL, -1)
    cv2.circle(canvas, (980, SKY_HEIGHT + 56), 152, COLOR_HILL, -1)

    cv2.rectangle(canvas, (0, SKY_HEIGHT), (CANVAS_WIDTH, CANVAS_HEIGHT), COLOR_GRASS, -1)
    cv2.rectangle(canvas, (0, SKY_HEIGHT), (CANVAS_WIDTH, SKY_HEIGHT + 16), COLOR_GRASS_TOP, -1)
    cv2.rectangle(canvas, (0, SKY_HEIGHT + 16), (CANVAS_WIDTH, SKY_HEIGHT + 34), COLOR_GRASS_SHADOW, -1)

    for x in range(0, CANVAS_WIDTH, 40):
        cv2.rectangle(canvas, (x, CANVAS_HEIGHT - 18), (x + 20, CANVAS_HEIGHT), COLOR_CONTROLS, -1)
    cv2.rectangle(canvas, (0, CANVAS_HEIGHT - 18), (CANVAS_WIDTH, CANVAS_HEIGHT), COLOR_WOOD, 2)


def get_item_status(item: dict, state: dict) -> tuple[str, tuple[int, int, int]]:
    owned = item["id"] in state.get("owned_items", [])
    equipped = item["id"] == state.get("equipped_item", "")
    if equipped:
        return "Equipado", COLOR_SUCCESS
    if owned:
        return "Comprado", COLOR_WARNING
    return f"{item['price']} pts", COLOR_LOCKED


def render_preview(canvas: np.ndarray, item: dict, state: dict):
    preview_panel = (724, 146, 1228, 530)
    draw_panel(canvas, (preview_panel[0], preview_panel[1]), (preview_panel[2], preview_panel[3]), COLOR_WOOD, COLOR_BORDER_SOFT, 4)
    draw_text(canvas, "PREVIEW DO LOOK", (750, 182), 0.62, COLOR_TEXT, 2)

    image_area = (758, 206, 1194, 494)
    cv2.rectangle(canvas, (image_area[0], image_area[1]), (image_area[2], image_area[3]), (244, 236, 220), -1)
    cv2.rectangle(canvas, (image_area[0], image_area[1]), (image_area[2], image_area[3]), COLOR_CAMERA_BANNER_BORDER, 2)

    if not item:
        draw_text(canvas, "Nenhum look cadastrado", (822, 332), 0.74, COLOR_WOOD_DARK, 2)
        draw_text(canvas, f"Coloque os PNGs em {LOOKS_DIR}", (792, 372), 0.42, COLOR_WOOD, 1)
        return

    image_path = LOOKS_DIR / item["file"]
    image = cv2.imread(str(image_path))
    if image is None:
        draw_text(canvas, "Preview indisponivel", (840, 346), 0.74, COLOR_WOOD_DARK, 2)
        return

    fitted = fit_image(image, 384, 264)
    offset_x = image_area[0] + (image_area[2] - image_area[0] - fitted.shape[1]) // 2
    offset_y = image_area[1] + (image_area[3] - image_area[1] - fitted.shape[0]) // 2
    canvas[offset_y : offset_y + fitted.shape[0], offset_x : offset_x + fitted.shape[1]] = fitted


def render_shop(items: list[dict], state: dict, selected_index: int, feedback: str) -> np.ndarray:
    canvas = np.zeros((CANVAS_HEIGHT, CANVAS_WIDTH, 3), dtype=np.uint8)
    draw_pixel_background(canvas)

    draw_panel(canvas, (182, 20), (730, 94), COLOR_CAMERA_BANNER, COLOR_BORDER, 4)
    draw_text(canvas, "LOJA LIBRAS", (344, 66), 1.16, COLOR_TEXT, 3)
    draw_text(canvas, "Escolha um look para o personagem", (286, 88), 0.5, COLOR_TEXT_SOFT, 1)

    draw_panel(canvas, (880, 24), (1224, 96), COLOR_STATUS_BG, COLOR_SUCCESS, 3)
    draw_text(canvas, "PONTOS DISPONIVEIS", (912, 52), 0.52, COLOR_TEXT, 2)
    draw_text(canvas, get_points_label(), (1038, 84), 1.06, COLOR_WARNING, 3)
    cv2.rectangle(canvas, (900, 62), (938, 82), COLOR_WARNING, -1)
    cv2.rectangle(canvas, (900, 62), (938, 82), COLOR_BORDER_SOFT, 2)

    draw_panel(canvas, (40, 126), (684, 622), COLOR_WOOD, COLOR_BORDER_SOFT, 4)
    draw_text(canvas, "CATALOGO DE LOOKS", (66, 162), 0.7, COLOR_TEXT, 2)

    list_top = 186
    visible_items = items[:6]
    for index, item in enumerate(visible_items):
        y1 = list_top + index * 70
        y2 = y1 + 56
        selected = index == selected_index
        fill = COLOR_WOOD_LIGHT if selected else COLOR_WOOD_SOFT
        border = COLOR_WARNING if selected else COLOR_BORDER_SOFT
        text_color = COLOR_TEXT if selected else COLOR_TEXT_SOFT
        card_left = 58
        card_right = 664
        draw_panel(canvas, (card_left, y1), (card_right, y2), fill, border, 3 if selected else 2)
        if selected:
            draw_selection_glow(canvas, (card_left, y1), (card_right, y2))

        status_text, status_color = get_item_status(item, state)
        draw_text(canvas, item["name"], (84, y1 + 24), 0.68, text_color, 2)
        draw_text(canvas, item.get("description", ""), (84, y1 + 47), 0.43, COLOR_MUTED, 1)

        if status_text == "Equipado":
            badge_fill = COLOR_STATUS_BG
            badge_text_color = COLOR_TEXT
        elif status_text == "Comprado":
            badge_fill = COLOR_CAMERA_BANNER
            badge_text_color = COLOR_WARNING
        else:
            badge_fill = COLOR_WOOD_DARK
            badge_text_color = COLOR_LOCKED
        draw_badge(canvas, 506, y1 + 13, status_text, badge_fill, badge_text_color)

        if selected:
            cv2.rectangle(canvas, (38, y1 + 16), (50, y1 + 28), COLOR_WARNING, -1)
            cv2.rectangle(canvas, (672, y1 + 16), (684, y1 + 28), COLOR_WARNING, -1)

    current_item = items[selected_index] if items else {}
    render_preview(canvas, current_item, state)

    draw_panel(canvas, (724, 548), (1228, 676), COLOR_WOOD_LIGHT, COLOR_BORDER_SOFT, 3)
    if current_item:
        status_text, status_color = get_item_status(current_item, state)
        draw_text(canvas, current_item["name"], (750, 588), 0.9, COLOR_TEXT, 2)
        draw_text(canvas, f"Arquivo: {current_item['file']}", (750, 618), 0.42, COLOR_MUTED, 1)
        draw_badge(canvas, 750, 636, f"Preco {current_item['price']} pontos", COLOR_WOOD_DARK, COLOR_WARNING)

        if status_text == "Equipado":
            detail_fill = COLOR_STATUS_BG
            detail_text = COLOR_TEXT
        elif status_text == "Comprado":
            detail_fill = COLOR_CAMERA_BANNER
            detail_text = COLOR_WARNING
        else:
            detail_fill = COLOR_WOOD_DARK
            detail_text = COLOR_LOCKED
        draw_badge(canvas, 1014, 636, status_text, detail_fill, detail_text)
    else:
        draw_text(canvas, "Nenhum look disponivel.", (750, 610), 0.76, COLOR_TEXT, 2)

    draw_panel(canvas, (40, 640), (684, 692), COLOR_STATUS_BG, COLOR_SUCCESS, 3)
    draw_text(canvas, feedback, (58, 672), 0.46, COLOR_TEXT, 1)

    cv2.rectangle(canvas, (724, 684), (1228, 706), COLOR_CONTROLS, -1)
    cv2.rectangle(canvas, (724, 684), (1228, 706), COLOR_BORDER_SOFT, 3)
    draw_text(
        canvas,
        "[1] Subir   [2] Descer   [3] Comprar   [4] Equipar   [5] Atualizar   [0] Sair",
        (738, 700),
        0.35,
        COLOR_TEXT,
        1,
    )

    return canvas


def main():
    items = sync_shop_catalog()
    state = load_state()
    selected_index = 0
    feedback = "Loja pronta. Seus looks foram carregados e os pontos infinitos estao ativos para teste."

    while True:
        items = load_shop_items()
        state = load_state()
        if selected_index >= len(items):
            selected_index = 0

        canvas = render_shop(items, state, selected_index, feedback)
        cv2.imshow(WINDOW_NAME, canvas)
        key = cv2.waitKey(0) & 0xFF

        if key in (27, ord("0")):
            break

        if not items:
            if key == ord("5"):
                items = sync_shop_catalog()
                feedback = "Catalogo atualizado."
            continue

        if key == ord("2"):
            selected_index = (selected_index + 1) % len(items)
            continue
        if key == ord("1"):
            selected_index = (selected_index - 1) % len(items)
            continue
        if key == ord("5"):
            items = sync_shop_catalog()
            feedback = "Catalogo atualizado com os arquivos da pasta."
            continue

        selected_item = items[selected_index]
        owned_items = state.get("owned_items", [])

        if key == ord("3"):
            if selected_item["id"] in owned_items:
                feedback = "Esse look ja foi comprado."
                continue
            success, _ = spend_points(selected_item["price"])
            if not success:
                feedback = "Pontos insuficientes para comprar esse look."
                continue

            state = load_state()
            state["owned_items"] = owned_items + [selected_item["id"]]
            save_state(state)
            feedback = f"Compra concluida: {selected_item['name']}."
            continue

        if key == ord("4"):
            if selected_item["id"] not in owned_items:
                feedback = "Compre o look antes de equipar."
                continue

            state["equipped_item"] = selected_item["id"]
            save_state(state)
            feedback = f"Look equipado: {selected_item['name']}."
            continue

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
