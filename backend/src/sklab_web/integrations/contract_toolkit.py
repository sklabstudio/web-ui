"""Contract Toolkit integration — PUBLIC module behind a typed adapter.

Contract Toolkit is public and may be installed as an optional dependency.
Degrade gracefully when absent; never fake tool support.
"""
from __future__ import annotations

import importlib.util
import os
from typing import Any


def _mock_enabled() -> bool:
    v = os.environ.get("SKLAB_MOCK_CONTRACTS", os.environ.get("SKLAB_MOCK_MODE", "")).lower()
    return v in ("1", "true", "yes")


def _available() -> tuple[bool, str | None]:
    try:
        spec = importlib.util.find_spec("sklab_contract_toolkit")
        if spec is None:
            return False, None
        mod = importlib.import_module("sklab_contract_toolkit")
        return True, str(getattr(mod, "__version__", "unknown"))
    except Exception:
        return False, None


def status(mock_mode: bool = False) -> dict[str, Any]:
    if mock_mode or _mock_enabled():
        return {"state": "READY", "version": "mock-0.2.0",
                "detail": "mock Contract Toolkit (deterministic fixture)", "mock": True}
    ok, ver = _available()
    if ok:
        return {"state": "READY", "version": ver,
                "detail": "detected sklab_contract_toolkit", "mock": False}
    return {"state": "NOT_INSTALLED", "version": None,
            "detail": "Contract Toolkit not installed (optional)", "mock": False}


def capability() -> str:
    return "contracts.toolkit"
