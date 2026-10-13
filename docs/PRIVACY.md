# Privacy & Data Sovereignty Specification

LedgerLens was built from day one on a radical principle: **financial data belongs to the person who earned it.**

---

## What Leaves Your Machine?

### **Nothing. Zero bytes.**

- **No Analytics SDKs:** No Google Analytics, Mixpanel, Segment, or PostHog.
- **No Crash Uploaders:** No Sentry, Datadog, or Bugsnag uploading stack traces containing file paths or financial amounts.
- **No Remote AI APIs:** No OpenAI, Anthropic, or cloud endpoints in the extraction pipeline.
- **Local Logging Only:** Application logs write strictly to local disk in standard XDG directories (`logs/ledgerlens.log` and `logs/updates.log`).

---

## Architectural Enforcement in Code

1. **Import Guardrails:** The test suite (`tests/unit/test_layering.py`) scans every Python file in `app/**` and fails CI if `requests`, `httpx`, or `openai` are imported outside of the isolated `app/update/` subsystem.
2. **Localhost Socket Binding:** All inference communication is bounded to `http://localhost:11434` (local Ollama daemon) or embedded in-memory python routines.
3. **Delete All My Data Button:**
   - Available in the UI under **Settings & Privacy** or via CLI: `python -m app.cli purge --yes`.
   - Executes immediate SQL `DELETE` cascades across `line_items`, `corrections`, and `documents`.
