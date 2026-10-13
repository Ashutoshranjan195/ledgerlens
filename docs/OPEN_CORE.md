# Open Core Licensing & Pricing Model

LedgerLens operates on an honest, sustainable **Open-Core** model.

---

## What is 100% Free & Open-Source (MIT License)

The entire core repository is MIT licensed:
- Local processing pipeline (`app/core/*`)
- SQLite storage and migration runner (`app/store/*`)
- Inspectable agent harness & prompt loader (`app/agent/*`)
- Full evaluation suite & golden datasets (`evals/*`)
- Auto-update subsystem orchestrator (`app/update/*`)
- CLI interface (`app/cli.py`)
- Free Tier UI access: Up to **30 documents per month** forever on the `fast` profile (`llama3.2:3b`).

---

## Commercial Perpetual Edition ($49 One-Time)

For high-volume solopreneurs, studios, and agencies processing hundreds or thousands of receipts:
- **Price:** $49 one-time payment (perpetual license, no recurring SaaS subscriptions).
- **Entitlements:**
  - Unlimited document ingestion across all months.
  - Full access to `balanced` (`qwen2.5:7b-vl`) and `best` (`qwen2.5:32b-vl`) multimodal vision profiles.
  - Multi-export batch pipelines (custom Quickbooks, Xero, and TurboTax CSV mappings).
- **Verification Guarantee:**
  - Verified 100% **offline** via public-key cryptography (Ed25519).
  - Your license key is formatted as `PAYLOAD.SIGNATURE`.
  - The app **never phones home** to verify licenses. Pull the Ethernet cable—it still unlocks.
