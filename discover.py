#!/usr/bin/env python3
"""Scan the machine for local TTS assets before downloading anything."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


def _hf_kokoro_cached() -> list[str]:
    hub = Path.home() / ".cache" / "huggingface" / "hub"
    if not hub.exists():
        return []
    return [str(p) for p in hub.glob("models--hexgrad--Kokoro-82M*") if p.is_dir()]


def _espeak_paths() -> list[str]:
    found = []
    for name in ("espeak-ng", "espeak"):
        p = shutil.which(name)
        if p:
            found.append(p)
    return found


def _brew_espeak() -> str | None:
    for prefix in ("/opt/homebrew", "/usr/local"):
        p = Path(prefix) / "bin" / "espeak-ng"
        if p.exists():
            return str(p)
    return None


def main() -> int:
    from engines.piper_engine import discover_piper_models
    from engines import list_engine_infos, pick_default_engine

    report = {
        "espeak": _espeak_paths() or ([_brew_espeak()] if _brew_espeak() else []),
        "kokoro_hf_cache": _hf_kokoro_cached(),
        "piper_models": discover_piper_models(),
        "piper_binary": shutil.which("piper"),
        "say_binary": shutil.which("say"),
    }

    print("Chapter Reader — local asset discovery\n")
    print(json.dumps(report, indent=2))
    print()

    if report["espeak"]:
        print(f"✓ espeak: {', '.join(x for x in report['espeak'] if x)}")
    else:
        print("✗ espeak-ng not found (required for Kokoro). Install: brew install espeak-ng")

    if report["kokoro_hf_cache"]:
        print(f"✓ Kokoro model cache: {len(report['kokoro_hf_cache'])} path(s)")
    else:
        print("○ Kokoro weights not cached yet (first run will download ~200MB)")

    piper_n = len(report["piper_models"])
    if piper_n:
        print(f"✓ Piper voices on disk: {piper_n}")
    else:
        print("○ No Piper ONNX models found")

    if report["say_binary"]:
        print("✓ macOS say available (Darwin fallback)")
    else:
        print("○ say not available (expected off-macOS)")

    print("\nEngines:")
    for info in list_engine_infos():
        mark = "✓" if info.available else "○"
        print(f"  {mark} {info.id}: {info.name}")
        if info.available and info.default_voice:
            print(f"      default voice: {info.default_voice}")

    try:
        default = pick_default_engine()
        print(f"\n→ Default engine: {default.id} (voice: {default.default_voice()})")
    except RuntimeError as e:
        print(f"\n→ No engine ready: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
