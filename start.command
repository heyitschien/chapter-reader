#!/bin/bash
# Double-click launcher for macOS Finder.
cd "$(dirname "$0")" || exit 1
chmod +x setup.sh start.sh 2>/dev/null || true
if [[ ! -d .venv ]]; then
  osascript -e 'display dialog "Run setup first: open Terminal in this folder and run ./setup.sh" buttons {"OK"} default button 1' 2>/dev/null || echo "Run ./setup.sh first."
  exit 1
fi
exec ./start.sh
