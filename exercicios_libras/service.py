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
GAME_MODES = ("palavras", "fotos", "misto")


class ExerciseGameService:
    """Modo exercicio para soletracao por LIBRAS com desafios por palavra e imagem."""

    def __init__(self, csv_path: Path | None = None):
        self.csv_path = csv_path or Path(__file__).resolve().parent / "dados" / "palavras_libras_filtrado.csv"
        self.images_path = Path(__file__).resolve().parent / "imagens_desafios"
        self.words = self._load_words()
        self.image_challenges = self._load_image_challenges()
        self.score = 0
        self.level = 1
        self.completed = False
        self.last_completed_word = ""
        self.last_feedback = "Monte a palavra alvo usando os gestos e confirme as letras."
        self.selected_difficulty = "facil"
        self.game_mode = "misto"
        self.filtered_challenges = []
        self.current_index = 0
        self.random = random.Random()
        initial_target = self.image_challenges[0]["palavra"] if self.image_challenges else "OI"
        self._apply_difficulty_filter(self.selected_difficulty, preserve_target=initial_target)

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

    def set_game_mode(self, game_mode: str) -> dict:
        normalized = (game_mode or "").strip().lower()
        if normalized not in GAME_MODES:
            self.last_feedback = "Modo de jogo invalido."
            return self.build_state("")

        self.game_mode = normalized
        preserve_target = self.target_word if hasattr(self, "target_word") else ""
        self._apply_difficulty_filter(self.selected_difficulty, preserve_target=preserve_target)
        self.completed = False
        self.last_completed_word = ""
        self.last_feedback = f"Modo de jogo alterado para {normalized}."
        return self.build_state("")

    def build_state(self, current_word: str) -> dict:
        image_relative_path = ""
        if self.challenge_image_path:
            image_relative_path = str(self.challenge_image_path.relative_to(Path.cwd()))

        return {
            "modo": "exercicios",
            "modo_jogo": self.game_mode,
            "tipo_desafio": self.challenge_type,
            "palavra_alvo": self.target_word,
            "descricao_desafio": self.challenge_prompt,
            "imagem_nome": self.challenge_image_name,
            "imagem_caminho": image_relative_path,
            "dificuldade": self.difficulty,
            "dificuldade_selecionada": self.selected_difficulty,
            "tamanho_palavra": self.word_size,
            "pontos_por_acerto": self.points_per_word,
            "pontuacao": self.score,
            "nivel": self.level,
            "indice_palavra": self.current_index,
            "total_palavras": len(self.filtered_challenges),
            "total_palavras_csv": len(self.words),
            "total_desafios_imagem": len(self.image_challenges),
            "palavra_usuario": (current_word or "").strip().upper(),
            "acertou": self.completed,
            "ultima_palavra_concluida": self.last_completed_word,
            "feedback": self.last_feedback,
            "fonte_dados": str(self.csv_path.relative_to(Path.cwd())) if self.csv_path.exists() else "fallback",
        }

    def _calculate_level(self) -> int:
        return max(1, (self.score // 5) + 1)

    def _apply_difficulty_filter(self, difficulty: str, preserve_target: str | None = None):
        filtered_words = [item for item in self.words if item["nivel"] == difficulty]
        filtered_images = [item for item in self.image_challenges if item["nivel"] == difficulty]
        if self.game_mode == "palavras":
            filtered = filtered_words
        elif self.game_mode == "fotos":
            filtered = filtered_images
        else:
            filtered = filtered_images + filtered_words
        self.filtered_challenges = filtered or [self._build_fallback_challenge()]
        target_word = (preserve_target or "").strip().upper()

        if target_word:
            for index, item in enumerate(self.filtered_challenges):
                if item["palavra"] == target_word:
                    self.current_index = index
                    self._set_current_word(index)
                    return

        self.current_index = 0
        self._set_current_word(0)

    def _set_current_word(self, index: int):
        selected = self.filtered_challenges[index]
        self.target_word = selected["palavra"]
        self.difficulty = selected["nivel"]
        self.word_size = selected["tamanho"]
        self.challenge_type = selected.get("tipo", "palavra")
        self.challenge_image_name = selected.get("imagem_nome", "")
        self.challenge_image_path = selected.get("imagem_caminho")
        self.challenge_prompt = selected.get("descricao", "Monte a palavra alvo usando os gestos e confirme as letras.")
        self.points_per_word = POINTS_BY_DIFFICULTY.get(self.difficulty, 1)

    def _advance_word(self):
        if not self.filtered_challenges:
            return

        if len(self.filtered_challenges) == 1:
            self.current_index = 0
            self._set_current_word(0)
            return

        available_indexes = [index for index in range(len(self.filtered_challenges)) if index != self.current_index]
        self.current_index = self.random.choice(available_indexes)
        self._set_current_word(self.current_index)

    def _build_fallback_challenge(self) -> dict:
        return {
            "tipo": "palavra",
            "palavra": "OI",
            "nivel": "facil",
            "tamanho": 2,
            "imagem_nome": "",
            "imagem_caminho": None,
            "descricao": "Monte a palavra alvo usando os gestos e confirme as letras.",
        }

    def _load_words(self) -> list[dict]:
        if not self.csv_path.exists():
            return [self._build_fallback_challenge()]

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
                        "tipo": "palavra",
                        "palavra": palavra,
                        "nivel": nivel,
                        "tamanho": tamanho,
                        "imagem_nome": "",
                        "imagem_caminho": None,
                        "descricao": "Monte a palavra alvo usando os gestos e confirme as letras.",
                    }
                )

        return words or [self._build_fallback_challenge()]

    def _load_image_challenges(self) -> list[dict]:
        if not self.images_path.exists():
            return []

        challenges = []
        for image_path in sorted(self.images_path.iterdir()):
            if not image_path.is_file():
                continue

            if image_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}:
                continue

            answer = "".join(char for char in image_path.stem.upper() if char.isalpha())
            if not answer:
                continue

            challenges.append(
                {
                    "tipo": "imagem",
                    "palavra": answer,
                    "nivel": "facil",
                    "tamanho": len(answer),
                    "imagem_nome": image_path.name,
                    "imagem_caminho": image_path,
                    "descricao": "Observe a imagem e soletre exatamente o nome dela.",
                }
            )

        return challenges
