# Recruiter Notes

## What this project demonstrates

Chapter Reader shows **documentation workflow thinking** and **user-facing tool design**. It is not a flashy AI product — it is a practical tool for listening to long-form text during writing and review cycles.

The proof is in clarity: setup scripts, troubleshooting table, privacy guarantees, and engine fallbacks that respect users who cannot install every dependency.

## What to look at first

1. **Run it** — `./setup.sh && ./start.sh` → paste text → Play.
2. **README troubleshooting table** — shows support-minded documentation.
3. **`discover.py`** — diagnostic script that reports which TTS engine will be used.
4. **Project layout** — small, understandable structure (server, engines, static UI).

## What is intentionally out of scope

- Cloud hosting, user accounts, or sync
- Commercial audiobook platform claims
- Integration with private Career OS or employer systems
- Electron desktop build (exists in a separate manuscript repo fork; this public repo is the standalone web version)

## Interview talking points

- **Writing workflow:** How listening catches issues that silent reading misses — pacing, repetition, awkward transitions.
- **Privacy design:** Why localhost-only matters for draft manuscripts and sensitive notes.
- **Support documentation:** The troubleshooting table as a pattern I reuse for user-facing tools.
- **Fallback engines:** Kokoro → Piper → macOS Say — graceful degradation when dependencies are missing.
- **Connection to product support:** Same mindset as reducing user confusion — clear setup, predictable behavior, honest scope.
