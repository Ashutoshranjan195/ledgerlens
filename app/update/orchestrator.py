"""Auto-Update Orchestrator for LedgerLens.

COORDINATES ALL 5 CHANNELS:
1. App Code (Signed manifest, delta check, safe rollback)
2. Models (Ollama pull by digest + smoke test)
3. Prompts (Eval-gated promotion vs. golden set)
4. Dependencies (Security audit)
5. Schema (Forward-only migrations + pre-backup)

OFFLINE UX RULES:
- Offline = ZERO ERRORS.
- Every update writes a human-readable entry to logs/updates.log.
- Single command: 'app update --all'
"""

from __future__ import annotations
import os
from typing import Any, Dict, Optional

from app.utils.logging import logger, log_update_event
from app.update.app import AppCodeUpdater
from app.update.models import ModelUpdater
from app.update.prompts import PromptUpdater
from app.update.deps import DependencyUpdater
from app.update.schema import SchemaUpdater

class UpdateOrchestrator:
    def __init__(self) -> None:
        self.app_updater = AppCodeUpdater()
        self.model_updater = ModelUpdater()
        self.prompt_updater = PromptUpdater()
        self.deps_updater = DependencyUpdater()
        self.schema_updater = SchemaUpdater()

    def update_all(self) -> Dict[str, Any]:
        """Execute unified update cycle across all 5 channels."""
        is_offline = os.environ.get("LEDGERLENS_OFFLINE") == "1"
        log_update_event(f"--- Initiating 'update --all' (Offline mode: {is_offline}) ---")
        print("\n" + "="*60)
        print(" LedgerLens Unified Update Subsystem ('update --all')")
        print("="*60)

        results: Dict[str, Any] = {}

        # Channel 5: Schema Migrations (Always runs first and safely offline)
        print("\n[Channel 5/5] Checking database schema & migrations...")
        schema_res = self.schema_updater.run_migrations()
        results["channel_5_schema"] = schema_res
        print(f"  → {schema_res['message']}")

        # Channel 4: Dependency Security Check
        print("\n[Channel 4/5] Checking dependencies & lockfile...")
        deps_res = self.deps_updater.check_security_advisories()
        results["channel_4_deps"] = deps_res
        print(f"  → {deps_res.get('message', 'Checked')}")

        # Channel 1: App Code Updates
        print("\n[Channel 1/5] Checking for app updates...")
        app_res = self.app_updater.check_for_updates()
        results["channel_1_app"] = app_res
        if app_res.get("update_available"):
            print(f"  → New version available: {app_res['latest_version']}. Staging...")
            self.app_updater.stage_update(app_res["manifest"])
        else:
            print(f"  → {app_res['message']}")

        # Channel 2: Model Weights
        print("\n[Channel 2/5] Checking model digests & smoke tests...")
        model_res = self.model_updater.update_models()
        results["channel_2_models"] = model_res
        if model_res["status"] == "skipped":
            print("  → Offline mode: Retaining verified local model weights.")
        else:
            print(f"  → Models verified: {model_res.get('updated', ['All active models verified'])}")

        # Channel 3: Prompts with Eval Gate
        print("\n[Channel 3/5] Evaluating prompts against golden baseline...")
        # Verify candidate v2 if present
        prompts_res = self.prompt_updater.evaluate_and_promote(
            prompt_name="extract_fields",
            candidate_version="v2"
        )
        results["channel_3_prompts"] = prompts_res
        if not prompts_res.get("promoted", False):
            print("\n  +------------------------------------------------------------------------+")
            print("  | [CHANNEL 3 EVAL GATE] PROMPT CANDIDATE STAGED, NOT PROMOTED            |")
            print(f"  | Candidate: {prompts_res.get('prompt', 'extract_fields')} v2                                           |")
            delta_val = prompts_res.get('delta', 0.0)
            print(f"  | Delta vs Baseline: {delta_val*100:+.2f}pp (Required Margin: >= +1.00pp)               |")
            print("  | Action: Baseline retained (v1). Zero regression risk.                  |")
            print("  +------------------------------------------------------------------------+")
        else:
            print(f"  -> {prompts_res['message']}")

        print("\n" + "="*60)
        print(" Update Cycle Complete. All entries recorded in logs/updates.log")
        print("="*60 + "\n")
        log_update_event("--- Update cycle completed successfully ---")

        return results

_GLOBAL_ORCHESTRATOR: Optional[UpdateOrchestrator] = None

def get_orchestrator() -> UpdateOrchestrator:
    global _GLOBAL_ORCHESTRATOR
    if _GLOBAL_ORCHESTRATOR is None:
        _GLOBAL_ORCHESTRATOR = UpdateOrchestrator()
    return _GLOBAL_ORCHESTRATOR
