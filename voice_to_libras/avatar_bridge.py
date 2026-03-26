from .models import AvatarCommand, GlossSequence


class AvatarBridge:
    """Transforma glosas em comandos para um futuro avatar."""

    def build_commands(self, gloss_sequence: GlossSequence) -> list[AvatarCommand]:
        return [
            AvatarCommand(
                command_type="play_sign_sequence",
                payload={
                    "glosses": gloss_sequence.glosses,
                    "source_text": gloss_sequence.source_text,
                },
            )
        ]
