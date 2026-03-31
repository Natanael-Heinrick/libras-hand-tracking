from __future__ import annotations

import csv
from pathlib import Path


POINTS_BY_DIFFICULTY = {
    "facil": 1,
    "medio": 2,
    "dificil": 3,
}


class ExerciseGameService:
    """Modo exercicio para soletracao por LIBRAS carregando palavras de CSV."""

    def __init__(self, csv_path: Path | None = None):
        self.csv_path = csv_path or Path(__file__).resolve().parent / "dados" / "palavras_libras_filtrado.csv"
        self.words = self._load_words()
        self.current_index = 0
        self.score = 0
        self.level = 1
        self.completed = False
        self.last_feedback = "Monte a palavra alvo usando os gestos e confirme as letras."
        self._set_current_word(self._find_initial_index())

    def evaluate_word(self, current_word: str) -> dict:
        word = (current_word or "").strip().upper()
        self.completed = word == self.target_word

        if self.completed:
            self.score += self.points_per_word
            self.last_feedback = "Acertou a palavra alvo."
        else:
            self.last_feedback = "Ainda nao corresponde a palavra alvo."

        return self.build_state(word)

    def restart_round(self) -> dict:
        self.completed = False
        self.last_feedback = "Rodada reiniciada. Tente novamente."
        return self.build_state("")

    def next_word(self) -> dict:
        if self.words:
            self.current_index = (self.current_index + 1) % len(self.words)
            self._set_current_word(self.current_index)
        self.completed = False
        self.last_feedback = "Nova palavra carregada."
        return self.build_state("")

    def build_state(self, current_word: str) -> dict:
        return {
            "modo": "exercicios",
            "palavra_alvo": self.target_word,
            "dificuldade": self.difficulty,
            "tamanho_palavra": self.word_size,
            "pontos_por_acerto": self.points_per_word,
            "pontuacao": self.score,
            "nivel": self.level,
            "indice_palavra": self.current_index,
            "total_palavras": len(self.words),
            "palavra_usuario": (current_word or "").strip().upper(),
            "acertou": self.completed,
            "feedback": self.last_feedback,
            "fonte_dados": str(self.csv_path.relative_to(Path.cwd())) if self.csv_path.exists() else "fallback",
        }

    def _set_current_word(self, index: int):
        if not self.words:
            self.target_word = "OI"
            self.difficulty = "facil"
            self.word_size = 2
            self.points_per_word = 1
            return

        selected = self.words[index]
        self.target_word = selected["palavra"]
        self.difficulty = selected["nivel"]
        self.word_size = selected["tamanho"]
        self.points_per_word = POINTS_BY_DIFFICULTY.get(self.difficulty, 1)

    def _find_initial_index(self) -> int:
        for index, item in enumerate(self.words):
            if item["palavra"] == "OI":
                return index
        return 0

    def _load_words(self) -> list[dict]:
        if not self.csv_path.exists():
            return [{"palavra": "OI", "nivel": "facil", "tamanho": 2}]

        words = []
        with self.csv_path.open("r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                palavra = "".join(char for char in (row.get("palavra") or "").upper() if char.isalpha())
                nivel = (row.get("nivel") or "facil").strip().lower()
                tamanho = int(row.get("tamanho") or len(palavra) or 0)

                if not palavra:
                    continue

                words.append(
                    {
                        "palavra": palavra,
                        "nivel": nivel,
                        "tamanho": tamanho,
                    }
                )

        return words or [{"palavra": "OI", "nivel": "facil", "tamanho": 2}]
