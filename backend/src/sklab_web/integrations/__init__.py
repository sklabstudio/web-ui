"""Isolated integration shims. Each detects availability, degrades gracefully,
never duplicates business logic. Real Orchestrator wiring lives in orchestrator.py."""
from __future__ import annotations

import importlib.util
from typing import Any


def _mod_available(name: str) -> tuple[bool, str | None]:
    try:
        spec = importlib.util.find_spec(name)
        if spec is None:
            return False, None
        mod = importlib.import_module(name)
        ver = getattr(mod, "__version__", None)
        return True, str(ver) if ver else "unknown"
    except Exception:
        return False, None


def component_state(name: str, mock_mode: bool) -> dict[str, Any]:
    if mock_mode:
        mapping = {
            "orchestrator": ("DEGRADED", "mock-0.1.0", "mock mode: deterministic simulator"),
            "agent_adapters": ("READY", "mock", "mock agent catalog"),
            "provider_connections": ("READY", "mock", "mock provider catalog"),
            "repo_context": ("READY", "mock", "mock context"),
            "reprobox": ("READY", "mock", "mock env"),
            "patchbench": ("READY", "mock", "mock verifier"),
            "benchsuite": ("READY", "mock", "mock catalog"),
            "codetrials": ("READY", "mock", "mock history"),
            "promptbench": ("READY", "mock", "mock history"),
        }
        s, v, d = mapping.get(name, ("UNKNOWN", None, ""))
        return {"state": s, "version": v, "detail": d}
    pkg = {
        "orchestrator": "sklab_orchestrator",
        "agent_adapters": "sklab_agents",
        "provider_connections": "sklab_connections",
        "repo_context": "sklab_repo_context",
        "reprobox": "sklab_reprobox",
        "patchbench": "sklab_patchbench",
        "benchsuite": "sklab_benchsuite",
        "codetrials": "sklab_codetrials",
        "promptbench": "sklab_promptbench",
    }.get(name, name)
    ok, ver = _mod_available(pkg)
    if ok:
        return {"state": "READY", "version": ver, "detail": f"detected {pkg}"}
    return {"state": "UNAVAILABLE", "version": None, "detail": f"{pkg} not installed"}
