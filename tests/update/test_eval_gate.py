"""Test eval gate promotion logic:
Ensures a prompt that scores worse is not promoted.
"""

from unittest.mock import patch
import pytest
from app.update.prompts import PromptUpdater

def test_eval_gate_rejects_inferior_candidate():
    updater = PromptUpdater()

    # Mock eval runner: current scores 0.95, candidate scores 0.80 (inferior)
    def mock_eval(prompt_version=None, **kwargs):
        if prompt_version == "v1":
            return {"metrics": {"overall_exact_match": 0.90}}
        elif prompt_version == "candidate_inferior":
            return {"metrics": {"overall_exact_match": 0.80}}
        return {"metrics": {"overall_exact_match": 0.92}}

    with patch("app.update.prompts.run_evaluation", side_effect=mock_eval):
        res = updater.evaluate_and_promote("extract_fields", "candidate_inferior")
        assert res["promoted"] is False
        assert "NOT PROMOTED" in res["message"]
