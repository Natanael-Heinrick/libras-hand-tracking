import asyncio
import base64
import json
import queue
import subprocess
import threading

import cv2
import numpy as np
from websockets.asyncio.client import connect

from ui_decor import get_floating_hands_css, get_floating_hands_markup

try:
    import webview
except ImportError:
    webview = None


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


def build_camera_html() -> str:
    return """
<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Hand Tracking - Alfabeto</title>
    <style>
        :root {
            --bg: #fff8e8;
            --surface: #ffffff;
            --surface-2: #fff4c9;
            --ink: #1b2533;
            --muted: #66758a;
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
            gap: 24px;
            padding: 24px;
            position: relative;
            z-index: 1;
        }
        .camera-panel, .info-panel {
            background: var(--surface);
            border: 2px solid var(--line);
            border-radius: 8px;
            box-shadow: 0 16px 40px rgba(29, 45, 68, .1);
        }
        .camera-panel {
            align-self: start;
            padding: 16px;
            border-color: var(--cyan);
        }
        .camera-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
            color: var(--muted);
            font-weight: 700;
        }
        .live-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--green);
            display: inline-block;
            margin-right: 8px;
        }
        #camera {
            width: 100%;
            aspect-ratio: 4 / 3;
            object-fit: cover;
            display: block;
            border-radius: 6px;
            background: #172033;
        }
        .info-panel {
            padding: 22px;
            display: grid;
            gap: 14px;
            align-content: start;
        }
        h1 {
            margin: 0 0 4px;
            font-size: 2rem;
            letter-spacing: 0;
        }
        .lead {
            margin: 0 0 8px;
            color: var(--muted);
            line-height: 1.45;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 12px;
        }
        .card {
            border: 2px solid var(--card-color, var(--line));
            background: linear-gradient(180deg, #ffffff 0%, var(--surface-2) 100%);
            border-radius: 8px;
            padding: 16px;
            min-height: 118px;
        }
        .card:nth-child(1) { --card-color: var(--amber); }
        .card:nth-child(2) { --card-color: var(--pink); }
        .card:nth-child(3) { --card-color: var(--blue); }
        .card:nth-child(4) { --card-color: var(--green); }
        .wide { grid-column: 1 / -1; }
        .label {
            color: var(--muted);
            font-size: .78rem;
            text-transform: uppercase;
            font-weight: 800;
            letter-spacing: .04em;
        }
        .value {
            margin-top: 10px;
            font-size: 2rem;
            font-weight: 800;
            word-break: break-word;
        }
        .letter { color: var(--amber); font-size: 4rem; line-height: .95; }
        .word { color: var(--blue); }
        .status-text {
            margin-top: 10px;
            color: var(--green);
            font-weight: 700;
        }
        .actions {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 4px;
        }
        button {
            min-height: 42px;
            border: 1px solid var(--line);
            border-radius: 8px;
            background: white;
            color: var(--ink);
            padding: 0 14px;
            font: inherit;
            font-weight: 700;
            cursor: pointer;
        }
        button.primary {
            background: var(--blue);
            border-color: var(--blue);
            color: white;
        }
        button.warn {
            background: var(--red);
            border-color: var(--red);
            color: white;
        }
        button:nth-child(2) { border-color: var(--amber); background: #fff2bd; }
        button:nth-child(3) { border-color: var(--green); background: #dcfce7; }
        button:nth-child(4) { border-color: var(--purple); background: #eee8ff; }
        pre {
            margin: 0;
            max-height: 190px;
            overflow: auto;
            white-space: pre-wrap;
            color: #dbe8ff;
            background: #172033;
            border-radius: 8px;
            padding: 14px;
            font-size: .82rem;
        }
        @media (max-width: 860px) {
            .app { grid-template-columns: 1fr; padding: 14px; }
            .grid { grid-template-columns: 1fr; }
        }
        __FLOATING_HANDS_CSS__
    </style>
</head>
<body>
    __FLOATING_HANDS_MARKUP__
    <div class="app">
        <section class="camera-panel">
            <div class="camera-head">
                <span><i class="live-dot"></i>Camera</span>
                <span id="hands">0 mao(s)</span>
            </div>
            <img id="camera" alt="Camera ao vivo">
        </section>
        <section class="info-panel">
            <div>
                <h1>Treino de Alfabeto</h1>
                <p class="lead">Confirme a letra estavel e monte sua palavra sem a camera ocupar a tela inteira.</p>
            </div>
            <div class="grid">
                <article class="card">
                    <div class="label">Letra atual</div>
                    <div class="value letter" id="letter">--</div>
                </article>
                <article class="card">
                    <div class="label">Pontos</div>
                    <div class="value" id="points">--</div>
                </article>
                <article class="card wide">
                    <div class="label">Sua palavra</div>
                    <div class="value word" id="word">_</div>
                </article>
                <article class="card wide">
                    <div class="label">Status</div>
                    <div class="status-text" id="status">Aguardando leitura da mao</div>
                </article>
            </div>
            <div class="actions">
                <button class="primary" onclick="sendAction('confirmar_letra')">Espaco Confirmar</button>
                <button onclick="sendAction('limpar_palavra')">C Limpar</button>
                <button onclick="window.pywebview.api.speak()">P Falar</button>
                <button onclick="toggleDebug()">TAB Debug</button>
                <button class="warn" onclick="window.pywebview.api.close()">ESC Sair</button>
            </div>
            <pre id="debug" style="display:none">{}</pre>
        </section>
    </div>
    <script>
        let debugVisible = false;
        function sendAction(action) {
            window.pywebview.api.action(action);
        }
        function toggleDebug() {
            debugVisible = !debugVisible;
            document.getElementById("debug").style.display = debugVisible ? "block" : "none";
        }
        function updateFrame(imageBase64, estado) {
            document.getElementById("camera").src = "data:image/jpeg;base64," + imageBase64;
            const letter = estado.letra_estavel || estado.letra || "--";
            const word = estado.palavra || "_";
            const hands = estado.maos_detectadas || 0;
            document.getElementById("letter").textContent = letter;
            document.getElementById("word").textContent = word;
            document.getElementById("hands").textContent = hands + " mao(s)";
            document.getElementById("points").textContent = estado.pontos ?? "--";
            document.getElementById("status").textContent = estado.letra
                ? "Leitura instantanea: " + estado.letra
                : "Aguardando leitura da mao";
            if (debugVisible) {
                document.getElementById("debug").textContent = JSON.stringify(estado, null, 2);
            }
        }
        document.addEventListener("keydown", (event) => {
            if (event.key === " ") { event.preventDefault(); sendAction("confirmar_letra"); }
            if (event.key.toLowerCase() === "c") sendAction("limpar_palavra");
            if (event.key.toLowerCase() === "p") window.pywebview.api.speak();
            if (event.key === "Tab") { event.preventDefault(); toggleDebug(); }
            if (event.key === "Escape") window.pywebview.api.close();
        });
    </script>
</body>
</html>
""".replace("__FLOATING_HANDS_CSS__", get_floating_hands_css()).replace(
        "__FLOATING_HANDS_MARKUP__", get_floating_hands_markup()
    )


