"""Protocol Intelligence integration — PRIVATE module behind a public-safe adapter.

Same boundary rules as AppSec Lab: backend-side dynamic discovery only,
generic DTOs, no proprietary logic copied into this repo.
"""
from __future__ import annotations

import importlib.util
import os
from typing import Any


def _mock_enabled() -> bool:
    v = os.environ.get("SKLAB_MOCK_PROTOCOLS", os.environ.get("SKLAB_MOCK_MODE", "")).lower()
    return v in ("1", "true", "yes")


def _private_available() -> tuple[bool, str | None]:
    try:
        spec = importlib.util.find_spec("sklab_protocol_intelligence")
        if spec is None:
            return False, None
        mod = importlib.import_module("sklab_protocol_intelligence")
        return True, str(getattr(mod, "__version__", "unknown"))
    except Exception:
        return False, None


def status(mock_mode: bool = False) -> dict[str, Any]:
    if mock_mode or _mock_enabled():
        return {"state": "READY", "version": "mock-0.2.0",
                "detail": "mock Protocol Intelligence (deterministic fixture)", "mock": True}
    ok, ver = _private_available()
    if ok:
        return {"state": "READY", "version": ver,
                "detail": "detected sklab_protocol_intelligence", "mock": False}
    return {"state": "NOT_INSTALLED", "version": None,
            "detail": "Protocol Intelligence not installed (optional private module)", "mock": False}


def capability() -> str:
    return "protocols.intelligence"
