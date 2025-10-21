"""Settings loader for AI Republic.

This module loads YAML configuration and environment variables into a
pydantic-based settings object. It is designed to be imported early so other
modules can rely on structured configuration.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List

import yaml
from pydantic import BaseModel, Field

CONFIG_PATH = Path("config/settings.yaml")


class RuntimeSettings(BaseModel):
    offline_mode: bool = Field(default=True)
    enforcement_version: str = Field(default="1.0.0")
    constitution_path: str
    logs_dir: str
    reflections_dir: str
    sandbox_root: str
    proposal_dir: str
    db_path: str
    ledger_path: str
    max_runtime_seconds: int = Field(default=30)
    max_memory_mb: int = Field(default=128)


class NetworkSettings(BaseModel):
    github_api_url: str = Field(default="https://api.github.com")
    default_repo: str = Field(default="")


class SecuritySettings(BaseModel):
    allowed_write_paths: List[str] = Field(default_factory=list)
    disallowed_imports: List[str] = Field(default_factory=list)
    forbidden_calls: List[str] = Field(default_factory=list)


class SimulationSettings(BaseModel):
    starting_credit: int = Field(default=0)
    reward_per_success: int = Field(default=0)


class Settings(BaseModel):
    runtime: RuntimeSettings
    network: NetworkSettings
    security: SecuritySettings
    simulation: SimulationSettings

    @property
    def offline_mode(self) -> bool:
        env_value = os.getenv("OFFLINE_MODE")
        if env_value is None:
            return self.runtime.offline_mode
        return env_value.lower() in {"1", "true", "yes"}

    @property
    def github_token(self) -> str | None:
        token = os.getenv("GITHUB_TOKEN")
        return token or None

    @property
    def github_repository(self) -> str | None:
        repo = os.getenv("GITHUB_REPOSITORY") or self.network.default_repo
        return repo or None


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Settings(**data)


SETTINGS = load_settings()
