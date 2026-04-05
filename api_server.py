import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from soletracao_palavras import SpellingPlaybackService, WordSpellingService


HOST = "127.0.0.1"
PORT = 8000
word_spelling_service = WordSpellingService()
playback_service = SpellingPlaybackService(word_spelling_service)


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

    def do_GET(self):
        parsed = urlparse(self.path)
        route = parsed.path.lower()
        params = parse_qs(parsed.query)

        if route == "/":
            self._send_json(
                {
                    "mensagem": "API de transcricao por voz ativa",
                    "rotas": [
                        "/soletracao-palavras/iniciar?texto=oi",
                        "/soletracao-palavras/status",
                        "/soletracao-palavras/tela",
                        "/soletracao-palavras/gifs/<arquivo>",
                    ],
                    "acoes_tela": [
                        "Falar e Mostrar",
                        "Transcrever",
                    ],
                }
            )
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

        if route.startswith("/soletracao-palavras/gifs/"):
            gif_name = Path(parsed.path).name
            gif_path = Path(__file__).resolve().parent / "soletracao_palavras" / "gifs" / gif_name
            self._send_gif_file(gif_path)
            return

        self._send_json({"erro": "Rota nao encontrada"}, status=404)

    def do_POST(self):
        self._send_json({"erro": "Rota nao encontrada"}, status=404)

    def log_message(self, format, *args):
        return


def run():
    server = ThreadingHTTPServer((HOST, PORT), HandTrackingHandler)
    print(f"Servidor rodando em http://{HOST}:{PORT}")
    print(
        "Rotas disponiveis: /soletracao-palavras/iniciar?texto=oi, "
        "/soletracao-palavras/status, /soletracao-palavras/tela, "
        "/soletracao-palavras/gifs/<arquivo>"
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
