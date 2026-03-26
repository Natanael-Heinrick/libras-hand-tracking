import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import cv2

from hand_tracking_service import HandTrackingService


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


class HandTrackingHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

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
                            "erro": "Letra não suportada",
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

        self._send_json({"erro": "Rota não encontrada"}, status=404)

    def log_message(self, format, *args):
        return


def run():
    server = ThreadingHTTPServer((HOST, PORT), HandTrackingHandler)
    print(f"Servidor rodando em http://{HOST}:{PORT}")
    print(
        "Rotas disponíveis: /alfabeto, /estado, /camera/iniciar, "
        "/camera/parar, /camera/stream, /teste/a, /teste/letra/A"
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
