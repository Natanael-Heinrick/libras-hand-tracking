from __future__ import annotations

import csv
import random
from pathlib import Path


POINTS_BY_DIFFICULTY = {
    "facil": 1,
    "medio": 2,
    "dificil": 3,
}

DIFFICULTIES = ("facil", "medio", "dificil")


class ExerciseGameService:
    """Modo exercicio para soletracao por LIBRAS carregando palavras de CSV."""

    def __init__(self, csv_path: Path | None = None):
        self.csv_path = csv_path or Path(__file__).resolve().parent / "dados" / "palavras_libras_filtrado.csv"
        self.words = self._load_words()
        self.score = 0
        self.level = 1
        self.completed = False
        self.last_completed_word = ""
        self.last_feedback = "Monte a palavra alvo usando os gestos e confirme as letras."
        self.selected_difficulty = "facil"
        self.filtered_words = []
        self.current_index = 0
        self.random = random.Random()
        self._apply_difficulty_filter(self.selected_difficulty, preserve_target="OI")

    def evaluate_word(self, current_word: str) -> dict:
        word = (current_word or "").strip().upper()
        self.completed = word == self.target_word

        if self.completed:
            completed_word = self.target_word
            self.score += self.points_per_word
            self.level = self._calculate_level()
            self.last_completed_word = completed_word
            self.last_feedback = f"Acertou {completed_word}. Carregando a proxima palavra."
            self._advance_word()
            return self.build_state("")
        else:
            self.last_feedback = "Ainda nao corresponde a palavra alvo."

        return self.build_state(word)

    def restart_round(self) -> dict:
        self.completed = False
        self.last_completed_word = ""
        self.last_feedback = "Rodada reiniciada. Tente novamente."
        return self.build_state("")

    def next_word(self) -> dict:
        self._advance_word()
        self.completed = False
        self.last_completed_word = ""
        self.last_feedback = "Nova palavra aleatoria carregada."
        return self.build_state("")

    def set_difficulty(self, difficulty: str) -> dict:
        normalized = (difficulty or "").strip().lower()
        if normalized not in DIFFICULTIES:
            self.last_feedback = "Dificuldade invalida."
            return self.build_state("")

        self.selected_difficulty = normalized
        self._apply_difficulty_filter(normalized)
        self.completed = False
        self.last_completed_word = ""
        self.last_feedback = f"Dificuldade alterada para {normalized}."
        return self.build_state("")

    def build_state(self, current_word: str) -> dict:
        return {
            "modo": "exercicios",
            "palavra_alvo": self.target_word,
            "dificuldade": self.difficulty,
            "dificuldade_selecionada": self.selected_difficulty,
            "tamanho_palavra": self.word_size,
            "pontos_por_acerto": self.points_per_word,
            "pontuacao": self.score,
            "nivel": self.level,
            "indice_palavra": self.current_index,
            "total_palavras": len(self.filtered_words),
            "total_palavras_csv": len(self.words),
            "palavra_usuario": (current_word or "").strip().upper(),
            "acertou": self.completed,
            "ultima_palavra_concluida": self.last_completed_word,
            "feedback": self.last_feedback,
            "fonte_dados": str(self.csv_path.relative_to(Path.cwd())) if self.csv_path.exists() else "fallback",
        }

    def _calculate_level(self) -> int:
        return max(1, (self.score // 5) + 1)

    def _apply_difficulty_filter(self, difficulty: str, preserve_target: str | None = None):
        filtered = [item for item in self.words if item["nivel"] == difficulty]
        self.filtered_words = filtered or [{"palavra": "OI", "nivel": "facil", "tamanho": 2}]
        target_word = (preserve_target or "").strip().upper()

        if target_word:
            for index, item in enumerate(self.filtered_words):
                if item["palavra"] == target_word:
                    self.current_index = index
                    self._set_current_word(index)
                    return

        self.current_index = 0
        self._set_current_word(0)

    def _set_current_word(self, index: int):
        selected = self.filtered_words[index]
        self.target_word = selected["palavra"]
        self.difficulty = selected["nivel"]
        self.word_size = selected["tamanho"]
        self.points_per_word = POINTS_BY_DIFFICULTY.get(self.difficulty, 1)

    def _advance_word(self):
        if not self.filtered_words:
            return

        if len(self.filtered_words) == 1:
            self.current_index = 0
            self._set_current_word(0)
            return

        available_indexes = [index for index in range(len(self.filtered_words)) if index != self.current_index]
        self.current_index = self.random.choice(available_indexes)
        self._set_current_word(self.current_index)

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

                if not palavra or nivel not in DIFFICULTIES:
                    continue

                words.append(
                    {
                        "palavra": palavra,
                        "nivel": nivel,
                        "tamanho": tamanho,
                    }
                )

        return words or [{"palavra": "OI", "nivel": "facil", "tamanho": 2}]
