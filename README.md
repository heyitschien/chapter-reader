# Chapter Reader

**Paste long-form text. Hear it read aloud. Nothing leaves your machine.**

A small local web app for listening to books, articles, markdown notes, and drafts in a natural offline voice. Built for authors and readers who want audiobook-style playback without cloud APIs or subscriptions.

- **No API keys** — runs on `127.0.0.1` only
- **Offline after setup** — neural TTS via [Kokoro-82M](https://github.com/hexgrad/kokoro) (`af_bella` default)
- **Smooth playback** — pre-renders the first paragraphs, then stays ahead while you listen
- **Markdown-aware** — optional strip of headings, links, and emphasis

## Quick start (Mac)

**Requirements:** macOS 12+, Python **3.10–3.12** (not 3.13+), [Homebrew](https://brew.sh) recommended.

**This machine (CascadeProjects):** `~/CascadeProjects/chapter-reader` — open `chapter-reader.code-workspace` in Cursor, or:

```bash
cd ~/CascadeProjects/chapter-reader
```

**Clone elsewhere:**

```bash
git clone https://github.com/heyitschien/chapter-reader.git
cd chapter-reader
chmod +x setup.sh start.sh start.command
./setup.sh
./start.sh
```

Your browser opens **http://127.0.0.1:8765/** — paste text, press **Play**.

**Everyday users:** after `./setup.sh` once, double-click **`start.command`** in Finder.

**First run:** Kokoro downloads ~200MB of model weights (one time), then works offline.

## What you get

| Feature | Detail |
|---------|--------|
| UI | Paste box, play / pause / stop, speed slider (default `0.95` for book pace) |
| Engines | Kokoro → Piper (if installed) → macOS `say` |
| Privacy | Server binds localhost only; text never sent to the cloud |

## Engine priority

| Order | Engine | When used |
|-------|--------|-----------|
| 1 | Kokoro | `espeak-ng` + Python deps available |
| 2 | Piper | `.onnx` voice already on disk |
| 3 | macOS Say | Darwin fallback; best Premium voice auto-selected |

Override engine and voice in the UI anytime.

## Linux (developers)

Supported for development. Install `espeak-ng` and Python 3.10–3.12, then `./setup.sh` and `./start.sh`. Kokoro is the primary engine; macOS `say` is unavailable.

```bash
sudo apt-get install -y espeak-ng
./setup.sh && ./start.sh
```

## Check your install

```bash
.venv/bin/python discover.py
```

Reports espeak, Kokoro cache, Piper voices, and which engine will be used by default.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `espeak-ng not found` | `brew install espeak-ng` (Mac) |
| Kokoro import error | Use Python 3.12: `python3.12 -m venv .venv` then re-run `./setup.sh` |
| Slow first play | Normal: model download on first synthesis |
| Pause before audio | Normal: first paragraphs pre-render for smooth playback |
| Robotic macOS voice | Run setup so Kokoro is primary |
| Port in use | Change `PORT` in `server.py` or stop the other process on 8765 |

## Project layout

```
chapter-reader/
├── setup.sh          # one-time install
├── start.sh          # run server + open browser (Mac)
├── start.command     # Finder double-click launcher
├── server.py         # local FastAPI app
├── discover.py       # asset / engine check
├── engines/          # Kokoro, Piper, macOS say
└── static/           # web UI
```

## Related

Originally built for long-form book production. Used in the [Printing Intelligence on Sand](https://github.com/heyitschien/printing-intelligence-on-sand) manuscript workflow; this repo is the **standalone, public** copy.

## License

MIT — see [LICENSE](LICENSE).
