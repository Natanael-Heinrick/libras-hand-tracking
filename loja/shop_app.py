from __future__ import annotations

import base64
from pathlib import Path

import cv2
import numpy as np

from loja.state import LOOKS_DIR, get_points_label, load_shop_items, load_state, save_state, spend_points, sync_shop_catalog
from ui_decor import get_floating_hands_css, get_floating_hands_markup

try:
    import webview
except ImportError:
    webview = None


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


def shop_image_data_url(item: dict) -> str:
    if not item:
        return ""
    image_path = LOOKS_DIR / item["file"]
    if not image_path.exists():
        return ""
    mime = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(image_path.read_bytes()).decode('ascii')}"


def build_shop_html() -> str:
    return """
<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Loja LIBRAS</title>
    <style>
        :root { --surface:#fff; --soft:#fff4c9; --ink:#1d2735; --muted:#65758b; --line:#ffd36a; --blue:#2577ff; --green:#00a978; --amber:#ffb000; --red:#ef4444; --pink:#ff5c8a; --purple:#7c5cff; --cyan:#00b8d9; }
        * { box-sizing:border-box; }
        body { margin:0; min-height:100vh; font-family:"Segoe UI", Arial, sans-serif; color:var(--ink); background:linear-gradient(135deg,rgba(255,176,0,.18) 0 18%,transparent 18%),linear-gradient(45deg,rgba(124,92,255,.13) 0 16%,transparent 16%),linear-gradient(160deg,#fff8e8 0%,#e9f8ff 52%,#fff0f6 100%); }
        .app { min-height:100vh; display:grid; grid-template-columns:minmax(360px,46vw) 1fr; gap:22px; padding:22px; position:relative; z-index:1; }
        .panel { background:var(--surface); border:2px solid var(--line); border-radius:8px; box-shadow:0 16px 40px rgba(29,45,68,.1); }
        .catalog, .preview { padding:22px; }
        h1 { margin:0; font-size:2rem; letter-spacing:0; }
        .lead { margin:6px 0 18px; color:var(--muted); line-height:1.45; }
        .top { display:flex; justify-content:space-between; gap:12px; align-items:start; }
        .points { min-height:44px; display:inline-flex; align-items:center; border:2px solid var(--amber); border-radius:8px; padding:0 14px; background:#fff2bd; font-weight:850; color:#9a5d00; }
        .items { display:grid; gap:10px; }
        .item { display:grid; grid-template-columns:1fr auto; gap:12px; align-items:center; width:100%; min-height:70px; border:2px solid var(--item-color,var(--line)); border-radius:8px; background:#fff; padding:12px; text-align:left; cursor:pointer; }
        .item:nth-child(1) { --item-color:var(--blue); }
        .item:nth-child(2) { --item-color:var(--green); }
        .item:nth-child(3) { --item-color:var(--amber); }
        .item:nth-child(4) { --item-color:var(--pink); }
        .item:nth-child(5) { --item-color:var(--purple); }
        .item:nth-child(6) { --item-color:var(--cyan); }
        .item.active { border-color:var(--blue); box-shadow:0 10px 28px rgba(47,111,237,.16); background:#f0f7ff; }
        .name { font-weight:850; }
        .desc { margin-top:4px; color:var(--muted); font-size:.92rem; }
        .badge { display:inline-flex; min-height:30px; align-items:center; border-radius:999px; padding:0 11px; background:var(--soft); border:1px solid var(--line); font-weight:850; white-space:nowrap; }
        #preview-image { width:100%; aspect-ratio:4/3; object-fit:contain; border-radius:8px; border:1px solid var(--line); background:var(--soft); display:block; }
        .detail { margin-top:14px; border:1px solid var(--line); background:var(--soft); border-radius:8px; padding:16px; }
        .detail-title { font-size:1.5rem; font-weight:850; }
        .feedback { margin-top:14px; border-left:5px solid var(--green); background:#fff; border-radius:8px; padding:14px; font-weight:800; }
        .actions { display:flex; flex-wrap:wrap; gap:9px; margin-top:14px; }
        button { min-height:40px; border:1px solid var(--line); border-radius:8px; background:white; color:var(--ink); padding:0 12px; font:inherit; font-weight:800; cursor:pointer; }
        button.primary { background:var(--blue); border-color:var(--blue); color:white; }
        button.good { background:var(--green); border-color:var(--green); color:white; }
        button.warn { background:var(--red); border-color:var(--red); color:white; }
        button:nth-child(1), button:nth-child(2) { border-color:var(--amber); background:#fff2bd; }
        button:nth-child(5) { border-color:var(--cyan); background:#dff8ff; }
        @media (max-width:900px) { .app { grid-template-columns:1fr; padding:14px; } .top { display:block; } .points { margin-top:12px; } }
        __FLOATING_HANDS_CSS__
    </style>
</head>
<body>
    __FLOATING_HANDS_MARKUP__
    <div class="app">
        <section class="panel catalog">
            <div class="top">
                <div>
                    <h1>Loja LIBRAS</h1>
                    <p class="lead">Escolha, compre e equipe um look para o personagem.</p>
                </div>
                <div class="points" id="points">Pontos --</div>
            </div>
            <div class="items" id="items"></div>
            <div class="feedback" id="feedback">Loja pronta.</div>
        </section>
        <section class="panel preview">
            <img id="preview-image" alt="Preview do look">
            <div class="detail">
                <div class="detail-title" id="selected-name">Nenhum look</div>
                <p class="lead" id="selected-description"></p>
                <span class="badge" id="selected-status">--</span>
            </div>
            <div class="actions">
                <button onclick="call('previous')">1 Subir</button>
                <button onclick="call('next')">2 Descer</button>
                <button class="primary" onclick="call('buy')">3 Comprar</button>
                <button class="good" onclick="call('equip')">4 Equipar</button>
                <button onclick="call('refresh')">5 Atualizar</button>
                <button class="warn" onclick="window.pywebview.api.close()">0 Sair</button>
            </div>
        </section>
    </div>
    <script>
        function statusText(item, state) {
            if (!item) return "--";
            const owned = (state.owned_items || []).includes(item.id);
            const equipped = state.equipped_item === item.id;
            if (equipped) return "Equipado";
            if (owned) return "Comprado";
            return item.price + " pts";
        }
        function renderShop(data) {
            document.getElementById('points').textContent = 'Pontos ' + data.points;
            document.getElementById('feedback').textContent = data.feedback;
            const items = document.getElementById('items');
            items.innerHTML = '';
            data.items.forEach((item, index) => {
                const button = document.createElement('button');
                button.className = 'item' + (index === data.selected_index ? ' active' : '');
                button.onclick = () => window.pywebview.api.select(index).then(renderShop);
                button.innerHTML = '<span><span class="name"></span><span class="desc"></span></span><span class="badge"></span>';
                button.querySelector('.name').textContent = item.name;
                button.querySelector('.desc').textContent = item.description || '';
                button.querySelector('.badge').textContent = statusText(item, data.state);
                items.appendChild(button);
            });
            const selected = data.selected_item || {};
            document.getElementById('preview-image').src = data.preview || '';
            document.getElementById('selected-name').textContent = selected.name || 'Nenhum look';
            document.getElementById('selected-description').textContent = selected.description || '';
            document.getElementById('selected-status').textContent = statusText(selected, data.state || {});
        }
        function call(name) { window.pywebview.api[name]().then(renderShop); }
        document.addEventListener('keydown', (event) => {
            if (event.key === '1') call('previous');
            if (event.key === '2') call('next');
            if (event.key === '3') call('buy');
            if (event.key === '4') call('equip');
            if (event.key === '5') call('refresh');
            if (event.key === '0' || event.key === 'Escape') window.pywebview.api.close();
        });
        window.addEventListener('pywebviewready', () => window.pywebview.api.snapshot().then(renderShop));
    </script>
</body>
</html>
""".replace("__FLOATING_HANDS_CSS__", get_floating_hands_css()).replace(
        "__FLOATING_HANDS_MARKUP__", get_floating_hands_markup()
    )


