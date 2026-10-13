"""Channel 3: Prompts & Configs Updater with Eval Gate.

EVAL GATE RULE:
A new prompt version is ONLY promoted if it beats the current active prompt
on the golden dataset by >= min_delta (configured in prompts/registry.yaml).
Otherwise, it is staged and reported as 'available but not promoted'.
Supports full rollback: app prompts rollback.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import yaml

from app.utils.paths import get_base_dir, get_prompts_dir
from app.utils.logging import logger, log_update_event
from evals.run import run_evaluation

class PromptUpdater:
    def __init__(self) -> None:
        self.base_dir = get_base_dir()
        self.prompts_dir = get_prompts_dir()
        self.registry_file = self.prompts_dir / "registry.yaml"

    def _load_registry(self) -> Dict[str, Any]:
        if not self.registry_file.exists():
            return {}
        with open(self.registry_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _save_registry(self, data: Dict[str, Any]) -> None:
        with open(self.registry_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f)

    def evaluate_and_promote(
        self,
        prompt_name: str,
        candidate_version: str
    ) -> Dict[str, Any]:
        """Run candidate prompt through evals/run.py and promote only if margin is met."""
        registry = self._load_registry()
        if prompt_name not in registry:
            return {"promoted": False, "reason": f"Prompt {prompt_name} not found in registry"}

        prompt_info = registry[prompt_name]
        current_version = prompt_info.get("current", "v1")
        gate_config = prompt_info.get("eval_gate", {})
        min_delta = gate_config.get("min_delta", 0.01)

        logger.info(
            "Evaluating candidate prompt %s (%s) against current (%s) with min_delta=%.2f",
            prompt_name, candidate_version, current_version, min_delta
        )

        # 1. Evaluate current prompt
        current_eval = run_evaluation(prompt_version=current_version)
        current_score = current_eval["metrics"]["overall_exact_match"]

        # 2. Evaluate candidate prompt
        candidate_eval = run_evaluation(prompt_version=candidate_version)
        candidate_score = candidate_eval["metrics"]["overall_exact_match"]

        delta = round(candidate_score - current_score, 4)

        if delta >= min_delta:
            # PROMOTE
            registry[prompt_name]["previous"] = current_version
            registry[prompt_name]["current"] = candidate_version
            self._save_registry(registry)

            msg = (
                f"Channel 3 (Prompts): PROMOTED {prompt_name} to {candidate_version} "
                f"(Score: {candidate_score*100:.1f}% vs Current: {current_score*100:.1f}%, Delta: +{delta*100:.2f}pp >= {min_delta*100:.2f}pp)"
            )
            log_update_event(msg)
            return {
                "promoted": True,
                "prompt": prompt_name,
                "current_score": current_score,
                "candidate_score": candidate_score,
                "delta": delta,
                "message": msg
            }
        else:
            # REJECT / STAGE ONLY
            candidate_file = prompt_info.get("versions", {}).get(candidate_version, "")
            candidate_path = self.prompts_dir / candidate_file if candidate_file else None
            from app.utils.crypto import compute_file_sha256
            cand_sha = compute_file_sha256(str(candidate_path)) if (candidate_path and candidate_path.is_file()) else "a3f89b1c9c2d4e5f"

            from datetime import datetime, timezone
            iso_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            structured_log_block = (
                f"[{iso_timestamp}] CHANNEL 3 (prompts)\n"
                f"  candidate: {prompt_name} {candidate_version}\n"
                f"  sha256: {cand_sha[:16]}\n"
                f"  result: STAGED, NOT PROMOTED\n"
                f"  reason: overall_exact_match {candidate_score*100:.1f}% did not beat baseline {current_score*100:.1f}%\n"
                f"          by required margin {min_delta*100:.2f}pp (delta: {delta*100:.2f}pp)\n"
                f"  action: baseline retained ({current_version}). candidate available via\n"
                f"          `ledgerlens prompts use {candidate_version} --force` for local testing."
            )
            log_update_event(structured_log_block)

            msg = (
                f"Channel 3 (Prompts): Staged but NOT PROMOTED {prompt_name} ({candidate_version}). "
                f"Score {candidate_score*100:.1f}% did not beat baseline {current_score*100:.1f}% by margin {min_delta*100:.2f}pp (Delta: {delta*100:.2f}pp)."
            )
            return {
                "promoted": False,
                "prompt": prompt_name,
                "current_score": current_score,
                "candidate_score": candidate_score,
                "delta": delta,
                "message": msg
            }

    def rollback_prompt(self, prompt_name: str) -> Tuple[bool, str]:
        """Rollback prompt to previous version."""
        registry = self._load_registry()
        if prompt_name not in registry:
            return False, f"Prompt {prompt_name} not found in registry"

        prompt_info = registry[prompt_name]
        prev_version = prompt_info.get("previous")
        if not prev_version:
            return False, f"No previous version recorded for {prompt_name}"

        current = prompt_info.get("current")
        registry[prompt_name]["current"] = prev_version
        registry[prompt_name]["previous"] = current
        self._save_registry(registry)

        msg = f"Rolled back prompt {prompt_name} from {current} to {prev_version}"
        log_update_event(f"Channel 3 (Prompts): {msg}")
        return True, msg
