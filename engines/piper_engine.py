"""Piper ONNX TTS — used when voices already exist on disk."""
from __future__ import annotations

import io
import json
import shutil
import subprocess
from pathlib import Path

from .base import SynthesisResult, TTSEngine

# Prefer higher-quality English voices when multiple exist
VOICE_RANK = (
    "lessac",
    "amy",
    "ryan",
    "kristin",
    "cori",
    "alba",
    "libritts",
)


def _piper_search_dirs() -> list[Path]:
    home = Path.home()
    candidates = [
        home / ".local" / "share" / "piper" / "voices",
        home / "Library" / "Application Support" / "piper" / "voices",
        home / "Library" / "Application Support" / "piper",
        Path("/opt/homebrew/share/piper/voices"),
        Path("/opt/homebrew/share/piper"),
        Path("/usr/local/share/piper/voices"),
        Path("/usr/local/share/piper"),
    ]
    return [p for p in candidates if p.exists()]


def discover_piper_models() -> list[dict]:
    """Return [{onnx, json, name, quality}, ...]."""
    found: list[dict] = []
    seen: set[str] = set()
    for root in _piper_search_dirs():
        for onnx in root.rglob("*.onnx"):
            key = str(onnx.resolve())
            if key in seen:
                continue
            seen.add(key)
            cfg = onnx.with_suffix(".onnx.json")
            if not cfg.exists():
                cfg = Path(str(onnx) + ".json")
            name = onnx.stem
            quality = ""
            if cfg.exists():
                try:
                    meta = json.loads(cfg.read_text(encoding="utf-8"))
                    name = meta.get("dataset", name) or name
                    quality = meta.get("quality", "")
                except Exception:
                    pass
            found.append(
                {
                    "onnx": str(onnx),
                    "json": str(cfg) if cfg.exists() else "",
                    "name": name,
                    "quality": quality,
                    "path": str(onnx.parent),
                }
            )
    return found


def _rank_voice(model: dict) -> tuple[int, str]:
    blob = (model["name"] + " " + model["onnx"]).lower()
    for i, token in enumerate(VOICE_RANK):
        if token in blob:
            return (i, model["name"])
    return (len(VOICE_RANK), model["name"])


def _best_model(models: list[dict]) -> dict | None:
    if not models:
        return None
    en = [m for m in models if "en" in m["onnx"].lower() or "en_" in m["onnx"].lower()]
    pool = en if en else models
    return sorted(pool, key=_rank_voice)[0]


_piper_voice = None
_piper_model_path: str | None = None


class PiperEngine(TTSEngine):
    id = "piper"
    name = "Piper (ONNX, offline)"

    def is_available(self) -> bool:
        models = discover_piper_models()
        if not models:
            return False
        if shutil.which("piper"):
            return True
        try:
            import piper  # noqa: F401, PLC0415

            return True
        except ImportError:
            return False

    def list_voices(self) -> list[str]:
        return [m["name"] for m in discover_piper_models()]

    def default_voice(self) -> str:
        best = _best_model(discover_piper_models())
        return best["name"] if best else "default"

    def _resolve_model(self, voice: str | None) -> dict:
        models = discover_piper_models()
        if not models:
            raise RuntimeError("No Piper voice models found")
        if voice:
            for m in models:
                if voice in m["name"] or voice in m["onnx"]:
                    return m
        best = _best_model(models)
        if not best:
            raise RuntimeError("No Piper voice models found")
        return best

    def _synthesize_cli(self, text: str, model: dict, speed: float) -> bytes:
        import tempfile  # noqa: PLC0415

        piper_bin = shutil.which("piper")
        if not piper_bin:
            raise RuntimeError("piper binary not found")
        length_scale = max(0.5, min(2.0, 1.0 / speed)) if speed else 1.0
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            out_path = tmp.name
        cmd = [
            piper_bin,
            "--model",
            model["onnx"],
            "--output_file",
            out_path,
        ]
        if model.get("json"):
            cmd.extend(["--config", model["json"]])
        cmd.extend(["--length_scale", str(length_scale)])
        proc = subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            capture_output=True,
            check=False,
        )
        try:
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr.decode("utf-8", errors="replace") or "piper failed")
            return Path(out_path).read_bytes()
        finally:
            Path(out_path).unlink(missing_ok=True)

    def _synthesize_python(self, text: str, model: dict, speed: float) -> bytes:
        global _piper_voice, _piper_model_path
        from piper import PiperVoice  # noqa: PLC0415

        onnx = model["onnx"]
        if _piper_model_path != onnx:
            cfg = model.get("json") or None
            _piper_voice = PiperVoice.load(onnx, config_path=cfg)
            _piper_model_path = onnx
        assert _piper_voice is not None
        length_scale = max(0.5, min(2.0, 1.0 / speed)) if speed else 1.0
        buf = io.BytesIO()
        with _piper_voice.synthesize(text, length_scale=length_scale) as gen:
            import wave  # noqa: PLC0415

            wf = wave.open(buf, "wb")
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(_piper_voice.config.sample_rate)
            for chunk in gen:
                wf.writeframes(chunk.audio_int16_bytes)
            wf.close()
        return buf.getvalue()

    def synthesize(self, text: str, *, voice: str | None = None, speed: float = 1.0) -> SynthesisResult:
        model = self._resolve_model(voice)
        if shutil.which("piper"):
            wav = self._synthesize_cli(text, model, speed)
        else:
            wav = self._synthesize_python(text, model, speed)
        # Piper CLI may write raw PCM; assume WAV from python path
        sample_rate = 22050
        if model.get("json"):
            try:
                meta = json.loads(Path(model["json"]).read_text(encoding="utf-8"))
                sample_rate = int(meta.get("audio", {}).get("sample_rate", sample_rate))
            except Exception:
                pass
        return SynthesisResult(
            audio_bytes=wav,
            sample_rate=sample_rate,
            engine=self.id,
            voice=model["name"],
        )
