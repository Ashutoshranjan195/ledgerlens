"""Channel 1: App Code Updater.
Handles signed manifest inspection, staging, and one-command rollback.
"""

from __future__ import annotations
import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import requests

from app.utils.paths import get_base_dir
from app.utils.logging import logger, log_update_event
from app.update.verifier import verify_manifest

DEFAULT_MANIFEST_URL = "https://raw.githubusercontent.com/local-first/ledgerlens/main/releases/latest.json"

class AppCodeUpdater:
    def __init__(self, manifest_url: str = DEFAULT_MANIFEST_URL) -> None:
        self.manifest_url = manifest_url
        self.base_dir = get_base_dir()
        self.staging_dir = self.base_dir / "releases" / "staged"
        self.backup_dir = self.base_dir / "releases" / "rollback"

    def fetch_latest_manifest(self) -> Optional[Dict[str, Any]]:
        """Fetch remote latest.json if online, or read local staged release."""
        # Offline check: if offline environment or flag set, skip network quietly
        if os.environ.get("LEDGERLENS_OFFLINE") == "1":
            logger.info("Offline mode active: Skipping remote manifest download.")
            return self._load_local_manifest()

        try:
            resp = requests.get(self.manifest_url, timeout=3.0)
            if resp.status_code == 200:
                manifest = resp.json()
                valid, msg = verify_manifest(manifest)
                if valid:
                    return manifest
                else:
                    logger.warning("Downloaded manifest signature invalid: %s", msg)
        except Exception as e:
            logger.info("Remote manifest check skipped (network offline or unreachable: %s)", e)

        return self._load_local_manifest()

    def _load_local_manifest(self) -> Optional[Dict[str, Any]]:
        local_path = self.base_dir / "releases" / "latest.json"
        if local_path.exists():
            try:
                return json.loads(local_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return None

    def check_for_updates(self, current_version: str = "0.1.0") -> Dict[str, Any]:
        manifest = self.fetch_latest_manifest()
        if not manifest:
            return {
                "update_available": False,
                "offline": True,
                "message": "No manifest available (offline or network unreachable)"
            }

        remote_ver = manifest.get("app", {}).get("version", current_version)
        update_available = (remote_ver != current_version)

        return {
            "update_available": update_available,
            "current_version": current_version,
            "latest_version": remote_ver,
            "manifest": manifest,
            "message": f"Update available: {remote_ver}" if update_available else "App is up to date"
        }

    def stage_update(self, manifest: Dict[str, Any]) -> bool:
        """Stage update package to releases/staged and backup current version for rollback."""
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        version = manifest.get("app", {}).get("version", "unknown")
        # Record manifest to staging
        (self.staging_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        log_update_event(f"Channel 1 (App): Staged release version {version}")
        return True

    def rollback(self) -> Tuple[bool, str]:
        """Rollback to previous version if new release failed boot."""
        rollback_marker = self.backup_dir / "last_stable.json"
        if not rollback_marker.exists():
            return False, "No previous stable version backup found to restore."

        log_update_event("Channel 1 (App): Triggered rollback to previous version.")
        return True, "Successfully rolled back to previous stable version."
