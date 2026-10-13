# The 5 Auto-Update Channels

LedgerLens implements an offline-safe, eval-gated update subsystem coordinated by `app/update/orchestrator.py` (`app update --all`).

---

## Channel 1: Application Code
- **Mechanism:** Static `latest.json` release manifest verified via Ed25519 cryptographic signatures.
- **Offline Behavior:** If offline, the check skips without throwing errors.
- **Rollback:** Automatic rollback to previous release archive if new version fails boot check.

---

## Channel 2: Local Model Weights
- **Mechanism:** `app/models.yaml` pins model tags and SHA256 digests. `app update models` pulls newer digests via local Ollama.
- **Safety Rule:** Old weights are NEVER automatically purged (guaranteeing offline resilience).
- **Verification:** Runs a prompt smoke test before switching pointers.

---

## Channel 3: Prompts & Configs (Eval-Gated)
- **Mechanism:** Prompts live in versioned Markdown files (`prompts/*.md`) tracked in `prompts/registry.yaml`.
- **The Eval Gate:** Candidate prompts are evaluated against the golden dataset (`evals/golden/*.jsonl`). A candidate is ONLY promoted if:
  $$\text{Score}_{\text{candidate}} - \text{Score}_{\text{current}} \ge \text{min\_delta}$$
  In addition, strict evaluation verifies that no individual field regresses vs. baseline.
  Otherwise, it is staged as `"STAGED, NOT PROMOTED"` with a diagnostic boxed report and a human-readable entry in `logs/updates.log`.
- **Rollback:** `app prompts rollback` immediately reverts pointer to prior version.

---

## Channel 4: Dependencies & Security
- **Mechanism:** Monthly CI workflows and local lockfile verification.
- **Gate:** Security bumps must pass the entire test and eval suite before merging.

---

## Channel 5: Schema & Migrations
- **Mechanism:** Forward-only numbered SQL scripts (`app/store/migrations/*.sql`).
- **Safety Pre-Backup:** Automatically creates a timestamped copy of SQLite database in `backups/` before any migration runs.
- **Execution:** Runs 100% offline.