class CameraApi:
    def __init__(self):
        self.actions = queue.Queue()
        self.window = None
        self.closed = False
        self.last_word = ""

    def action(self, action_name):
        self.actions.put(str(action_name))

    def speak(self):
        falar_texto(self.last_word)

    def close(self):
        self.closed = True
        if self.window:
            self.window.destroy()


async def process_webview_actions(websocket, api):
    while True:
        try:
            action_name = api.actions.get_nowait()
        except queue.Empty:
            return

        if action_name in {"confirmar_letra", "limpar_palavra"}:
            await websocket.send(json.dumps({"acao": action_name}))
            response = json.loads(await websocket.recv())
            if response.get("tipo") == "erro":
                raise RuntimeError(response.get("mensagem", "Erro ao executar acao"))


async def run_webview_tracking(window, api):
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not camera.isOpened():
        raise RuntimeError("Erro ao acessar webcam local")

    try:
        async with connect(SERVER_URL, max_size=2**22) as websocket:
            while not api.closed:
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
                api.last_word = estado.get("palavra", "")
                camera_image = encode_frame(cv2.resize(frame, (640, 480)), quality=68)
                window.evaluate_js(
                    f"window.updateFrame('{camera_image}', {json.dumps(estado)});"
                )
                await process_webview_actions(websocket, api)
                await asyncio.sleep(0.02)
    finally:
        api.closed = True
        camera.release()


def start_webview_tracking(window, api):
    try:
        asyncio.run(run_webview_tracking(window, api))
    except Exception as exc:
        print(f"Erro na interface HTML da camera: {exc}")
        api.closed = True


async def run_cv2_tracking():
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


def run_webview_app():
    api = CameraApi()
    window = webview.create_window(
        WINDOW_NAME,
        html=build_camera_html(),
        js_api=api,
        width=1180,
        height=720,
        resizable=True,
    )
    api.window = window
    window.events.closed += lambda: setattr(api, "closed", True)
    webview.start(start_webview_tracking, (window, api), debug=False)


def main():
    if webview is not None:
        run_webview_app()
        return

    print("pywebview nao esta instalado; abrindo a interface antiga em OpenCV.")
    asyncio.run(run_cv2_tracking())


if __name__ == "__main__":
    main()
