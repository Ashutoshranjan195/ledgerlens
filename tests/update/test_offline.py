"""Test offline guarantee for update subsystem:
Offline = exit 0, no unhandled exceptions.
"""

import os
from unittest.mock import patch
import pytest
from app.update.orchestrator import get_orchestrator

def test_update_all_offline():
    with patch.dict(os.environ, {"LEDGERLENS_OFFLINE": "1"}):
        orchestrator = get_orchestrator()
        # update_all should execute and not raise network exceptions
        results = orchestrator.update_all()
        assert results is not None
        assert "channel_5_schema" in results
        assert results["channel_5_schema"]["status"] == "ok"
        assert results["channel_2_models"]["status"] == "skipped"
