"""Test rollback functionality across prompt and app update channels."""

import pytest
from app.update.prompts import PromptUpdater
from app.update.app import AppCodeUpdater

def test_prompt_rollback():
    updater = PromptUpdater()
    # Test safe handling when no previous version is present or rolled back
    ok, msg = updater.rollback_prompt("categorize")
    # Should safely return status tuple without crashing
    assert isinstance(ok, bool)
    assert isinstance(msg, str)

def test_app_rollback_safety():
    updater = AppCodeUpdater()
    ok, msg = updater.rollback()
    assert isinstance(ok, bool)
    assert isinstance(msg, str)
