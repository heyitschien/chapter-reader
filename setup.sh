#!/usr/bin/env bash
# One-time setup for Chapter Reader (macOS primary; Linux supported for dev).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "=== Chapter Reader setup ==="

# System: espeak-ng (required for Kokoro)
if ! command -v espeak-ng >/dev/null 2>&1 && ! command -v espeak >/dev/null 2>&1; then
  if [[ "$(uname -s)" == "Darwin" ]] && command -v brew >/dev/null 2>&1; then
    echo "Installing espeak-ng via Homebrew…"
    brew install espeak-ng
  elif command -v apt-get >/dev/null 2>&1; then
    echo "Installing espeak-ng via apt…"
    sudo apt-get update -qq
    sudo apt-get install -y -qq espeak-ng
  else
    echo "Warning: espeak-ng not found. Install manually (brew install espeak-ng)."
  fi
fi

# Python venv (prefer 3.12, then 3.11, then python3)
PY=""
for candidate in python3.12 python3.11 python3.10 python3; do
  if command -v "$candidate" >/dev/null 2>&1; then
    ver="$("$candidate" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    major="${ver%%.*}"
    minor="${ver#*.}"
    if [[ "$major" -eq 3 && "$minor" -ge 10 && "$minor" -le 12 ]]; then
      PY="$candidate"
      break
    fi
  fi
done

if [[ -z "$PY" ]]; then
  echo "Error: need Python 3.10–3.12 for Kokoro."
  exit 1
fi

echo "Using $PY ($($PY --version))"

if [[ ! -d .venv ]]; then
  if ! "$PY" -m venv .venv 2>/dev/null; then
    if command -v apt-get >/dev/null 2>&1; then
      echo "Installing python3-venv…"
      sudo apt-get install -y -qq "python${PY#python}-venv" || sudo apt-get install -y -qq python3-venv
    fi
    "$PY" -m venv .venv
  fi
fi

# shellcheck source=/dev/null
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "=== Asset discovery ==="
python discover.py || true

echo ""
echo "=== Prefetch Kokoro model (first run may download ~200MB) ==="
python - <<'PY'
import sys
sys.path.insert(0, ".")
try:
    from engines.kokoro_engine import prefetch_model
    if prefetch_model():
        print("Kokoro ready.")
    else:
        print("Kokoro prefetch skipped (espeak or deps missing).")
except Exception as e:
    print(f"Kokoro prefetch note: {e}")
PY

echo ""
echo "Setup complete. Run: ./start.sh"
