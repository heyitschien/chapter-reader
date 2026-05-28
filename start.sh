#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo "No .venv found. Run ./setup.sh first."
  exit 1
fi

# shellcheck source=/dev/null
source .venv/bin/activate

PORT=8765
URL="http://127.0.0.1:${PORT}/"

if [[ "$(uname -s)" == "Darwin" ]]; then
  open "$URL" 2>/dev/null || true
fi

echo "Chapter Reader at $URL"
echo "Press Ctrl+C to stop."
exec python server.py
