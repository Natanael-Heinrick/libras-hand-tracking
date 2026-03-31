class ExerciseGameService:
    """Estado inicial do modo exercicio para soletracao por LIBRAS."""

    def __init__(self):
        self.reset_game()

    def reset_game(self):
        self.target_word = "OI"
        self.difficulty = "facil"
        self.points_per_word = 1
        self.score = 0
        self.level = 1
        self.completed = False
        self.last_feedback = "Monte a palavra alvo usando os gestos e confirme as letras."

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

    def build_state(self, current_word: str) -> dict:
        return {
            "modo": "exercicios",
            "palavra_alvo": self.target_word,
            "dificuldade": self.difficulty,
            "pontos_por_acerto": self.points_per_word,
            "pontuacao": self.score,
            "nivel": self.level,
            "palavra_usuario": (current_word or "").strip().upper(),
            "acertou": self.completed,
            "feedback": self.last_feedback,
        }
