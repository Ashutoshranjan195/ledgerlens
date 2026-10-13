"""Database backup utility for LedgerLens.
Ensures automatic, pre-migration backups are stored in the local backups/ directory.
"""

from __future__ import annotations
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.utils.paths import get_db_path, get_backups_dir
from app.utils.logging import logger

def backup_database(label: str = "auto") -> Optional[Path]:
    """Create a point-in-time timestamped copy of the SQLite database."""
    db_path = get_db_path()
    if not db_path.exists():
        logger.info("No existing database to backup at %s", db_path)
        return None

    backups_dir = get_backups_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backups_dir / f"ledgerlens_backup_{label}_{timestamp}.db"

    try:
        shutil.copy2(db_path, backup_file)
        logger.info("Created database backup: %s", backup_file)
        return backup_file
    except Exception as e:
        logger.error("Failed to backup database: %s", e)
        raise RuntimeError(f"Database backup failed: {e}") from e

def restore_database(backup_path: Path) -> bool:
    """Restore database from a specified backup file."""
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    db_path = get_db_path()
    try:
        # Create safety copy of current DB if exists
        if db_path.exists():
            safety = db_path.with_suffix(".pre_restore")
            shutil.copy2(db_path, safety)

        shutil.copy2(backup_path, db_path)
        logger.info("Successfully restored database from %s", backup_path)
        return True
    except Exception as e:
        logger.error("Failed to restore database from backup: %s", e)
        return False
