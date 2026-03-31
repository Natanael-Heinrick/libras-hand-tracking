from dataclasses import dataclass, field


@dataclass
class SpeechResult:
    original_text: str
    normalized_text: str
    language: str = "pt-BR"


@dataclass
class GlossSequence:
    source_text: str
    glosses: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class AvatarCommand:
    command_type: str
    payload: dict
