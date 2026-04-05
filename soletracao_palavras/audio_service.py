from __future__ import annotations

import base64
from datetime import datetime


class AudioCaptureService:
    """Mantem apenas o ultimo audio recebido em memoria."""

    def __init__(self, base_dir=None):
        self._last_saved_audio: dict | None = None

    def save_base64_audio(self, audio_base64: str, extension: str = "webm") -> dict:
        clean_base64 = audio_base64.strip()
        if not clean_base64:
            raise ValueError("Audio em base64 nao informado.")

        if "," in clean_base64:
            clean_base64 = clean_base64.split(",", 1)[1]

        try:
            audio_bytes = base64.b64decode(clean_base64, validate=True)
        except Exception as exc:
            raise ValueError("Audio em base64 invalido.") from exc

        safe_extension = (extension or "webm").strip().lower()
        if not safe_extension.isalnum():
            safe_extension = "webm"

        saved_audio = {
            "id": f"audio_temp_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            "tamanho_bytes": len(audio_bytes),
            "extensao": safe_extension,
            "temporario": True,
            "recebido_em": datetime.now().isoformat(timespec="seconds"),
            "conteudo_bytes": audio_bytes,
        }
        self._last_saved_audio = saved_audio
        return saved_audio

    def get_last_saved_audio(self) -> dict | None:
        return self._last_saved_audio
