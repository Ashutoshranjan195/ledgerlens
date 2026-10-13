"""Single source of truth configuration loader for LedgerLens.
Merges app/models.yaml, app/config.yaml, and environment variables.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from pydantic import BaseModel, Field

from app.utils.paths import get_models_config_path, get_user_config_path
from app.utils.crypto import verify_offline_license

class ModelProfile(BaseModel):
    name: str
    min_ram_gb: int
    vision: bool

class ModelsConfig(BaseModel):
    profiles: Dict[str, ModelProfile]
    default_profile: str = "balanced"
    embeddings: str = "nomic-embed-text"
    allow_cloud_fallback: bool = False

class AppConfig(BaseModel):
    name: str = "LedgerLens"
    version: str = "0.1.0"
    profile: str = "balanced"
    currency_default: str = "USD"
    tax_year_default: int = 2026
    confidence_threshold: float = 0.85
    auto_backup_on_launch: bool = True
    export_format: str = "csv"
    free_tier_monthly_limit: int = 30
    strict_offline: bool = True
    allow_cloud_fallback: bool = False
    ollama_host: str = "http://localhost:11434"
    license_key: Optional[str] = None

class ConfigManager:
    """Singleton configuration manager."""
    _instance: Optional[ConfigManager] = None

    def __init__(self) -> None:
        self.models_config = self._load_models_config()
        self.app_config = self._load_app_config()

    @classmethod
    def get_instance(cls) -> ConfigManager:
        if cls._instance is None:
            cls._instance = ConfigManager()
        return cls._instance

    def _load_models_config(self) -> ModelsConfig:
        models_file = get_models_config_path()
        if models_file.exists():
            with open(models_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return ModelsConfig(**data)
        # Default fallback if file missing
        return ModelsConfig(
            profiles={
                "fast": ModelProfile(name="llama3.2:3b", min_ram_gb=8, vision=False),
                "balanced": ModelProfile(name="qwen2.5:7b-vl", min_ram_gb=16, vision=True),
                "best": ModelProfile(name="qwen2.5:32b-vl", min_ram_gb=32, vision=True),
            },
            default_profile="balanced",
            embeddings="nomic-embed-text",
            allow_cloud_fallback=False
        )

    def _load_app_config(self) -> AppConfig:
        config_file = get_user_config_path()
        data: Dict[str, Any] = {}
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
                app_sec = raw.get("app", {})
                priv_sec = raw.get("privacy", {})
                data = {**app_sec, **priv_sec}

        # Override with environment variables
        env_profile = os.environ.get("LEDGERLENS_PROFILE")
        if env_profile:
            data["profile"] = env_profile

        env_offline = os.environ.get("LEDGERLENS_OFFLINE")
        if env_offline is not None:
            data["strict_offline"] = (env_offline == "1" or env_offline.lower() == "true")

        env_host = os.environ.get("OLLAMA_HOST")
        if env_host:
            data["ollama_host"] = env_host

        env_license = os.environ.get("LEDGERLENS_LICENSE_KEY")
        if env_license:
            data["license_key"] = env_license

        return AppConfig(**data)

    def get_active_model_name(self) -> str:
        """Resolve the active model name based on current profile."""
        profile_key = self.app_config.profile
        profile = self.models_config.profiles.get(profile_key)
        if profile:
            return profile.name
        # Fallback to default profile
        default_p = self.models_config.profiles.get(self.models_config.default_profile)
        return default_p.name if default_p else "qwen2.5:7b-vl"

    def get_active_profile(self) -> ModelProfile:
        """Return the active ModelProfile object."""
        profile_key = self.app_config.profile
        if profile_key in self.models_config.profiles:
            return self.models_config.profiles[profile_key]
        return self.models_config.profiles[self.models_config.default_profile]

    def set_profile(self, profile_name: str) -> None:
        """Dynamically update active profile in memory and persist to config.yaml."""
        if profile_name in self.models_config.profiles:
            self.app_config.profile = profile_name
            config_file = get_user_config_path()
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    raw = yaml.safe_load(f) or {}
                if "app" not in raw:
                    raw["app"] = {}
                raw["app"]["profile"] = profile_name
                with open(config_file, "w", encoding="utf-8") as f:
                    yaml.safe_dump(raw, f)

    def is_offline(self) -> bool:
        return self.app_config.strict_offline

    def get_license_status(self) -> dict:
        return verify_offline_license(self.app_config.license_key or "")

def get_config() -> ConfigManager:
    return ConfigManager.get_instance()
