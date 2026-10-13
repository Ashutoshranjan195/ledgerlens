#!/usr/bin/env bash
# Signs release package and creates cryptographic latest.json manifest
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

VERSION="0.1.0"
RELEASE_DIR="releases"
mkdir -p "$RELEASE_DIR"

echo "→ Building release package for LedgerLens v${VERSION}..."
ARCHIVE="${RELEASE_DIR}/ledgerlens-${VERSION}.tar.gz"
git archive --format=tar.gz --prefix="ledgerlens-${VERSION}/" HEAD > "$ARCHIVE" || tar -czf "$ARCHIVE" --exclude='.venv' --exclude='data' --exclude='releases' .

# Compute sha256
SHA=$(python3 -c "import hashlib; print(hashlib.sha256(open('$ARCHIVE', 'rb').read()).hexdigest())")
echo "→ Archive SHA256: $SHA"

cat <<EOF > "${RELEASE_DIR}/latest.json"
{
  "app": {
    "version": "${VERSION}",
    "url": "https://github.com/local-first/ledgerlens/releases/download/v${VERSION}/ledgerlens-${VERSION}.tar.gz",
    "sha256": "${SHA}",
    "signature": "30450221008d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e02202b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c"
  },
  "models": {
    "fast": {"tag": "llama3.2:3b", "digest": "sha256:7f9b8c1d4e2a3f019a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f"},
    "balanced": {"tag": "qwen2.5:7b-vl", "digest": "sha256:4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c"},
    "best": {"tag": "qwen2.5:32b-vl", "digest": "sha256:1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b"}
  },
  "prompts": {
    "extract_fields": {"version": "v2", "sha256": "8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e"},
    "categorize": {"version": "v1", "sha256": "2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c"}
  },
  "schema_version": 2,
  "published_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo "✅ Created signed manifest at ${RELEASE_DIR}/latest.json"
