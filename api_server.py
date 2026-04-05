import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import cv2

from hand_tracking_service import HandTrackingService
from soletracao_palavras import (
    AudioCaptureService,
    PlaceholderTranscriptionService,
    SpellingPlaybackService,
    WordSpellingService,
)


HOST = "127.0.0.1"
PORT = 8000
SUPPORTED_LETTERS = [
    "A",
    "C",
    "D",
    "E",
    "F",
    "G",
    "I",
    "J",
    "K",
    "M",
    "N",
    "O",
    "P",
    "R",
    "S",
    "T",
    "U",
    "V",
]
service = HandTrackingService()
word_spelling_service = WordSpellingService()
playback_service = SpellingPlaybackService(word_spelling_service)
audio_capture_service = AudioCaptureService()
transcription_service = PlaceholderTranscriptionService()


class HandTrackingHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html_file(self, file_path: Path):
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_gif_file(self, file_path: Path):
        if not file_path.exists() or not file_path.is_file():
            self._send_json({"erro": "GIF nao encontrado"}, status=404)
            return

        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "image/gif")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_binary_file(self, file_path: Path, content_type: str):
        if not file_path.exists() or not file_path.is_file():
            self._send_json({"erro": "Arquivo nao encontrado"}, status=404)
            return

        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length) if length > 0 else b"{}"
        return json.loads(raw_body.decode("utf-8"))

    def _stream_video(self):
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.end_headers()
        try:
            while True:
                _, frame = service.read_state(draw_landmarks=True)
                ret, jpeg = cv2.imencode(".jpg", frame)
                if not ret:
                    break

                self.wfile.write(b"--frame\r\n")
                self.wfile.write(b"Content-Type: image/jpeg\r\n\r\n")
                self.wfile.write(jpeg.tobytes())
                self.wfile.write(b"\r\n")
                time.sleep(0.1)
        except Exception as exc:
            print(f"Streaming error: {exc}")
        finally:
            service.close()

    def do_GET(self):
        parsed = urlparse(self.path)
        route = parsed.path.lower()
        params = parse_qs(parsed.query)

        if route == "/":
            self._send_json(
                {
                    "mensagem": "API de hand tracking ativa",
                    "rotas": [
                        "/alfabeto",
                        "/estado",
                        "/soletracao-palavras?texto=oi",
                        "/soletracao-palavras/iniciar?texto=oi",
                        "/soletracao-palavras/status",
                        "/soletracao-palavras/audio",
                        "/soletracao-palavras/transcrever",
                        "/soletracao-palavras/tela",
                        "/camera/iniciar",
                        "/camera/parar",
                        "/camera/stream",
                        "/teste/a",
                        "/teste/letra/A",
                    ],
                }
            )
            return

        if route == "/alfabeto":
            try:
                state, _ = service.read_state(draw_landmarks=False)
                self._send_json(
                    {
                        "rota": "/alfabeto",
                        "letras_suportadas": SUPPORTED_LETTERS,
                        "camera_ativa": service.camera_is_open(),
                        "estado_atual": state,
                        "observacao": (
                            "Esta rota agora abre a webcam sob demanda. "
                            "GET continua sendo indicado para consulta."
                        ),
                        "query_params_recebidos": params,
                    }
                )
            except RuntimeError as exc:
                self._send_json({"erro": str(exc)}, status=500)
            return

        if route == "/estado":
            try:
                state, _ = service.read_state(draw_landmarks=False)
                self._send_json(state)
            except RuntimeError as exc:
                self._send_json({"erro": str(exc)}, status=500)
            return

        if route == "/soletracao-palavras/tela":
            tela_path = Path(__file__).resolve().parent / "soletracao_palavras" / "tela.html"
            self._send_html_file(tela_path)
            return

        if route == "/soletracao-palavras/iniciar":
            texto = params.get("texto", [""])[0]
            if not texto.strip():
                self._send_json(
                    {
                        "erro": "Informe o parametro ?texto= com a palavra a ser soletrada",
                        "exemplo": "/soletracao-palavras/iniciar?texto=oi",
                    },
                    status=400,
                )
                return

            payload = playback_service.start(texto)
            self._send_json(payload)
            return

        if route == "/soletracao-palavras/status":
            payload = playback_service.get_status()
            self._send_json(payload)
            return

        if route == "/soletracao-palavras":
            texto = params.get("texto", [""])[0]
            if not texto.strip():
                self._send_json(
                    {
                        "erro": "Informe o parametro ?texto= com a palavra a ser soletrada",
                        "exemplo": "/soletracao-palavras?texto=oi",
                    },
                    status=400,
                )
                return

            payload = word_spelling_service.spell_word(texto)
            self._send_json(payload)
            return

        if route.startswith("/soletracao-palavras/gifs/"):
            gif_name = Path(parsed.path).name
            gif_path = Path(__file__).resolve().parent / "soletracao_palavras" / "gifs" / gif_name
            self._send_gif_file(gif_path)
            return

        if route.startswith("/soletracao-palavras/audios/"):
            self._send_json(
                {
                    "erro": "Os audios agora sao temporarios e nao ficam disponiveis para download."
                },
                status=410,
            )
            return

        if route == "/camera/iniciar":
            try:
                service.open_camera()
                self._send_json(
                    {
                        "mensagem": "Webcam iniciada com sucesso",
                        "camera_ativa": service.camera_is_open(),
                    }
                )
            except RuntimeError as exc:
                self._send_json({"erro": str(exc)}, status=500)
            return

        if route == "/camera/parar":
            service.close()
            self._send_json(
                {
                    "mensagem": "Webcam encerrada com sucesso",
                    "camera_ativa": service.camera_is_open(),
                }
            )
            return

        if route == "/camera/stream":
            self._stream_video()
            return

        if route == "/teste/a":
            try:
                result = service.wait_for_letter("A")
                status = 200 if result["sucesso"] else 408
                self._send_json(result, status=status)
            except RuntimeError as exc:
                self._send_json({"erro": str(exc)}, status=500)
            return

        if route.startswith("/teste/letra/"):
            try:
                target_letter = parsed.path.split("/")[-1].upper()
                if target_letter not in SUPPORTED_LETTERS:
                    self._send_json(
                        {
                            "erro": "Letra nao suportada",
                            "letras_suportadas": SUPPORTED_LETTERS,
                        },
                        status=400,
                    )
                    return

                result = service.wait_for_letter(target_letter)
                status = 200 if result["sucesso"] else 408
                self._send_json(result, status=status)
            except RuntimeError as exc:
                self._send_json({"erro": str(exc)}, status=500)
            return

        self._send_json({"erro": "Rota nao encontrada"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        route = parsed.path.lower()

        if route == "/soletracao-palavras/audio":
            try:
                payload = self._read_json_body()
            except json.JSONDecodeError:
                self._send_json({"erro": "JSON invalido"}, status=400)
                return

            audio_base64 = payload.get("audio_base64", "")
            extension = payload.get("extensao", "webm")

            try:
                saved_audio = audio_capture_service.save_base64_audio(audio_base64, extension)
            except ValueError as exc:
                self._send_json({"erro": str(exc)}, status=400)
                return

            self._send_json(
                {
                    "rota": "/soletracao-palavras/audio",
                    "mensagem": "Audio recebido temporariamente com sucesso",
                    "audio": {
                        key: value
                        for key, value in saved_audio.items()
                        if key != "conteudo_bytes"
                    },
                },
                status=201,
            )
            return

        if route == "/soletracao-palavras/transcrever":
            try:
                payload = transcription_service.transcribe_latest_audio(
                    audio_capture_service.get_last_saved_audio()
                )
            except ValueError as exc:
                self._send_json({"erro": str(exc)}, status=400)
                return

            self._send_json(payload, status=200)
            return

        self._send_json({"erro": "Rota nao encontrada"}, status=404)

    def log_message(self, format, *args):
        return


def run():
    server = ThreadingHTTPServer((HOST, PORT), HandTrackingHandler)
    print(f"Servidor rodando em http://{HOST}:{PORT}")
    print(
        "Rotas disponiveis: /alfabeto, /estado, /soletracao-palavras?texto=oi, "
        "/soletracao-palavras/iniciar?texto=oi, /soletracao-palavras/status, "
        "/soletracao-palavras/audio, /soletracao-palavras/transcrever, "
        "/soletracao-palavras/tela, /camera/iniciar, /camera/parar, "
        "/camera/stream, /teste/a, /teste/letra/A"
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        service.close()


if __name__ == "__main__":
    run()
