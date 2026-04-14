import asyncio
import base64
import json
import sys
from pathlib import Path

import cv2
from websockets.asyncio.client import connect


SERVER_URL = "ws://127.0.0.1:8765/exercicios"
PROJECT_ROOT = Path(__file__).resolve().parent
CHALLENGE_WINDOW = "Desafio por Imagem"


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
    cv2.rectangle(overlay, (10, 10), (overlay.shape[1] - 10, 70), (35, 45, 75), -1)
    cv2.addWeighted(overlay, 0.78, image, 0.22, 0, image)
    cv2.putText(
        image,
        f"Dica: {hint_text}",
        (20, 48),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (220, 235, 255),
        2,
    )


def wrap_text(text, max_chars=42):
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


async def main():
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not camera.isOpened():
        raise RuntimeError("Erro ao acessar webcam local")

    current_image_path = None
    current_image_frame = None
    show_hint = False
    initial_game_mode = get_initial_game_mode()

    try:
        async with connect(SERVER_URL, max_size=2**22) as websocket:
            if initial_game_mode != "misto":
                await websocket.send(json.dumps({"acao": "definir_modo_jogo", "modo_jogo": initial_game_mode}))
                response = json.loads(await websocket.recv())
                if response.get("tipo") == "erro":
                    raise RuntimeError(response.get("mensagem", "Erro ao definir modo de jogo"))

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
                letra = estado.get("letra_estavel") or estado.get("letra") or ""
                tipo_desafio = exercicio.get("tipo_desafio", "palavra")
                imagem_caminho = exercicio.get("imagem_caminho", "")
                modo_jogo = exercicio.get("modo_jogo", "misto")
                dica = exercicio.get("dica", "")
                wrapped_hint = wrap_text(f"Dica: {dica}", max_chars=44) if show_hint and dica else []

                cv2.putText(frame, "Rota: /exercicios", (30, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                cv2.putText(frame, f"Letra: {letra}", (30, 75), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 0), 3)
                cv2.putText(
                    frame,
                    f"Sua palavra: {estado.get('palavra', '')}",
                    (30, 115),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (255, 255, 0),
                    2,
                )
                if tipo_desafio == "imagem":
                    cv2.putText(
                        frame,
                        "Desafio: adivinhe o nome da imagem",
                        (30, 155),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 200, 255),
                        2,
                    )
                    if show_hint and dica:
                        box_bottom = 165 + max(45, len(wrapped_hint) * 24 + 20)
                        cv2.rectangle(frame, (20, 165), (620, box_bottom), (45, 60, 90), -1)
                        for index, line in enumerate(wrapped_hint):
                            cv2.putText(
                                frame,
                                line,
                                (30, 193 + index * 24),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.62,
                                (180, 220, 255),
                                2,
                            )
                    else:
                        cv2.putText(
                            frame,
                            "Dica oculta. Pressione H para mostrar.",
                            (30, 185),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.65,
                            (180, 220, 255),
                            2,
                        )
                else:
                    cv2.putText(
                        frame,
                        f"Alvo: {exercicio.get('palavra_alvo', '')}",
                        (30, 155),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9,
                        (0, 200, 255),
                        2,
                    )
                cv2.putText(
                    frame,
                    f"Dica: {'ON' if show_hint else 'OFF'}",
                    (30, 245),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 220, 180),
                    2,
                )
                cv2.putText(
                    frame,
                    (
                        f"Pontos: {exercicio.get('pontuacao', 0)} | "
                        f"Nivel: {exercicio.get('nivel', 1)} | "
                        f"{exercicio.get('dificuldade', '')} ({exercicio.get('pontos_por_acerto', 1)} pts)"
                    ),
                    (30, 275),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                )
                cv2.putText(
                    frame,
                    f"Modo: {modo_jogo}",
                    (30, 205),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                )
                cv2.putText(
                    frame,
                    f"Feedback: {exercicio.get('feedback', '')}",
                    (30, 305),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (200, 255, 200),
                    2,
                )
                cv2.putText(
                    frame,
                    (
                        f"Filtro: {exercicio.get('dificuldade_selecionada', '')} | "
                        f"Desafio: {exercicio.get('indice_palavra', 0) + 1}/{exercicio.get('total_palavras', 0)}"
                    ),
                    (30, 335),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (255, 220, 180),
                    2,
                )
                cv2.putText(
                    frame,
                    f"Ultima concluida: {exercicio.get('ultima_palavra_concluida', '')}",
                    (30, 360),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (180, 255, 180),
                    2,
                )
                cv2.putText(
                    frame,
                    "ESPACO confirma | C limpa | R reinicia | N proxima manual | H dica",
                    (30, 395),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.56,
                    (255, 255, 255),
                    2,
                )
                cv2.putText(
                    frame,
                    "1 facil | 2 medio | 3 dificil | F fotos | P palavras | M misto | ESC sai",
                    (30, 420),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 255),
                    2,
                )

                if exercicio.get("ultima_palavra_concluida"):
                    cv2.putText(
                        frame,
                        "ACERTOU!",
                        (30, 460),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.2,
                        (0, 255, 0),
                        3,
                    )

                if tipo_desafio == "imagem" and imagem_caminho:
                    resolved_image_path = (PROJECT_ROOT / imagem_caminho).resolve()
                    if current_image_path != resolved_image_path:
                        challenge_image = cv2.imread(str(resolved_image_path))
                        current_image_path = resolved_image_path
                        current_image_frame = None

                        if challenge_image is not None:
                            current_image_frame = cv2.resize(challenge_image, (420, 420))

                    if current_image_frame is not None:
                        challenge_view = current_image_frame.copy()
                        if show_hint and dica:
                            draw_hint_overlay(challenge_view, dica)
                        cv2.imshow(CHALLENGE_WINDOW, challenge_view)
                else:
                    current_image_path = None
                    current_image_frame = None
                    close_challenge_window()

                cv2.imshow("Hand Tracking - Exercicios", frame)
                key = cv2.waitKey(1) & 0xFF

                if key == ord(" "):
                    await websocket.send(json.dumps({"acao": "confirmar_letra"}))
                    response = json.loads(await websocket.recv())
                    if response.get("tipo") == "erro":
                        raise RuntimeError(response.get("mensagem", "Erro ao confirmar letra"))
                elif key == ord("c"):
                    await websocket.send(json.dumps({"acao": "limpar_palavra"}))
                    response = json.loads(await websocket.recv())
                    if response.get("tipo") == "erro":
                        raise RuntimeError(response.get("mensagem", "Erro ao limpar palavra"))
                elif key == ord("r"):
                    await websocket.send(json.dumps({"acao": "reiniciar_exercicio"}))
                    response = json.loads(await websocket.recv())
                    if response.get("tipo") == "erro":
                        raise RuntimeError(response.get("mensagem", "Erro ao reiniciar exercicio"))
                    show_hint = False
                elif key == ord("n"):
                    await websocket.send(json.dumps({"acao": "proxima_palavra"}))
                    response = json.loads(await websocket.recv())
                    if response.get("tipo") == "erro":
                        raise RuntimeError(response.get("mensagem", "Erro ao avancar palavra"))
                    show_hint = False
                elif key == ord("1"):
                    await websocket.send(json.dumps({"acao": "definir_dificuldade", "dificuldade": "facil"}))
                    response = json.loads(await websocket.recv())
                    if response.get("tipo") == "erro":
                        raise RuntimeError(response.get("mensagem", "Erro ao definir dificuldade"))
                    show_hint = False
                elif key == ord("2"):
                    await websocket.send(json.dumps({"acao": "definir_dificuldade", "dificuldade": "medio"}))
                    response = json.loads(await websocket.recv())
                    if response.get("tipo") == "erro":
                        raise RuntimeError(response.get("mensagem", "Erro ao definir dificuldade"))
                    show_hint = False
                elif key == ord("3"):
                    await websocket.send(json.dumps({"acao": "definir_dificuldade", "dificuldade": "dificil"}))
                    response = json.loads(await websocket.recv())
                    if response.get("tipo") == "erro":
                        raise RuntimeError(response.get("mensagem", "Erro ao definir dificuldade"))
                    show_hint = False
                elif key == ord("f"):
                    await websocket.send(json.dumps({"acao": "definir_modo_jogo", "modo_jogo": "fotos"}))
                    response = json.loads(await websocket.recv())
                    if response.get("tipo") == "erro":
                        raise RuntimeError(response.get("mensagem", "Erro ao definir modo de jogo"))
                    show_hint = False
                elif key == ord("p"):
                    await websocket.send(json.dumps({"acao": "definir_modo_jogo", "modo_jogo": "palavras"}))
                    response = json.loads(await websocket.recv())
                    if response.get("tipo") == "erro":
                        raise RuntimeError(response.get("mensagem", "Erro ao definir modo de jogo"))
                    show_hint = False
                elif key == ord("m"):
                    await websocket.send(json.dumps({"acao": "definir_modo_jogo", "modo_jogo": "misto"}))
                    response = json.loads(await websocket.recv())
                    if response.get("tipo") == "erro":
                        raise RuntimeError(response.get("mensagem", "Erro ao definir modo de jogo"))
                    show_hint = False
                elif key in (ord("h"), ord("H"), ord("4")):
                    show_hint = not show_hint
                elif key == 27:
                    break
    finally:
        camera.release()
        close_challenge_window()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    asyncio.run(main())
