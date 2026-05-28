"""TTS engine protocol."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SynthesisResult:
    audio_bytes: bytes
    sample_rate: int
    engine: str
    voice: str


@dataclass
class EngineInfo:
    id: str
    name: str
    available: bool
    voices: list[str]
    default_voice: str | None
    note: str = ""


class TTSEngine(ABC):
    id: str
    name: str

    @abstractmethod
    def is_available(self) -> bool:
        ...

    @abstractmethod
    def list_voices(self) -> list[str]:
        ...

    @abstractmethod
    def default_voice(self) -> str:
        ...

    def info(self) -> EngineInfo:
        voices = self.list_voices() if self.is_available() else []
        default = self.default_voice() if self.is_available() else None
        return EngineInfo(
            id=self.id,
            name=self.name,
            available=self.is_available(),
            voices=voices,
            default_voice=default,
        )

    @abstractmethod
    def synthesize(self, text: str, *, voice: str | None = None, speed: float = 1.0) -> SynthesisResult:
        ...
