from __future__ import annotations

import csv
import random
import time
from pathlib import Path


PLAYER_ONE = "oponente_1"
PLAYER_TWO = "oponente_2"
PLAYER_ORDER = (PLAYER_ONE, PLAYER_TWO)
PLAYER_LABELS = {
    PLAYER_ONE: "Oponente 1",
    PLAYER_TWO: "Oponente 2",
}
PLAYER_COLORS = {
    PLAYER_ONE: (255, 120, 0),
    PLAYER_TWO: (0, 140, 255),
}
GAME_PHASES = (
    "aguardando_inicio",
    "jogando",
    "troca_jogador",
    "resultado",
)
SUPPORTED_LETTERS = {
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "I",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
}


class DueloGameService:
    """Estado base do duelo local por tempo entre dois jogadores."""

    def __init__(self, csv_path: Path | None = None, max_lives: int = 3):
        self.csv_path = csv_path or Path(__file__).resolve().parent.parent / "exercicios_libras" / "dados" / "palavras_libras_filtrado.csv"
        self.max_lives = max(1, int(max_lives))
        self.random = random.Random()
        self.words = self._load_supported_words()
        self.last_feedback = ""
        self.round_winner = ""
        self.winning_reason = ""
        self.transition_message = ""
        self.reset_match()

    def reset_match(self) -> dict:
        self.player_lives = {player: self.max_lives for player in PLAYER_ORDER}
        self.player_times = {player: None for player in PLAYER_ORDER}
        self.current_player = PLAYER_ONE
        self.current_word = self._choose_word()
        self.phase = "aguardando_inicio"
        self.round_started_at = None
        self.last_feedback = "Prepare o Oponente 1 e pressione iniciar rodada."
        self.round_winner = ""
        self.winning_reason = ""
        self.transition_message = ""
        return self.build_state("")

    def start_round(self) -> dict:
        if self.phase == "resultado":
            self.last_feedback = "A rodada terminou. Reinicie ou avance para outra palavra."
            return self.build_state("")

        self.phase = "jogando"
        self.round_started_at = time.monotonic()
        self.transition_message = ""
        self.last_feedback = f"{self.get_player_label(self.current_player)} em jogo."
        return self.build_state("")

    def evaluate_attempt(self, current_word: str) -> dict:
        normalized = self._normalize_word(current_word)

        if self.phase != "jogando":
            self.last_feedback = "Inicie a rodada antes de validar a palavra."
            return self.build_state(normalized)

        if normalized != self.current_word:
            self._lose_life(self.current_player)
            if self.phase == "resultado":
                return self.build_state(normalized)

            self.last_feedback = (
                f"{self.get_player_label(self.current_player)} errou a palavra. "
                f"Restam {self.player_lives[self.current_player]} vida(s)."
            )
            return self.build_state(normalized)

        elapsed = self._finish_current_turn()
        if self.current_player == PLAYER_ONE:
            self.player_times[PLAYER_ONE] = elapsed
            self.current_player = PLAYER_TWO
            self.phase = "troca_jogador"
            self.transition_message = (
                f"Oponente 1 concluiu em {elapsed:.2f}s. Passe a vez para o Oponente 2."
            )
            self.last_feedback = "Troca de jogador pronta."
            self.round_started_at = None
            return self.build_state("")

        self.player_times[PLAYER_TWO] = elapsed
        self.phase = "resultado"
        self._define_winner()
        return self.build_state("")

    def continue_to_next_player(self) -> dict:
        if self.phase != "troca_jogador":
            self.last_feedback = "Nao ha troca pendente de jogador."
            return self.build_state("")

        self.phase = "jogando"
        self.round_started_at = time.monotonic()
        self.transition_message = ""
        alvo = self.player_times[PLAYER_ONE] or 0.0
        self.last_feedback = f"Oponente 2 em jogo. Tempo a bater: {alvo:.2f}s."
        return self.build_state("")

    def next_round(self) -> dict:
        self.player_times = {player: None for player in PLAYER_ORDER}
        self.current_player = PLAYER_ONE
        self.current_word = self._choose_word(exclude=self.current_word)
        self.phase = "aguardando_inicio"
        self.round_started_at = None
        self.round_winner = ""
        self.winning_reason = ""
        self.transition_message = ""
        self.last_feedback = "Nova palavra carregada. Prepare o Oponente 1."
        return self.build_state("")

    def build_state(self, current_word: str) -> dict:
        normalized = self._normalize_word(current_word)
        current_elapsed = 0.0
        if self.phase == "jogando" and self.round_started_at is not None:
            current_elapsed = time.monotonic() - self.round_started_at

        return {
            "modo": "duelo",
            "fase": self.phase,
            "palavra_alvo": self.current_word,
            "palavra_usuario": normalized,
            "jogador_atual": self.current_player,
            "jogador_atual_label": self.get_player_label(self.current_player),
            "jogador_atual_cor_bgr": list(self.get_player_color(self.current_player)),
            "tempo_atual": round(current_elapsed, 3),
            "tempo_oponente_1": self._round_time(self.player_times[PLAYER_ONE]),
            "tempo_oponente_2": self._round_time(self.player_times[PLAYER_TWO]),
            "tempo_a_bater": self._round_time(self.player_times[PLAYER_ONE]),
            "vidas_oponente_1": self.player_lives[PLAYER_ONE],
            "vidas_oponente_2": self.player_lives[PLAYER_TWO],
            "vidas_maximas": self.max_lives,
            "vencedor": self.round_winner,
            "vencedor_label": self.get_player_label(self.round_winner) if self.round_winner else "",
            "motivo_vitoria": self.winning_reason,
            "mensagem_transicao": self.transition_message,
            "feedback": self.last_feedback,
            "letras_suportadas": "".join(sorted(SUPPORTED_LETTERS)),
            "total_palavras_validas": len(self.words),
            "fonte_dados": str(self.csv_path.relative_to(Path.cwd())) if self.csv_path.exists() else "fallback",
        }

    def get_player_label(self, player_id: str) -> str:
        return PLAYER_LABELS.get(player_id, "")

    def get_player_color(self, player_id: str) -> tuple[int, int, int]:
        return PLAYER_COLORS.get(player_id, (255, 255, 255))

    def _finish_current_turn(self) -> float:
        if self.round_started_at is None:
            return 0.0
        elapsed = time.monotonic() - self.round_started_at
        self.round_started_at = None
        self.last_feedback = f"{self.get_player_label(self.current_player)} concluiu a palavra."
        return round(elapsed, 3)

    def _lose_life(self, player_id: str):
        self.player_lives[player_id] = max(0, self.player_lives[player_id] - 1)
        if self.player_lives[player_id] > 0:
            return

        self.phase = "resultado"
        other_player = PLAYER_TWO if player_id == PLAYER_ONE else PLAYER_ONE
        self.round_winner = other_player
        self.winning_reason = f"{self.get_player_label(player_id)} ficou sem vidas."
        self.last_feedback = self.winning_reason

    def _define_winner(self):
        time_one = self.player_times[PLAYER_ONE]
        time_two = self.player_times[PLAYER_TWO]

        if time_one is None or time_two is None:
            self.round_winner = ""
            self.winning_reason = "Tempos incompletos para definir vencedor."
            self.last_feedback = self.winning_reason
            return

        if time_two < time_one:
            self.round_winner = PLAYER_TWO
            self.winning_reason = (
                f"Oponente 2 venceu por ser mais rapido: {time_two:.2f}s contra {time_one:.2f}s."
            )
        elif time_two == time_one:
            self.round_winner = ""
            self.winning_reason = f"Empate em {time_one:.2f}s."
        else:
            self.round_winner = PLAYER_ONE
            self.winning_reason = (
                f"Oponente 1 venceu com {time_one:.2f}s contra {time_two:.2f}s."
            )

        self.last_feedback = self.winning_reason

    def _choose_word(self, exclude: str = "") -> str:
        if not self.words:
            return "SOL"

        normalized_exclude = self._normalize_word(exclude)
        if len(self.words) == 1:
            return self.words[0]

        candidates = [word for word in self.words if word != normalized_exclude]
        return self.random.choice(candidates or self.words)

    def _load_supported_words(self) -> list[str]:
        if not self.csv_path.exists():
            return self._fallback_words()

        words = []
        with self.csv_path.open("r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                normalized = self._normalize_word(row.get("palavra") or "")
                if not normalized:
                    continue
                if set(normalized).issubset(SUPPORTED_LETTERS):
                    words.append(normalized)

        unique_words = sorted(set(words), key=lambda item: (len(item), item))
        return unique_words or self._fallback_words()

    def _fallback_words(self) -> list[str]:
        return ["BOLA", "CASA", "DADO", "FOCA", "GALO", "LAMA", "LONA", "SOL"]

    def _normalize_word(self, value: str) -> str:
        return "".join(char for char in (value or "").upper() if char.isalpha())

    def _round_time(self, value: float | None) -> float | None:
        if value is None:
            return None
        return round(float(value), 3)
