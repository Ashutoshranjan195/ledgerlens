"""Main application entrypoint for LedgerLens.
Launches Streamlit interface on localhost.
"""

from __future__ import annotations
import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.utils.logging import logger
from app.store.db import get_db

def main() -> None:
    # Ensure database schema is migrated before launching UI
    db = get_db()
    db.run_migrations()

    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT) + os.pathsep + env.get("PYTHONPATH", "")

    logger.info("Launching LedgerLens Local UI from %s", PROJECT_ROOT / "app" / "ui" / "app.py")

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(PROJECT_ROOT / "app" / "ui" / "app.py"),
        "--server.headless=true",
        "--theme.base=dark"
    ]
    try:
        subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            env=env,
            check=True
        )
    except KeyboardInterrupt:
        logger.info("LedgerLens stopped by user.")

if __name__ == "__main__":
    main()
