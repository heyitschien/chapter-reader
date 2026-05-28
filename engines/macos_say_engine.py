"""macOS built-in `say` — fallback using Premium/Enhanced voices."""
from __future__ import annotations

import platform
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from .base import SynthesisResult, TTSEngine

# Prefer Premium/Enhanced narration voices
VOICE_PRIORITY = (
    "Samantha",
    "Ava",
    "Allison",
    "Susan",
    "Karen",
    "Serena",
    "Daniel",
    "Tom",
    "Oliver",
    "Zoe",
    "Nicky",
    "Jamie",
)


def _parse_say_voices() -> list[dict]:
    if platform.system() != "Darwin" or not shutil.which("say"):
        return []
    try:
        out = subprocess.run(
            ["say", "-v", "?"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
    except Exception:
        return []
    voices: list[dict] = []
    for line in out.stdout.splitlines():
        # Samantha                en_US    # Premium?
        m = re.match(r"^(\S+)\s+([a-z]{2}(?:_[A-Z]{2})?)", line.strip())
        if not m:
            continue
        name, lang = m.group(1), m.group(2)
        if not lang.lower().startswith("en"):
            continue
        premium = "premium" in line.lower() or "enhanced" in line.lower()
        voices.append({"name": name, "lang": lang, "premium": premium})
    return voices


def _pick_best_voice(voices: list[dict]) -> str | None:
    if not voices:
        return None
    by_name = {v["name"]: v for v in voices}
    for preferred in VOICE_PRIORITY:
        if preferred in by_name:
            return preferred
    premium = [v for v in voices if v.get("premium")]
    if premium:
        return premium[0]["name"]
    return voices[0]["name"]


class MacOSSayEngine(TTSEngine):
    id = "macos_say"
    name = "macOS Say (system voices)"

    def is_available(self) -> bool:
        return platform.system() == "Darwin" and shutil.which("say") is not None

    def list_voices(self) -> list[str]:
        return [v["name"] for v in _parse_say_voices()]

    def default_voice(self) -> str:
        picked = _pick_best_voice(_parse_say_voices())
        return picked or "Samantha"

    def synthesize(self, text: str, *, voice: str | None = None, speed: float = 1.0) -> SynthesisResult:
        if not self.is_available():
            raise RuntimeError("macOS say is only available on Darwin")
        voice = voice or self.default_voice()
        # say rate: ~175 WPM default; scale with speed slider
        rate = int(175 * max(0.5, min(2.0, speed or 1.0)))
        with tempfile.TemporaryDirectory() as tmp:
            aiff = Path(tmp) / "out.aiff"
            wav = Path(tmp) / "out.wav"
            subprocess.run(
                ["say", "-v", voice, "-r", str(rate), "-o", str(aiff), text],
                check=True,
                capture_output=True,
            )
            # Convert to WAV for browser playback
            if shutil.which("afconvert"):
                subprocess.run(
                    ["afconvert", "-f", "WAVE", "-d", "LEI16", str(aiff), str(wav)],
                    check=True,
                    capture_output=True,
                )
                data = wav.read_bytes()
            else:
                data = aiff.read_bytes()
            return SynthesisResult(
                audio_bytes=data,
                sample_rate=22050,
                engine=self.id,
                voice=voice,
            )
