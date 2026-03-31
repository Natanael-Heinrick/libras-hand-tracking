from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from time import monotonic


DEFAULT_ITEM_DURATION_MS = 1800
DEFAULT_WORD_GAP_MS = 600


class WordSpellingService:
    """Resolve um texto em palavras, letras e GIFs locais."""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = (base_dir or Path(__file__).resolve().parent / "gifs").resolve()

    def spell_word(self, text: str) -> dict:
        words = self._split_words(text)
        normalized = "".join(words)
        letters = [char for char in normalized if char.isalpha()]

        grouped_words = []
        items = []

        for word_index, raw_word in enumerate(words):
            word_items = []
            for letter_index, letter in enumerate(raw_word):
                item = self._build_letter_item(letter, raw_word, word_index, letter_index)
                word_items.append(item)
                items.append(item)

            grouped_words.append(
                {
                    "palavra": raw_word,
                    "indice_palavra": word_index,
                    "sequencia": word_items,
                }
            )

            if word_index < len(words) - 1:
                items.append(self._build_pause_item(word_index))

        return {
            "rota": "/soletracao-palavras",
            "texto_original": text,
            "texto_normalizado": normalized,
            "palavras": words,
            "grupos_palavras": grouped_words,
            "letras": letters,
            "sequencia": items,
            "status_atual": "hold" if items else "continue",
            "proximo_status": "continue",
            "observacao": (
                "Envie GIFs nomeados por letra em soletracao_palavras/gifs, "
                "por exemplo O.gif e I.gif."
            ),
        }

    def _split_words(self, text: str) -> list[str]:
        return [
            "".join(char for char in token.upper() if char.isalpha())
            for token in text.split()
            if token.strip()
        ]

    def _build_letter_item(self, letter: str, word: str, word_index: int, letter_index: int) -> dict:
        gif_path = self.base_dir / f"{letter}.gif"
        return {
            "tipo": "letra",
            "letra": letter,
            "palavra": word,
            "indice_palavra": word_index,
            "indice_letra": letter_index,
            "gif_nome": gif_path.name,
            "gif_path": str(gif_path.relative_to(Path.cwd())),
            "gif_url": f"/soletracao-palavras/gifs/{gif_path.name}",
            "gif_existe": gif_path.exists(),
        }

    def _build_pause_item(self, previous_word_index: int) -> dict:
        return {
            "tipo": "pausa",
            "palavra": None,
            "indice_palavra": previous_word_index,
            "gif_existe": True,
        }


class SpellingPlaybackService:
    """Controla o estado hold -> continue de uma sequencia de soletracao."""

    def __init__(
        self,
        spelling_service: WordSpellingService,
        item_duration_ms: int = DEFAULT_ITEM_DURATION_MS,
        word_gap_ms: int = DEFAULT_WORD_GAP_MS,
    ):
        self.spelling_service = spelling_service
        self.item_duration_ms = item_duration_ms
        self.word_gap_ms = word_gap_ms
        self._current_session: dict | None = None
        self._session_counter = 0

    def start(self, text: str) -> dict:
        payload = self.spelling_service.spell_word(text)
        queue = [
            item
            for item in payload["sequencia"]
            if item["tipo"] == "pausa" or item["gif_existe"]
        ]
        timeline = self._build_timeline(queue)

        self._session_counter += 1
        self._current_session = {
            "session_id": self._session_counter,
            "texto_original": payload["texto_original"],
            "texto_normalizado": payload["texto_normalizado"],
            "palavras": payload["palavras"],
            "grupos_palavras": payload["grupos_palavras"],
            "fila": queue,
            "timeline": timeline,
            "duracao_total_ms": timeline[-1]["fim_ms"] if timeline else 0,
            "iniciado_em": monotonic(),
        }

        return {
            "rota": "/soletracao-palavras/iniciar",
            "session_id": self._session_counter,
            "texto_original": payload["texto_original"],
            "texto_normalizado": payload["texto_normalizado"],
            "palavras": payload["palavras"],
            "grupos_palavras": payload["grupos_palavras"],
            "fila": queue,
            "duracao_item_ms": self.item_duration_ms,
            "duracao_pausa_ms": self.word_gap_ms,
            "status_atual": "hold" if queue else "continue",
            "proximo_status": "continue",
        }

    def get_status(self) -> dict:
        if self._current_session is None:
            return {
                "rota": "/soletracao-palavras/status",
                "status_atual": "continue",
                "session_id": None,
                "palavras": [],
                "grupos_palavras": [],
                "fila": [],
                "item_atual": None,
                "indice_atual": None,
                "duracao_item_ms": self.item_duration_ms,
                "duracao_pausa_ms": self.word_gap_ms,
                "observacao": "Nenhuma execucao iniciada.",
            }

        session = self._current_session
        queue = session["fila"]
        timeline = session["timeline"]

        if not queue:
            return {
                "rota": "/soletracao-palavras/status",
                "status_atual": "continue",
                "session_id": session["session_id"],
                "palavras": session["palavras"],
                "grupos_palavras": session["grupos_palavras"],
                "fila": [],
                "item_atual": None,
                "indice_atual": None,
                "duracao_item_ms": self.item_duration_ms,
                "duracao_pausa_ms": self.word_gap_ms,
                "texto_original": session["texto_original"],
                "texto_normalizado": session["texto_normalizado"],
            }

        elapsed_ms = int((monotonic() - session["iniciado_em"]) * 1000)
        current_index = self._find_current_index(elapsed_ms, timeline)

        if current_index >= len(queue):
            return {
                "rota": "/soletracao-palavras/status",
                "status_atual": "continue",
                "session_id": session["session_id"],
                "palavras": session["palavras"],
                "grupos_palavras": session["grupos_palavras"],
                "fila": deepcopy(queue),
                "item_atual": None,
                "indice_atual": None,
                "duracao_item_ms": self.item_duration_ms,
                "duracao_pausa_ms": self.word_gap_ms,
                "texto_original": session["texto_original"],
                "texto_normalizado": session["texto_normalizado"],
                "finalizado": True,
            }

        item = deepcopy(queue[current_index])
        current_slot = timeline[current_index]
        return {
            "rota": "/soletracao-palavras/status",
            "status_atual": "hold",
            "session_id": session["session_id"],
            "palavras": session["palavras"],
            "grupos_palavras": session["grupos_palavras"],
            "fila": deepcopy(queue),
            "item_atual": item,
            "indice_atual": current_index,
            "duracao_item_ms": self.item_duration_ms,
            "duracao_pausa_ms": self.word_gap_ms,
            "duracao_item_atual_ms": current_slot["duracao_ms"],
            "texto_original": session["texto_original"],
            "texto_normalizado": session["texto_normalizado"],
            "restante_ms_item": current_slot["fim_ms"] - elapsed_ms,
            "finalizado": False,
        }

    def _build_timeline(self, queue: list[dict]) -> list[dict]:
        timeline = []
        current_start = 0
        for item in queue:
            duration_ms = self.word_gap_ms if item["tipo"] == "pausa" else self.item_duration_ms
            timeline.append(
                {
                    "inicio_ms": current_start,
                    "fim_ms": current_start + duration_ms,
                    "duracao_ms": duration_ms,
                }
            )
            current_start += duration_ms
        return timeline

    def _find_current_index(self, elapsed_ms: int, timeline: list[dict]) -> int:
        for index, slot in enumerate(timeline):
            if elapsed_ms < slot["fim_ms"]:
                return index
        return len(timeline)
