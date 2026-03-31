from __future__ import annotations


class PlaceholderTranscriptionService:
    """Transcricao provisoria para validar o fluxo de ponta a ponta."""

    def transcribe_latest_audio(self, last_audio: dict | None) -> dict:
        if last_audio is None:
            raise ValueError("Nenhum audio foi enviado ainda.")

        recognized_text = "oi"
        normalized_text = recognized_text.strip().lower()

        return {
            "rota": "/soletracao-palavras/transcrever",
            "modo": "provisorio",
            "mensagem": "Transcricao simulada com sucesso",
            "audio": last_audio,
            "texto_transcrito": recognized_text,
            "texto_normalizado": normalized_text,
            "observacao": (
                "Esta etapa ainda usa um texto fixo de teste. "
                "Depois trocamos pelo motor real de transcricao."
            ),
        }
