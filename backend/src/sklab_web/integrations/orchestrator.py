"""Orchestrator integration — the ONLY place that talks to Orchestrator.

Preferred: direct Python import. Fallback: machine-readable CLI JSON.
Never parse Rich/human output. Never duplicate state-machine logic.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any


def orchestrator_available() -> tuple[bool, str | None]:
    try:
        import importlib

        import sklab_orchestrator  # type: ignore  # noqa: F401

        mod = importlib.import_module("sklab_orchestrator")
        return True, getattr(mod, "__version__", "unknown")
    except Exception:
        pass
    if shutil.which("sklab-run"):
        return True, "cli"
    return False, None


def build_plan_via_orchestrator(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Return a plan dict or None if Orchestrator is unavailable (caller falls back to mock)."""
    try:
        from sklab_orchestrator.planning import classify_task  # type: ignore

        cls = classify_task(payload.get("task", ""))
        category = getattr(getattr(cls, "category", None), "value", str(getattr(cls, "category", "UNKNOWN")))
        return {"classification": category}
    except Exception:
        pass
    # CLI fallback: only machine-readable JSON, never Rich text.
    if shutil.which("sklab-run"):
        try:
            p = subprocess.run(["sklab-run", "plan", "--json", payload.get("task", "")],
                               capture_output=True, text=True, timeout=10)
            if p.returncode == 0 and p.stdout.strip().startswith("{"):
                return json.loads(p.stdout)
        except Exception:
            return None
    return None
