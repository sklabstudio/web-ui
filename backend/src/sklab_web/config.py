"""Backend configuration: env + YAML, auth modes, repo roots, safety defaults."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

AuthMode = Literal["disabled", "token", "password"]


class ServerConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8787


class RepositoriesConfig(BaseModel):
    allowed_roots: list[str] = Field(default_factory=list)


class AuthConfig(BaseModel):
    mode: AuthMode = "disabled"
    token: str = ""
    password_hash: str = ""
    session_expiry_seconds: int = 12 * 3600


class IntegrationsConfig(BaseModel):
    orchestrator: str = "auto"
    agent_adapters: str = "auto"
    provider_connections: str = "auto"
    reprobox: str = "auto"
    patchbench: str = "auto"
    benchsuite: str = "auto"
    codetrials: str = "auto"
    promptbench: str = "auto"
    repo_context: str = "auto"


class UIConfig(BaseModel):
    title: str = "SKLab Studio"


class AppConfig(BaseModel):
    schema_version: int = 1
    server: ServerConfig = ServerConfig()
    repositories: RepositoriesConfig = RepositoriesConfig()
    auth: AuthConfig = AuthConfig()
    integrations: IntegrationsConfig = IntegrationsConfig()
    ui: UIConfig = UIConfig()
    mock_mode: bool = False


def _default_allowed_roots() -> list[str]:
    # Sensible VPS defaults; overridden by env/YAML.
    return ["/srv/sklab/repos", "/home/sklab/projects"]


def load_config(config_path: str | None = None) -> AppConfig:
    path = config_path or os.environ.get("SKLAB_CONFIG", "")
    cfg = AppConfig()
    if path and Path(path).exists():
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        cfg = AppConfig.model_validate(_merge_defaults(data))
    # Env overrides (highest precedence)
    if os.environ.get("SKLAB_MOCK_MODE", "").lower() in ("1", "true", "yes"):
        cfg.mock_mode = True
    auth_mode = os.environ.get("AUTH_MODE", "")
    if auth_mode in ("disabled", "token", "password"):
        cfg.auth.mode = auth_mode  # type: ignore[assignment]
    if os.environ.get("SKLAB_AUTH_TOKEN"):
        cfg.auth.token = os.environ["SKLAB_AUTH_TOKEN"]
    if os.environ.get("SKLAB_AUTH_PASSWORD_HASH"):
        cfg.auth.password_hash = os.environ["SKLAB_AUTH_PASSWORD_HASH"]
    roots = os.environ.get("SKLAB_ALLOWED_ROOTS", "")
    if roots:
        cfg.repositories.allowed_roots = [r.strip() for r in roots.split(",") if r.strip()]
    if not cfg.repositories.allowed_roots:
        cfg.repositories.allowed_roots = _default_allowed_roots()
    return cfg


def _merge_defaults(data: dict) -> dict:
    return data
