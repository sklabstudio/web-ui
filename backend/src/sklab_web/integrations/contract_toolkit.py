"""Contract Toolkit integration — PUBLIC module behind a typed adapter.

Contract Toolkit is public and may be installed as an optional dependency.
Degrade gracefully when absent; never fake tool support.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
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


def live_available(mock_mode: bool = False) -> bool:
    """True when the real toolkit is installed and mocks are off."""
    if mock_mode or _mock_enabled():
        return False
    ok, _ = _available()
    return ok


def resolve_project_root(pid: str) -> str | None:
    """Map a project id to a real repo dir under SKLAB_CONTRACTS_ROOT.

    Only explicit operator configuration; never developer-machine defaults,
    so fresh checkouts behave identically. Returns None when unresolvable
    (caller falls back to fixtures).
    """
    import re
    from pathlib import Path

    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-_]{0,63}", pid or ""):
        return None
    root_env = os.environ.get("SKLAB_CONTRACTS_ROOT", "").strip()
    if not root_env:
        return None
    candidate = (Path(root_env).expanduser() / pid).resolve()
    try:
        base = Path(root_env).expanduser().resolve()
    except Exception:
        return None
    if base not in candidate.parents:
        return None
    return str(candidate) if candidate.is_dir() else None


def _toolkit(root: str):  # type: ignore[no-untyped-def]
    from sklab_contract_toolkit.sdk import ContractToolkit

    return ContractToolkit(root=root)


def live_project_ids() -> list[str] | None:
    """Real project ids = subdirectories of SKLAB_CONTRACTS_ROOT.

    None when no root is configured (caller falls back to fixtures).
    """
    root_env = os.environ.get("SKLAB_CONTRACTS_ROOT", "").strip()
    if not root_env:
        return None
    try:
        base = Path(root_env).expanduser().resolve()
    except Exception:
        return None
    if not base.is_dir():
        return []
    return sorted(p.name for p in base.iterdir()
                  if p.is_dir() and not p.name.startswith("."))


def live_projects(pid: str) -> list[dict[str, Any]] | None:
    """Real project detection. None when unresolvable/unavailable."""
    root = resolve_project_root(pid)
    if root is None:
        return None
    try:
        sdk = _toolkit(root)
        detected = sdk.detect_project()
        contracts = sdk.list_contracts()
    except Exception:
        return None
    if not isinstance(detected, dict):
        return None
    return [{
        "id": pid,
        "name": Path(root).name,
        "chain": str(detected.get("chain", "evm")),
        "toolchain": str(detected.get("toolchain", detected.get("kind", "unknown"))),
        "contracts": len(contracts) if isinstance(contracts, list) else 0,
        "status": "READY",
        "live": True,
    }]


def live_inventory(pid: str) -> list[dict[str, Any]] | None:
    """Real contract inventory. None when unresolvable/unavailable."""
    root = resolve_project_root(pid)
    if root is None:
        return None
    try:
        contracts = _toolkit(root).list_contracts()
    except Exception:
        return None
    if not isinstance(contracts, list):
        return None
    out: list[dict[str, Any]] = []
    for i, c in enumerate(contracts):
        if not isinstance(c, dict):
            continue
        funcs = c.get("functions", []) or []
        auths = [a for a in (c.get("authorities", []) or []) if isinstance(a, str)]
        out.append({
            "id": f"c-{i}",
            "name": str(c.get("contract_name", c.get("name", f"contract-{i}"))),
            "source": str(c.get("source_file", "")),
            "kind": "contract",
            "standard": str((c.get("standards", []) or [""])[0] or "custom"),
            "authorities": auths,
            "functions": len(funcs) if isinstance(funcs, list) else 0,
            "live": True,
        })
    return out or None


def live_findings(pid: str) -> list[dict[str, Any]] | None:
    """Real analysis findings (internal rules + Slither when present)."""
    root = resolve_project_root(pid)
    if root is None:
        return None
    try:
        findings = _toolkit(root).run_analysis()
    except Exception:
        return None
    if not isinstance(findings, list):
        return None
    out: list[dict[str, Any]] = []
    for f in findings:
        if not isinstance(f, dict):
            continue
        out.append({
            "id": str(f.get("id", "")),
            "source": str(f.get("tool", "toolkit")),
            "severity": str(f.get("severity", "INFO")),
            "confidence": str(f.get("confidence", "MEDIUM")),
            "title": str(f.get("title", f.get("rule_id", ""))),
            "contract": str(f.get("contract", "")),
            "function": str(f.get("function", "")),
            "status": str(f.get("status", "OPEN")),
            "evidence_ref": str(f.get("fingerprint", f.get("id", ""))),
            "description": str(f.get("description", f.get("evidence", ""))),
            "remediation": str(f.get("recommendation", f.get("remediation", ""))),
            "impact": {},
            "live": True,
        })
    return out


def live_compile(pid: str) -> dict[str, Any] | None:
    root = resolve_project_root(pid)
    if root is None:
        return None
    try:
        res = _toolkit(root).compile_project()
    except Exception:
        return None
    if not isinstance(res, dict):
        return None
    return {"project": pid, "ok": bool(res.get("success", False)),
            "compiler": str(res.get("compiler", "")),
            "warnings": list(res.get("warnings", []) or []),
            "errors": list(res.get("errors", []) or []),
            "build_fingerprint": str(res.get("build_fingerprint", "")),
            "live": True}


def live_tests(pid: str) -> dict[str, Any] | None:
    root = resolve_project_root(pid)
    if root is None:
        return None
    try:
        res = _toolkit(root).run_tests()
    except Exception:
        return None
    if not isinstance(res, dict):
        return None
    return {"project": pid, "total": res.get("total", 0), "passed": res.get("passed", 0),
            "failed": res.get("failed", 0), "skipped": res.get("skipped", 0),
            "duration_seconds": res.get("duration_seconds", 0),
            "tool": str(res.get("tool", "")), "failures": list(res.get("failures", []) or []),
            "note": str(res.get("raw_output", ""))[:300], "live": True}


def live_fuzz(pid: str, runs: int = 256) -> dict[str, Any] | None:
    root = resolve_project_root(pid)
    if root is None:
        return None
    try:
        res = _toolkit(root).run_fuzz(runs=min(max(runs, 1), 10000))
    except Exception:
        return None
    items = res if isinstance(res, list) else []
    failures = sum(1 for r in items if isinstance(r, dict) and r.get("failures"))
    first_ce = next((str(r.get("counterexample", "")) for r in items
                     if isinstance(r, dict) and r.get("counterexample")), "")
    tool = str(items[0].get("tool", "")) if items and isinstance(items[0], dict) else ""
    return {"project": pid, "tool": tool, "runs": runs, "targets": len(items),
            "failures": failures, "counterexample": first_ce, "live": True}


def live_invariants(pid: str) -> dict[str, Any] | None:
    root = resolve_project_root(pid)
    if root is None:
        return None
    try:
        res = _toolkit(root).run_invariants()
    except Exception:
        return None
    items = res if isinstance(res, list) else []
    out = []
    for r in items:
        if not isinstance(r, dict):
            continue
        out.append({"property": str(r.get("property", "")),
                    "status": str(r.get("status", "UNKNOWN")),
                    "runs": r.get("runs", 0),
                    "counterexample": str(r.get("counterexample", "")),
                    "tool": str(r.get("tool", ""))})
    return {"project": pid, "invariants": out, "live": True}


def live_tools(timeout: float = 15.0) -> list[dict[str, Any]] | None:
    """Query the real Contract Toolkit CLI for tool availability.

    Returns normalized tool dicts or None when the CLI is absent/fails,
    so callers can fall back to mock fixtures honestly.
    """
    import json
    import shutil
    import subprocess

    if shutil.which("sklab-contract") is None:
        return None
    try:
        out = subprocess.run(
            ["sklab-contract", "tools", "--json"],
            capture_output=True, text=True, timeout=timeout,
        )
    except Exception:
        return None
    if out.returncode != 0 or not out.stdout.strip():
        return None
    try:
        data = json.loads(out.stdout)
    except Exception:
        return None
    items = data if isinstance(data, list) else data.get("tools", [])
    normalized: list[dict[str, Any]] = []
    for t in items:
        if not isinstance(t, dict):
            continue
        name = str(t.get("tool", t.get("id", "unknown")))
        normalized.append({
            "id": name.lower(),
            "tool": name,
            "installed": bool(t.get("installed", False)),
            "version": t.get("version") or None,
            "status": "READY" if t.get("installed") else "NOT_INSTALLED",
            "capabilities": list(t.get("capabilities", [])),
            "path": t.get("path", ""),
            "notes": t.get("notes", ""),
        })
    return normalized or None
