"""Logging utility for LedgerLens.

STRICT PRIVACY GUARANTEE:
- All logs write to local disk ONLY.
- Absolutely NO telemetry, analytics SDKs, Sentry, or cloud error reporting.
- User data and extraction content can be sanitized or kept local.
"""

from __future__ import annotations
import logging
import sys
from datetime import datetime
from pathlib import Path
from app.utils.paths import get_logs_dir

_LOGGER_INITIALIZED = False

def setup_logger(name: str = "ledgerlens") -> logging.Logger:
    """Configure and return a local-only file and console logger."""
    global _LOGGER_INITIALIZED
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        logs_dir = get_logs_dir()
        log_file = logs_dir / "ledgerlens.log"

        file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

def log_update_event(message: str) -> None:
    """Record an entry specifically into logs/updates.log for auditability."""
    logs_dir = get_logs_dir()
    update_log = logs_dir / "updates.log"
    with open(update_log, "a", encoding="utf-8") as f:
        if message.startswith("["):
            f.write(f"{message}\n")
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")

logger = setup_logger()
