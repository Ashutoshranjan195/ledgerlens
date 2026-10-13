"""Channel 5: Schema and Migrations Updater.
Runs forward-only idempotent SQL migrations with automatic pre-migration SQLite backup.
Runs 100% offline.
"""

from __future__ import annotations
from typing import Any, Dict
from app.store.db import get_db
from app.utils.logging import log_update_event

class SchemaUpdater:
    def __init__(self) -> None:
        self.db = get_db()

    def run_migrations(self) -> Dict[str, Any]:
        """Apply all pending migrations with pre-migration backup."""
        applied_count = self.db.run_migrations()
        msg = f"Channel 5 (Schema): Applied {applied_count} forward migrations."
        log_update_event(msg)
        return {
            "status": "ok",
            "applied_count": applied_count,
            "message": msg
        }
