from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path


class AudioCaptureService:
    """Salva audios recebidos pela tela em uma pasta local."""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = (base_dir or Path(__file__).resolve().parent / "audios").resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
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

        file_name = f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.{safe_extension}"
        file_path = self.base_dir / file_name
        file_path.write_bytes(audio_bytes)

        saved_audio = {
            "arquivo": file_name,
            "arquivo_path": str(file_path.relative_to(Path.cwd())),
            "arquivo_url": f"/soletracao-palavras/audios/{file_name}",
            "tamanho_bytes": len(audio_bytes),
            "extensao": safe_extension,
        }
        self._last_saved_audio = saved_audio
        return saved_audio

    def get_last_saved_audio(self) -> dict | None:
        return self._last_saved_audio
