# LedgerLens Local Hardware & Model Matrix

LedgerLens is designed to run 100% locally on standard consumer laptops up to dedicated studio workstations.

## Profiles

| Profile | Model Tag | Vision Support | Minimum RAM | Recommended Hardware |
| :--- | :--- | :--- | :--- | :--- |
| **Fast** | `llama3.2:3b` | Text OCR only | 8 GB | Base M1/M2 MacBook Air, Intel Core i5 / Ryzen 5 (8GB RAM) |
| **Balanced** *(Default)* | `qwen2.5:7b-vl` | Full VLM Vision | 16 GB | M1/M2/M3 Pro with 16GB Unified RAM, or PC with RTX 3060 (12GB) |
| **Best** | `qwen2.5:32b-vl` | High-Res VLM Vision | 32 GB+ | M-series Max/Ultra with 32GB+ RAM, or RTX 3090/4090 (24GB VRAM) |

## Swapping Profiles

Edit `app/models.yaml` or toggle in the UI:
```yaml
default_profile: balanced  # change to 'fast' or 'best'
```
No code changes required.
