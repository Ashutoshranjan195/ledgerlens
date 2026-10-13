"""Unit test verifying architectural layering and offline guarantees in LedgerLens.

STRICT ENFORCEMENT RULES:
1. app/core/** may NOT import from app/ui/** or app/update/**.
2. app/update/** may import evals/run.py (eval gate).
3. Nothing under app/** may import requests, httpx, or openai OUTSIDE of app/update/**.
"""

import ast
from pathlib import Path
import pytest

APP_DIR = Path(__file__).resolve().parent.parent.parent / "app"

def get_python_files(directory: Path):
    return list(directory.rglob("*.py"))

def get_imported_modules(file_path: Path):
    content = file_path.read_text(encoding="utf-8")
    tree = ast.parse(content, filename=str(file_path))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    return imports

def test_app_core_layering():
    """Verify app/core/** never imports app/ui or app/update."""
    core_dir = APP_DIR / "core"
    for py_file in get_python_files(core_dir):
        imports = get_imported_modules(py_file)
        for mod in imports:
            assert not mod.startswith("app.ui"), f"Layering violation in {py_file.name}: imports {mod}"
            assert not mod.startswith("app.update"), f"Layering violation in {py_file.name}: imports {mod}"

def test_offline_import_isolation():
    """Verify nothing under app/** imports requests, httpx, or openai outside of app/update/**."""
    banned_network_modules = {"requests", "httpx", "openai"}
    for py_file in get_python_files(APP_DIR):
        rel_path = py_file.relative_to(APP_DIR)
        # app/update/** is allowed to import network clients for update manifests
        if str(rel_path).startswith("update"):
            continue

        imports = get_imported_modules(py_file)
        for banned in banned_network_modules:
            for imp in imports:
                assert not (imp == banned or imp.startswith(f"{banned}.")), (
                    f"Offline guarantee violation in {rel_path}: imports banned network module '{imp}'"
                )
