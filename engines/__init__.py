"""TTS engine registry and default selection."""
from __future__ import annotations

from .base import EngineInfo, SynthesisResult, TTSEngine
from .kokoro_engine import KokoroEngine
from .macos_say_engine import MacOSSayEngine
from .piper_engine import PiperEngine

_ENGINE_TYPES: list[type[TTSEngine]] = [KokoroEngine, PiperEngine, MacOSSayEngine]
_instances: dict[str, TTSEngine] = {}


def _all_engines() -> list[TTSEngine]:
    out: list[TTSEngine] = []
    for cls in _ENGINE_TYPES:
        eid = cls.id  # type: ignore[attr-defined]
        if eid not in _instances:
            _instances[eid] = cls()  # type: ignore[call-arg]
        out.append(_instances[eid])
    return out


def list_engine_infos() -> list[EngineInfo]:
    return [e.info() for e in _all_engines()]


def pick_default_engine() -> TTSEngine:
    for engine in _all_engines():
        if engine.is_available():
            return engine
    raise RuntimeError(
        "No TTS engine available. Run ./setup.sh (Mac) and ensure espeak-ng is installed."
    )


def get_engine(engine_id: str | None = None) -> TTSEngine:
    if not engine_id:
        return pick_default_engine()
    for engine in _all_engines():
        if engine.id == engine_id and engine.is_available():
            return engine
    raise ValueError(f"Engine not available: {engine_id}")


def synthesize(
    text: str,
    *,
    engine_id: str | None = None,
    voice: str | None = None,
    speed: float = 0.95,
) -> SynthesisResult:
    engine = get_engine(engine_id)
    return engine.synthesize(text, voice=voice, speed=speed)


__all__ = [
    "EngineInfo",
    "SynthesisResult",
    "TTSEngine",
    "get_engine",
    "list_engine_infos",
    "pick_default_engine",
    "synthesize",
]
