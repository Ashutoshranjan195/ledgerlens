#!/usr/bin/env bash
# Post-update boot check and smoke test
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "→ Running post-update smoke test..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 1. Verify schema loads without error
python3 -c "from app.store.db import get_db; db = get_db(); assert db.get_connection() is not None; print('✓ Database connectivity OK')"

# 2. Verify config loads
python3 -c "from app.config import get_config; cfg = get_config(); print('✓ Config and models.yaml OK')"

# 3. Verify single sample run completes
python3 -m app.cli run --file samples/receipts/bh_photo_receipt.txt

echo "✅ Smoke test passed: All core modules boot cleanly."
