"""Paths utility for LedgerLens.
Ensures standard XDG-compliant directory paths for data, config, logs, and backups.
Zero hardcoded assumptions, 100% local.
"""

from __future__ import annotations
import os
import sys
from pathlib import Path

APP_NAME = "ledgerlens"

def get_base_dir() -> Path:
    """Return the repository / installed root directory."""
    return Path(__file__).resolve().parent.parent.parent

def get_data_dir() -> Path:
    """Return the user data directory according to XDG or OS conventions."""
    env_override = os.environ.get("LEDGERLENS_DATA_DIR")
    if env_override:
        path = Path(env_override)
    elif sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        path = Path(local_app_data) / APP_NAME
    elif sys.platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / APP_NAME
    else:
        xdg_data_home = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
        path = Path(xdg_data_home) / APP_NAME

    path.mkdir(parents=True, exist_ok=True)
    return path

def get_db_path() -> Path:
    """Return the path to the primary SQLite database."""
    return get_data_dir() / "ledgerlens.db"

def get_logs_dir() -> Path:
    """Return the directory where local logs are stored."""
    env_data = os.environ.get("LEDGERLENS_DATA_DIR")
    if env_data:
        path = Path(env_data) / "logs"
    else:
        path = get_base_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_backups_dir() -> Path:
    """Return the directory where pre-migration DB backups are stored."""
    env_data = os.environ.get("LEDGERLENS_DATA_DIR")
    if env_data:
        path = Path(env_data) / "backups"
    else:
        path = get_base_dir() / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_prompts_dir() -> Path:
    """Return the directory where versioned prompts live."""
    return get_base_dir() / "prompts"

def get_models_config_path() -> Path:
    """Return the path to app/models.yaml."""
    return get_base_dir() / "app" / "models.yaml"

def get_user_config_path() -> Path:
    """Return the path to app/config.yaml or user config."""
    return get_base_dir() / "app" / "config.yaml"
