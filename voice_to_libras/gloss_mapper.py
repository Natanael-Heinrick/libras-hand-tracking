from .models import GlossSequence, SpeechResult


class GlossMapper:
    """Converte texto em uma estrutura intermediaria para futura geracao em LIBRAS."""

    def map_to_gloss(self, speech: SpeechResult) -> GlossSequence:
        tokens = [token.upper() for token in speech.normalized_text.split() if token]
        return GlossSequence(
            source_text=speech.normalized_text,
            glosses=tokens,
            notes=[
                "Esqueleto inicial: glosas atuais sao apenas tokens em maiusculo.",
                "Futura etapa: reorganizar a frase para uma estrutura mais adequada a LIBRAS.",
            ],
        )
