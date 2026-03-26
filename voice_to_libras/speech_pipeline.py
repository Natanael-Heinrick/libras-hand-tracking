from .models import SpeechResult


class SpeechPipeline:
    """Base para capturar e normalizar fala antes da etapa de glosas."""

    def transcribe_text(self, raw_text: str) -> SpeechResult:
        normalized = " ".join(raw_text.strip().split())
        return SpeechResult(
            original_text=raw_text,
            normalized_text=normalized,
        )
