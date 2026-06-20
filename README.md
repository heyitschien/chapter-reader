# Chapter Reader

**Paste long-form text. Hear it read aloud. Nothing leaves your machine.**

This repo demonstrates how I organize long-form reading, chapter review, and writing iteration into a structured workflow — a local tool for listening to books, articles, markdown notes, and drafts in a natural offline voice.

Built for authors and readers who want audiobook-style playback without cloud APIs or subscriptions.

---

## What this is

A small local web app (Python + FastAPI) that converts pasted text to speech using on-device neural TTS. No API keys, no cloud upload — everything runs on `127.0.0.1`.

Originally built for long-form book production; this is the **standalone, public** copy. Also used in the [Printing Intelligence on Sand](https://github.com/heyitschien/printing-intelligence-on-sand) manuscript workflow.

---

## Why it matters

Documentation and writing work often involves reading long drafts aloud to catch awkward phrasing, pacing issues, and structural problems. Chapter Reader turns that into a repeatable local workflow — useful for authors, technical writers, and anyone doing structured content review.

---

## What it demonstrates

- Structured reading/review workflow for long-form content
- Documentation-minded tool design (clear setup, troubleshooting table)
- Privacy-first architecture (localhost only, no cloud APIs)
- Practical Python/FastAPI implementation with offline TTS
- User-facing simplicity — paste, play, adjust speed
- AI-assisted content operations support (listening while reviewing AI-generated drafts)

---

## Recruiter quick scan

This project demonstrates:

- Documentation and structured review workflow design
- Clear, customer-facing communication in README and troubleshooting
- Privacy-conscious tool building (no API keys required)
- Practical implementation skills (Python, FastAPI, local TTS)
- Writing systems thinking — versioned iteration through listening
- Support-minded UX (setup script, Finder launcher, engine fallbacks)

**Start here:** run locally (below) → paste a paragraph → press Play

---

## Demo / walkthrough

1. Run `./setup.sh` once, then `./start.sh`
2. Browser opens **http://127.0.0.1:8765/**
3. Paste a chapter or article excerpt
4. Press **Play** — listen for pacing, clarity, and awkward phrasing
5. Adjust speed slider (default `0.95` for book pace)

Optional: enable markdown stripping to hear clean prose without heading syntax.

---

## How to run locally

**Requirements:** macOS 12+, Python **3.10–3.12** (not 3.13+), [Homebrew](https://brew.sh) recommended.

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

### Linux (developers)

```bash
sudo apt-get install -y espeak-ng
./setup.sh && ./start.sh
```

### Check your install

```bash
.venv/bin/python discover.py
```

---

## Screenshots / video

See [docs/screenshots/](./docs/screenshots/) — placeholders for future UI captures.

Video walkthrough is optional for this repo.

---

## Notes on privacy / scope

| In scope (public) | Out of scope |
|---|---|
| Local-only TTS tool, MIT licensed | Cloud sync or multi-user deployment |
| Offline playback after setup | Enterprise document management |
| Open-source standalone copy | Claims of commercial product adoption |

- **No API keys** — runs on `127.0.0.1` only
- **Offline after setup** — neural TTS via [Kokoro-82M](https://github.com/hexgrad/kokoro) (`af_bella` default)
- Text never sent to the cloud

---

## What you get

| Feature | Detail |
|---------|--------|
| UI | Paste box, play / pause / stop, speed slider (default `0.95` for book pace) |
| Engines | Kokoro → Piper (if installed) → macOS `say` |
| Privacy | Server binds localhost only; text never sent to the cloud |

### Engine priority

| Order | Engine | When used |
|-------|--------|-----------|
| 1 | Kokoro | `espeak-ng` + Python deps available |
| 2 | Piper | `.onnx` voice already on disk |
| 3 | macOS Say | Darwin fallback; best Premium voice auto-selected |

Override engine and voice in the UI anytime.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `espeak-ng not found` | `brew install espeak-ng` (Mac) |
| Kokoro import error | Use Python 3.12: `python3.12 -m venv .venv` then re-run `./setup.sh` |
| Slow first play | Normal: model download on first synthesis |
| Pause before audio | Normal: first paragraphs pre-render for smooth playback |
| Robotic macOS voice | Run setup so Kokoro is primary |
| Port in use | Change `PORT` in `server.py` or stop the other process on 8765 |

---

## Project layout

```
chapter-reader/
├── setup.sh          # one-time install
├── start.sh          # run server + open browser (Mac)
├── start.command     # Finder double-click launcher
├── server.py         # local FastAPI app
├── discover.py       # asset / engine check
├── engines/          # Kokoro, Piper, macOS say
├── static/           # web UI
└── docs/
    └── screenshots/
```

---

## License

MIT — see [LICENSE](LICENSE).

---

## Contact

- **GitHub:** https://github.com/heyitschien
- **LinkedIn:** https://www.linkedin.com/in/chien-escalera-duong-4ba535347/

For deeper context, see [docs/recruiter-notes.md](./docs/recruiter-notes.md).
