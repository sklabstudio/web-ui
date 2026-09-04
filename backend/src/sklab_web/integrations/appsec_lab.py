"""AppSec Lab integration — PRIVATE module behind a public-safe adapter.

Never imports private implementation at frontend build time. Backend-only
dynamic discovery: if the private package is installed locally it may be
used; otherwise return mock-safe / unavailable states. All DTOs are
redacted (no cookies, tokens, RPC URLs, raw bodies).
"""
from __future__ import annotations

import importlib.util
import os
from typing import Any


def _mock_enabled() -> bool:
    v = os.environ.get("SKLAB_MOCK_SECURITY", os.environ.get("SKLAB_MOCK_MODE", "")).lower()
    return v in ("1", "true", "yes")


def _private_available() -> tuple[bool, str | None]:
    try:
        spec = importlib.util.find_spec("sklab_appsec_lab")
        if spec is None:
            return False, None
        mod = importlib.import_module("sklab_appsec_lab")
        return True, str(getattr(mod, "__version__", "unknown"))
    except Exception:
        return False, None


def status(mock_mode: bool = False) -> dict[str, Any]:
    if mock_mode or _mock_enabled():
        return {"state": "READY", "version": "mock-0.2.0",
                "detail": "mock AppSec Lab (deterministic fixture)", "mock": True}
    ok, ver = _private_available()
    if ok:
        return {"state": "READY", "version": ver,
                "detail": "detected sklab_appsec_lab", "mock": False}
    return {"state": "NOT_INSTALLED", "version": None,
            "detail": "AppSec Lab not installed (optional private module)", "mock": False}


def capability() -> str:
    return "security.appsec"


def redacted(dto: dict[str, Any]) -> dict[str, Any]:
    """Strip sensitive keys from any AppSec DTO before it leaves the backend."""
    banned_sub = ("cookie", "token", "secret", "authorization", "set-cookie",
                  "rpc_url", "private_key", "password", "api_key", "sessionid")
    out: dict[str, Any] = {}
    for k, v in dto.items():
        lk = k.lower()
        if any(b in lk for b in banned_sub):
            out[k] = "[REDACTED]"
        elif isinstance(v, dict):
            out[k] = redacted(v)
        elif isinstance(v, list):
            out[k] = [redacted(i) if isinstance(i, dict) else i for i in v]
        else:
            out[k] = v
    return out
