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


MODULE_CAPABILITIES = {
    "security.appsec": "appsec_lab",
    "contracts.toolkit": "contract_toolkit",
    "protocols.intelligence": "protocol_intelligence",
}


def module_discovery(mock_mode: bool = False) -> list[dict[str, Any]]:
    """Generic module capability registration (prefers static adapters,
    migrates to SKLab CLI/registry when available)."""
    from sklab_web.integrations import appsec_lab, contract_toolkit, protocol_intelligence

    out = []
    for cap, short in MODULE_CAPABILITIES.items():
        if short == "appsec_lab":
            s = appsec_lab.status(mock_mode)
        elif short == "contract_toolkit":
            s = contract_toolkit.status(mock_mode)
        else:
            s = protocol_intelligence.status(mock_mode)
        out.append({"name": short, "capability": cap, **s})
    return out


def component_state(name: str, mock_mode: bool) -> dict[str, Any]:
    # v0.2 private/public module adapters take precedence for their names.
    if name in ("appsec_lab", "security"):
        from sklab_web.integrations import appsec_lab

        return appsec_lab.status(mock_mode)
    if name in ("contract_toolkit", "contracts"):
        from sklab_web.integrations import contract_toolkit

        return contract_toolkit.status(mock_mode)
    if name in ("protocol_intelligence", "protocols"):
        from sklab_web.integrations import protocol_intelligence

        return protocol_intelligence.status(mock_mode)
    if name == "sklab_cli":
        from sklab_web.integrations.cli import cli_available

        if cli_available("sklab"):
            return {"state": "READY", "version": "cli", "detail": "sklab CLI detected"}
        return {"state": "NOT_INSTALLED", "version": None, "detail": "sklab CLI not installed"}
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
        "agent_adapters": "sklab_agent_adapters",
        "provider_connections": "sklab_provider_connections",
        "repo_context": "repocontext",
        "reprobox": "reprobox",
        "patchbench": "patchbench",
        "benchsuite": "benchsuite",
        "codetrials": "codetrials",
        "promptbench": "promptbench",
    }.get(name, name)
    ok, ver = _mod_available(pkg)
    if ok:
        return {"state": "READY", "version": ver, "detail": f"detected {pkg}"}
    return {"state": "UNAVAILABLE", "version": None, "detail": f"{pkg} not installed"}
