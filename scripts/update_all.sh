#!/usr/bin/env bash
# Wraps app update --all across all 5 channels
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "→ Running LedgerLens unified update subsystem..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

python3 -m app.cli update --all
