#!/bin/bash
set -euo pipefail
cd -- "$(dirname "${BASH_SOURCE[0]}")"
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This installer is for macOS. On Windows, use setup.ps1." >&2
  exit 1
fi
skip_model=0
if [[ "${1:-}" == "--skip-model" ]]; then
  skip_model=1
elif [[ $# -gt 0 ]]; then
  echo "Usage: bash setup.sh [--skip-model]" >&2
  exit 1
fi
if [[ ! -x .venv/bin/python ]]; then
  if ! command -v python3.12 >/dev/null 2>&1; then
    echo "Install Python 3.12 first (python.org or: brew install python@3.12)." >&2
    exit 1
  fi
  python3.12 -m venv .venv
fi
.venv/bin/python -c 'import platform,struct,sys; sys.exit(0 if sys.version_info[:2]==(3,12) and struct.calcsize("P")==8 and platform.machine() in ("arm64","x86_64") else 1)' || {
  echo "Use 64-bit Python 3.12. Apple Silicon users should use native arm64 Python." >&2
  exit 1
}
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
if [[ "$skip_model" -eq 0 ]]; then
  .venv/bin/python scripts/download_model.py
fi
echo "Setup complete. Double-click the .command launcher, or run .venv/bin/python app/launch.pyw."
