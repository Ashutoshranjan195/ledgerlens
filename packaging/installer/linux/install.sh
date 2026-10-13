#!/usr/bin/env bash
# Linux Installer for LedgerLens
set -euo pipefail
echo "==> Installing LedgerLens for Linux"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
python3 -m app.cli update --schema
echo "==> Done! Run with: python3 -m app.main"
