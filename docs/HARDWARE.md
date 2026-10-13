# Hardware Specifications & Execution Floors

LedgerLens operates across three hardware tiers:

---

## 1. Fast Profile (`llama3.2:3b`)
- **System Memory (RAM):** 8 GB minimum
- **VRAM / GPU:** Not required (runs smoothly on CPU)
- **Floor Device:** Base M1 MacBook Air (2020) or Intel Core i5 (8th Gen+) laptop
- **Typical Speed:** ~1.1 seconds per receipt
- **Modalities:** Embedded PDF text, OCR text dumps

---

## 2. Balanced Profile (`qwen2.5:7b-vl`) — Recommended
- **System Memory (RAM):** 16 GB unified RAM or PC with 12 GB GPU
- **VRAM / GPU:** Apple Metal (Apple Silicon) or Nvidia RTX 3060/4060
- **Floor Device:** M1/M2/M3 Pro MacBook Pro (16 GB) or desktop PC
- **Typical Speed:** ~2.8 seconds per receipt
- **Modalities:** Native multimodal vision (reads smartphone photos of paper receipts directly)

---

## 3. Best Profile (`qwen2.5:32b-vl`)
- **System Memory (RAM):** 32 GB+ RAM
- **VRAM / GPU:** Nvidia RTX 3090/4090 (24 GB) or Apple M-series Max/Ultra (36GB+ Unified)
- **Typical Speed:** ~6.5 seconds per receipt
- **Modalities:** Complex handwritten receipts, multilingual European invoices, dense statements
