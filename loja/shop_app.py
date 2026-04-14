from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from loja.state import LOOKS_DIR, get_points_label, load_shop_items, load_state, save_state, spend_points, sync_shop_catalog


WINDOW_NAME = "Loja LIBRAS"


def fit_image(image: np.ndarray, max_width: int, max_height: int) -> np.ndarray:
    height, width = image.shape[:2]
    scale = min(max_width / width, max_height / height)
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return cv2.resize(image, new_size)


def draw_text(canvas: np.ndarray, text: str, position: tuple[int, int], scale: float, color: tuple[int, int, int], thickness: int = 2):
    cv2.putText(canvas, text, position, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)


def render_preview(canvas: np.ndarray, item: dict):
    preview_area = (760, 120, 1180, 520)
    cv2.rectangle(canvas, (preview_area[0], preview_area[1]), (preview_area[2], preview_area[3]), (29, 44, 70), -1)

    if not item:
        draw_text(canvas, "Nenhum look cadastrado ainda.", (790, 300), 0.8, (230, 230, 230), 2)
        draw_text(canvas, f"Coloque os PNGs em {LOOKS_DIR}", (790, 340), 0.55, (180, 210, 255), 1)
        return

    image_path = LOOKS_DIR / item["file"]
    image = cv2.imread(str(image_path))
    if image is None:
        draw_text(canvas, "Preview indisponivel.", (820, 300), 0.8, (230, 230, 230), 2)
        return

    fitted = fit_image(image, 360, 360)
    offset_x = preview_area[0] + (preview_area[2] - preview_area[0] - fitted.shape[1]) // 2
    offset_y = preview_area[1] + (preview_area[3] - preview_area[1] - fitted.shape[0]) // 2
    canvas[offset_y : offset_y + fitted.shape[0], offset_x : offset_x + fitted.shape[1]] = fitted


def render_shop(items: list[dict], state: dict, selected_index: int, feedback: str) -> np.ndarray:
    canvas = np.full((720, 1280, 3), (16, 22, 32), dtype=np.uint8)
    cv2.rectangle(canvas, (0, 0), (1280, 90), (29, 44, 70), -1)
    draw_text(canvas, "Loja LIBRAS", (40, 58), 1.1, (255, 255, 255), 3)
    draw_text(canvas, f"Pontos disponiveis: {get_points_label()}", (840, 58), 0.8, (120, 255, 180), 2)

    draw_text(canvas, "Looks", (40, 125), 0.9, (255, 220, 140), 2)
    draw_text(canvas, "Use 1 para subir, 2 para descer, 3 para comprar, 4 para equipar, 5 para atualizar, 0 para sair.", (40, 670), 0.58, (220, 220, 220), 1)
    draw_text(canvas, feedback, (40, 705), 0.58, (180, 255, 180), 1)

    list_top = 150
    visible_items = items[:6]
    for index, item in enumerate(visible_items):
        y1 = list_top + (index * 80)
        y2 = y1 + 62
        selected = index == selected_index
        color = (55, 93, 145) if selected else (34, 48, 74)
        cv2.rectangle(canvas, (40, y1), (700, y2), color, -1)
        cv2.rectangle(canvas, (40, y1), (700, y2), (120, 180, 255), 2 if selected else 1)

        owned = item["id"] in state.get("owned_items", [])
        equipped = item["id"] == state.get("equipped_item", "")
        status = "Comprado" if owned else f"{item['price']} pts"
        if equipped:
            status = "Equipado"

        draw_text(canvas, f"{index + 1}. {item['name']}", (60, y1 + 26), 0.72, (255, 255, 255), 2)
        draw_text(canvas, item.get("description", ""), (60, y1 + 50), 0.5, (220, 220, 220), 1)
        draw_text(canvas, status, (560, y1 + 38), 0.62, (255, 220, 140), 2)

    current_item = items[selected_index] if items else {}
    render_preview(canvas, current_item)
    if current_item:
        draw_text(canvas, current_item["name"], (760, 560), 0.9, (255, 255, 255), 2)
        draw_text(canvas, f"Arquivo: {current_item['file']}", (760, 600), 0.6, (180, 210, 255), 1)
        draw_text(canvas, f"Preco: {current_item['price']} pontos", (760, 635), 0.65, (255, 220, 140), 2)
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
