"""Prompts loader for LedgerLens.
Ensures prompts are NEVER hardcoded in code strings.
Always resolves through prompts/registry.yaml to load versioned markdown files.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional
import yaml
from app.utils.paths import get_prompts_dir

class PromptRegistry:
    def __init__(self, prompts_dir: Optional[Path] = None) -> None:
        self.prompts_dir = prompts_dir or get_prompts_dir()
        self.registry_file = self.prompts_dir / "registry.yaml"
        self._registry_cache: Optional[Dict] = None

    def _load_registry(self) -> Dict:
        if not self.registry_file.exists():
            return {}
        with open(self.registry_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def get_prompt_text(self, prompt_name: str, version: Optional[str] = None) -> str:
        """Load the content of a versioned prompt template."""
        registry = self._load_registry()
        if prompt_name not in registry:
            raise KeyError(f"Prompt '{prompt_name}' not found in registry {self.registry_file}")

        entry = registry[prompt_name]
        selected_version = version or entry.get("current", "v1")
        versions_map = entry.get("versions", {})

        if selected_version not in versions_map:
            raise KeyError(f"Version '{selected_version}' not found for prompt '{prompt_name}'")

        file_name = versions_map[selected_version]
        file_path = self.prompts_dir / file_name

        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file {file_path} does not exist on disk")

        return file_path.read_text(encoding="utf-8")

    def format_prompt(self, prompt_name: str, version: Optional[str] = None, **kwargs) -> str:
        """Load and inject parameters into the prompt template."""
        raw_text = self.get_prompt_text(prompt_name, version=version)
        try:
            return raw_text.format(**kwargs)
        except KeyError:
            # If prompt has unescaped curly braces in JSON examples, perform safe replacement
            res = raw_text
            for k, v in kwargs.items():
                res = res.replace("{" + k + "}", str(v))
            return res

_GLOBAL_PROMPT_REGISTRY = PromptRegistry()

def get_prompt(name: str, version: Optional[str] = None, **kwargs) -> str:
    """Convenience helper to retrieve formatted prompt."""
    return _GLOBAL_PROMPT_REGISTRY.format_prompt(name, version=version, **kwargs)
