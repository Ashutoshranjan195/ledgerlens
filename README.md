# LedgerLens

> **Local-First, Offline, Zero-Marginal-Cost Receipt & Expense Ledger for Creatives and Solopreneurs.**  
> Turn messy shoebox receipt photos and invoice PDFs into tax-categorized CSVs and audit-proof JSON ledgers directly on your laptop ($49 one-time / generous free tier forever).

[![Watch Demo (90s offline walkthrough, WiFi off)](https://img.shields.io/badge/Demo_Video-90s_Walkthrough_(WiFi_off)-2ea44f?style=for-the-badge&logo=youtube)](https://ledgerlens.dev/demo)
*(Demo: 90-second end-to-end receipt extraction with WiFi off in airplane mode)*

---

## Install (3 lines, no cloud account required)

```bash
curl -fsSL https://ledgerlens.dev/install.sh | bash
ledgerlens onboard
# drop a folder of receipts into the app window — done
```

Works fully offline after first run. Windows: see
[packaging/installer/windows/install.ps1](packaging/installer/windows/install.ps1).

---

## Hardware Floor

- **Fast Profile (`llama3.2:3b`):** **8 GB RAM floor** (runs on base M1/M2/M3 MacBook Air or modern Intel Core i5 / AMD Ryzen laptop).
- **Balanced Profile (`qwen2.5:7b-vl` - Recommended):** 16 GB RAM with Apple Silicon or dedicated GPU (RTX 3060+).
- **Best Profile (`qwen2.5:32b-vl`):** 32 GB+ RAM studio grade workstation.

---

## Why Open?

- **Zero Marginal Cost:** Running 1,000 document extractions costs **$0.00** locally vs. **$35.00–$55.00** on closed cloud APIs (GPT-4o Vision).
- **Absolute Privacy (No Server):** No data ever leaves your laptop. Zero telemetry, no analytics SDKs, and no cloud retention risk for client names or bank statements. Includes a one-click "Delete all my data" button.
- **Model-Swappable in 1 Line:** Change one line in `app/models.yaml` to swap between `llama3.2:3b`, `qwen2.5:7b-vl`, and `qwen2.5:32b-vl` without code edits.

---

## Comparison vs Closed APIs

| Feature | Closed Cloud APIs (GPT-4o / Claude) | LedgerLens (Open Weights) |
| :--- | :--- | :--- |
| **Data Privacy** | PII & client names transmitted to third-party clouds | **100% on-device.** Nothing leaves RAM / local disk. |
| **Offline Capability** | Fails immediately without internet | **Runs in airplane mode** on a flight or remote photo shoot. |
| **Cost at 1,000 scans** | ~$35.00–$55.00 | **$0.00** |
| **Latency & Throttling** | Rate limits, 429 errors, vendor outages | Consistent local latency, zero external dependencies. |
| **Model Portability** | Locked to proprietary vendor endpoints | Swap `llama3.2:3b` ↔ `qwen2.5:7b-vl` with one YAML toggle. |

---

## The Pitch

Every month, freelance photographers, designers, and solopreneurs waste 4 to 8 hours squinting at coffee-stained paper receipts, crumpled equipment slips, and scattered PDF invoices. The existing alternatives are broken:
- **Cloud Bookkeeping SaaS ($20–$60/mo):** Uploads your private clients, vendor bank details, and personal expenses to third-party cloud servers.
- **ChatGPT Wrappers:** Per-token billing that leaks financial data, hallucinates totals without confidence bounds, and breaks down completely when you're on a shoot without Wi-Fi.

**LedgerLens is 100% local.** It processes images, scans, and PDFs using local open-weight vision-language models (`qwen2.5:7b-vl`, `llama3.2:3b`), validates mathematical integrity locally, remembers your corrections via local SQLite few-shot memory, and outputs tax-ready CSV/JSON.

---

## The Offline Guarantee (Airplane-Mode Verified)

1. **Pull the plug:** Pull the Wi-Fi card or board a flight. Every core feature—ingestion, OCR/VLM extraction, validation, correction memory, export—functions with zero internet connectivity.
2. **Zero Telemetry:** LedgerLens contains no Google Analytics, no PostHog, no Sentry phone-home SDKs. Logs stay on your local disk in standard XDG data directories.
3. **Zero Marginal Cost:** 1 scan or 10,000 scans costs $0.00.
4. **Open Weights First:** Powered locally by Ollama with embedded `llama-cpp-python` fallback. Model swapping requires changing a single line in `app/models.yaml`.
5. **Delete All Data Button:** One click or one command purges the entire SQLite database and cached assets forever.

---

## Licensing & Open-Core Model

- **Core Engine & CLI:** MIT Licensed (100% free forever).
- **Commercial Edition:** $49 one-time perpetual license with offline Ed25519 signature verification. Free tier includes 30 documents/month forever. See [docs/OPEN_CORE.md](docs/OPEN_CORE.md) for details.
