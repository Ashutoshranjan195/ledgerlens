#!/usr/bin/env bash
set -euo pipefail
echo "→ simulating airplane mode (no network egress allowed)"
# Linux: drop egress via unshare; macOS: rely on app-level offline flag
if [[ "$(uname)" == "Linux" ]]; then
  unshare -n bash -c 'python -m app.cli run --sample samples/receipts'
else
  LEDGERLENS_OFFLINE=1 python -m app.cli run --sample samples/receipts
fi
echo "✅ core loop completed with zero network access"
