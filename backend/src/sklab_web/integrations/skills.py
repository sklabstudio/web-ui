"""Skill Hub integration — task-scoped skill resolution via ``sklab-skills``.

Boundary rules:
- ``install`` is NEVER global-enable. Enable is explicit per call.
- Never executes skill code. Read-only except enable/disable/auto-set,
  which are operator-scoped registry decisions (never touch source repos).
- All payloads are metadata (trust/permissions/risk/scores), never secrets.
"""

from __future__ import annotations

from typing import Any

from sklab_web.integrations.cli import CliError, cli_available, run_cli_json

AUTO_MODES = ("OFF", "SAFE", "SMART", "FULL")


def available() -> bool:
    return cli_available("sklab-skills")


def live_list(category: str = "", trust: str = "") -> list[dict[str, Any]] | None:
    if not available():
        return None
    args = ["list", "--json"]
    if category:
        args += ["--category", category]
    if trust:
        args += ["--trust", trust]
    try:
        data = run_cli_json("sklab-skills", args, timeout=30.0)
    except CliError:
        return None
    items = data if isinstance(data, list) else data.get("skills", [])
    out: list[dict[str, Any]] = []
    for s in items:
        if not isinstance(s, dict):
            continue
        out.append(_normalize(s))
    return out


def _normalize(s: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(s.get("id", s.get("skill_id", "unknown"))),
        "enabled": bool(s.get("enabled", False)),
        "category": str(s.get("category", "general")),
        "source": str(s.get("source", s.get("type", "builtin"))),
        "trust_level": str(s.get("trust", s.get("trust_level", "unknown"))),
        "permissions": list(s.get("permissions", []) or []),
        "risk": str(s.get("risk", "unknown")),
        "version": str(s.get("version", "")),
        "compatible_agents": list(s.get("compatible_agents", []) or []),
        "description": str(s.get("description", ""))[:500],
        "live": True,
    }


def live_show(skill_id: str) -> dict[str, Any] | None:
    from sklab_web.integrations.cli import require_id

    require_id(skill_id, "skill")
    if not available():
        return None
    try:
        data = run_cli_json("sklab-skills", ["show", skill_id, "--json"], timeout=30.0)
    except CliError:
        return None
    if not isinstance(data, dict):
        return None
    return _normalize(data.get("skill", data))


def live_audit(skill_id: str) -> dict[str, Any] | None:
    from sklab_web.integrations.cli import require_id

    require_id(skill_id, "skill")
    if not available():
        return None
    try:
        data = run_cli_json("sklab-skills", ["audit", skill_id, "--json"], timeout=30.0)
    except CliError:
        return None
    return data if isinstance(data, dict) else None


def live_resolve(task: str, category: str = "", agent: str = "") -> dict[str, Any] | None:
    if not available() or not task.strip():
        return None
    args = ["resolve", "--task", task[:2000], "--json"]
    if category:
        args += ["--category", category]
    if agent:
        args += ["--agent", agent]
    try:
        data = run_cli_json("sklab-skills", args, timeout=30.0)
    except CliError:
        return None
    return data if isinstance(data, dict) else None


def live_enable(skill_id: str, task_scoped: bool = True) -> dict[str, Any] | None:
    """Enable for current task by default (never global unless asked)."""
    from sklab_web.integrations.cli import require_id

    require_id(skill_id, "skill")
    if not available():
        return None
    args = ["enable", skill_id, "--json"]
    if task_scoped:
        args += ["--task", "web-ui-task"]
    try:
        data = run_cli_json("sklab-skills", args, timeout=30.0)
    except CliError:
        return None
    return data if isinstance(data, dict) else {"ok": True, "skill": skill_id}


def live_disable(skill_id: str) -> dict[str, Any] | None:
    from sklab_web.integrations.cli import require_id

    require_id(skill_id, "skill")
    if not available():
        return None
    try:
        data = run_cli_json("sklab-skills", ["disable", skill_id, "--json"], timeout=30.0)
    except CliError:
        return None
    return data if isinstance(data, dict) else {"ok": True, "skill": skill_id}


def live_auto_status() -> dict[str, Any] | None:
    if not available():
        return None
    try:
        data = run_cli_json("sklab-skills", ["auto", "status", "--json"], timeout=30.0)
    except CliError:
        return None
    return data if isinstance(data, dict) else None


def live_auto_set(mode: str) -> dict[str, Any] | None:
    mode = (mode or "").upper()
    if mode not in AUTO_MODES:
        raise CliError("BAD_REQUEST", f"auto mode must be one of {AUTO_MODES}")
    if not available():
        return None
    try:
        data = run_cli_json("sklab-skills", ["auto", "set", mode, "--json"], timeout=30.0)
    except CliError:
        return None
    return data if isinstance(data, dict) else {"ok": True, "mode": mode}
