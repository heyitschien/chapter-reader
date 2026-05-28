"""Kokoro-82M local neural TTS (primary engine)."""
from __future__ import annotations

import io
import shutil
from typing import Iterator

from .base import SynthesisResult, TTSEngine

DEFAULT_VOICE = "af_bella"
DEFAULT_LANG = "a"
BOOK_SPEED = 0.95

KOKORO_VOICES = [
    "af_bella",
    "af_heart",
    "af_nicole",
    "af_sarah",
    "af_sky",
    "am_adam",
    "am_michael",
    "bf_emma",
    "bf_isabella",
    "bm_george",
    "bm_lewis",
]

_pipeline = None


def _espeak_available() -> bool:
    return shutil.which("espeak-ng") is not None or shutil.which("espeak") is not None


def _import_kokoro():
    from kokoro import KPipeline  # noqa: PLC0415

    return KPipeline


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        KPipeline = _import_kokoro()
        _pipeline = KPipeline(lang_code=DEFAULT_LANG)
    return _pipeline


def _audio_to_wav_bytes(audio, sample_rate: int = 24000) -> bytes:
    import numpy as np  # noqa: PLC0415
    import soundfile as sf  # noqa: PLC0415

    arr = np.asarray(audio, dtype=np.float32)
    buf = io.BytesIO()
    sf.write(buf, arr, sample_rate, format="WAV")
    return buf.getvalue()


class KokoroEngine(TTSEngine):
    id = "kokoro"
    name = "Kokoro (neural, offline)"

    def is_available(self) -> bool:
        if not _espeak_available():
            return False
        try:
            _import_kokoro()
            return True
        except Exception:
            return False

    def list_voices(self) -> list[str]:
        return list(KOKORO_VOICES)

    def default_voice(self) -> str:
        return DEFAULT_VOICE

    def synthesize(self, text: str, *, voice: str | None = None, speed: float = 1.0) -> SynthesisResult:
        if not text.strip():
            raise ValueError("Empty text")
        voice = voice or DEFAULT_VOICE
        if voice not in KOKORO_VOICES:
            voice = DEFAULT_VOICE
        rate = speed if speed > 0 else BOOK_SPEED
        pipeline = _get_pipeline()
        chunks: list = []
        generator: Iterator = pipeline(
            text,
            voice=voice,
            speed=rate,
            split_pattern=r"\n+",
        )
        for _i, (_gs, _ps, audio) in enumerate(generator):
            chunks.append(audio)
        if not chunks:
            raise RuntimeError("Kokoro produced no audio")
        import numpy as np  # noqa: PLC0415

        combined = np.concatenate([np.asarray(c, dtype=np.float32) for c in chunks])
        wav = _audio_to_wav_bytes(combined, 24000)
        return SynthesisResult(
            audio_bytes=wav,
            sample_rate=24000,
            engine=self.id,
            voice=voice,
        )


def prefetch_model() -> bool:
    """Load pipeline once to trigger Hugging Face download if needed."""
    if not _espeak_available():
        return False
    try:
        _get_pipeline()
        return True
    except Exception:
        return False
