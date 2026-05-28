#!/usr/bin/env python3
"""Local chapter reader API — bind 127.0.0.1 only."""
from __future__ import annotations

import base64
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engines import get_engine, list_engine_infos, pick_default_engine, synthesize  # noqa: E402
from text_utils import split_paragraphs, strip_markdown  # noqa: E402

HOST = "127.0.0.1"
PORT = 8765

app = FastAPI(title="Chapter Reader", version="1.0.0")


class SpeakRequest(BaseModel):
    text: str = Field(..., min_length=1)
    engine: str | None = None
    voice: str | None = None
    speed: float = Field(default=0.95, ge=0.5, le=2.0)
    strip_md: bool = True


class PrepareRequest(BaseModel):
    text: str
    strip_md: bool = True


class SpeakResponse(BaseModel):
    audio_base64: str
    sample_rate: int
    engine: str
    voice: str
    char_count: int


@app.get("/api/status")
def api_status():
    engines = list_engine_infos()
    try:
        default_engine = pick_default_engine()
        default = {
            "engine": default_engine.id,
            "voice": default_engine.default_voice(),
        }
    except RuntimeError:
        default = None
    return {"engines": engines, "default": default}


@app.post("/api/prepare")
def api_prepare(body: PrepareRequest):
    text = strip_markdown(body.text) if body.strip_md else body.text.strip()
    chunks = split_paragraphs(text)
    return {"chunks": chunks, "count": len(chunks), "char_count": len(text)}


@app.post("/api/speak", response_model=SpeakResponse)
def api_speak(body: SpeakRequest):
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty text")
    if body.strip_md:
        text = strip_markdown(text)
    if not text:
        raise HTTPException(status_code=400, detail="No speakable text after markdown strip")
    try:
        result = synthesize(
            text,
            engine_id=body.engine,
            voice=body.voice,
            speed=body.speed,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    b64 = base64.standard_b64encode(result.audio_bytes).decode("ascii")
    return SpeakResponse(
        audio_base64=b64,
        sample_rate=result.sample_rate,
        engine=result.engine,
        voice=result.voice,
        char_count=len(text),
    )


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")


static_dir = ROOT / "static"
if static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


def main():
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()