class ShopApi:
    def __init__(self):
        self._selected_index = 0
        self._feedback = "Loja pronta. Seus looks foram carregados e os pontos infinitos estao ativos para teste."
        self._window = None
        sync_shop_catalog()

    def snapshot(self):
        items = load_shop_items()
        state = load_state()
        if self._selected_index >= len(items):
            self._selected_index = 0
        selected_item = items[self._selected_index] if items else {}
        return {
            "items": items,
            "state": state,
            "selected_index": self._selected_index,
            "selected_item": selected_item,
            "preview": shop_image_data_url(selected_item),
            "points": get_points_label(),
            "feedback": self._feedback,
        }

    def select(self, index):
        items = load_shop_items()
        if items:
            self._selected_index = max(0, min(int(index), len(items) - 1))
        return self.snapshot()

    def previous(self):
        items = load_shop_items()
        if items:
            self._selected_index = (self._selected_index - 1) % len(items)
        return self.snapshot()

    def next(self):
        items = load_shop_items()
        if items:
            self._selected_index = (self._selected_index + 1) % len(items)
        return self.snapshot()

    def refresh(self):
        sync_shop_catalog()
        self._feedback = "Catalogo atualizado com os arquivos da pasta."
        return self.snapshot()

    def buy(self):
        items = load_shop_items()
        if not items:
            self._feedback = "Nenhum look disponivel."
            return self.snapshot()
        state = load_state()
        selected_item = items[self._selected_index]
        owned_items = state.get("owned_items", [])
        if selected_item["id"] in owned_items:
            self._feedback = "Esse look ja foi comprado."
            return self.snapshot()
        success, _ = spend_points(selected_item["price"])
        if not success:
            self._feedback = "Pontos insuficientes para comprar esse look."
            return self.snapshot()
        state = load_state()
        state["owned_items"] = owned_items + [selected_item["id"]]
        save_state(state)
        self._feedback = f"Compra concluida: {selected_item['name']}."
        return self.snapshot()

    def equip(self):
        items = load_shop_items()
        if not items:
            self._feedback = "Nenhum look disponivel."
            return self.snapshot()
        state = load_state()
        selected_item = items[self._selected_index]
        if selected_item["id"] not in state.get("owned_items", []):
            self._feedback = "Compre o look antes de equipar."
            return self.snapshot()
        state["equipped_item"] = selected_item["id"]
        save_state(state)
        self._feedback = f"Look equipado: {selected_item['name']}."
        return self.snapshot()

    def close(self):
        if self._window:
            self._window.destroy()


def run_webview_app():
    api = ShopApi()
    window = webview.create_window(
        WINDOW_NAME,
        html=build_shop_html(),
        js_api=api,
        width=1180,
        height=720,
        resizable=True,
    )
    api._window = window
    webview.start(debug=False)


def run_cv2_shop():
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


def main():
    if webview is not None:
        run_webview_app()
        return

    print("pywebview nao esta instalado; abrindo loja com interface antiga em OpenCV.")
    run_cv2_shop()


if __name__ == "__main__":
    main()
