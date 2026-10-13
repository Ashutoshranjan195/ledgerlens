#!/usr/bin/env bash
# One-Command Local-First Installer for LedgerLens
# Zero cloud accounts required.
set -euo pipefail

echo "=========================================================="
echo "           Installing LedgerLens (Local-First)            "
echo "=========================================================="

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "❌ Error: Python 3.10+ is required on your system."
    exit 1
fi

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "→ Detected Python: $PY_VER"

# Setup virtual environment
INSTALL_DIR="${HOME}/.local/share/ledgerlens"
mkdir -p "$INSTALL_DIR"
cd "$(dirname "$0")/.."

echo "→ Creating local virtual environment in .venv..."
python3 -m venv .venv
source .venv/bin/activate

echo "→ Installing local dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -e .

# Check Ollama
if command -v ollama &>/dev/null; then
    echo "→ Ollama found. Ensuring recommended profile weights are available..."
    ollama pull qwen2.5:7b-vl || echo "ℹ️ Model pull skipped or will run on first launch."
else
    echo "ℹ️ Note: Ollama not found in PATH. LedgerLens will run using embedded fallback mode."
fi

# Run initial migrations
python3 -m app.cli update --schema

echo ""
echo "✅ LedgerLens successfully installed!"
echo "To launch the UI: make run  (or .venv/bin/python -m app.main)"
echo "To process files: .venv/bin/python -m app.cli run --sample samples/receipts"
