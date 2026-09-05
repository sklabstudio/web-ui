"""Full SKLab module matrix via ``sklab status --json`` + zero-cost doctor.

Public-safe: only id/name/version/status/detail/origin/visibility cross
the boundary. Never module internals, never secrets.
"""

from __future__ import annotations

from typing import Any

from sklab_web.integrations.cli import CliError, cli_available, run_cli_json

_VALID_STATES = {"READY", "DEGRADED", "FAILED", "NOT_INSTALLED", "UNAVAILABLE", "UNKNOWN"}


def _norm_state(raw: Any) -> str:
    s = str(raw or "UNKNOWN").upper()
    return s if s in _VALID_STATES else "UNKNOWN"


def full_matrix() -> list[dict[str, Any]] | None:
    """All modules from the SKLab CLI registry. None when CLI is absent."""
    if not cli_available("sklab"):
        return None
    try:
        data = run_cli_json("sklab", ["status", "--json"], timeout=30.0)
    except CliError:
        return None
    items = data if isinstance(data, list) else data.get("modules", [])
    out: list[dict[str, Any]] = []
    for m in items:
        if not isinstance(m, dict):
            continue
        out.append(
            {
                "id": str(m.get("id", "unknown")),
                "name": str(m.get("name", m.get("id", "unknown"))),
                "capability": str(m.get("capability", m.get("id", ""))),
                "version": m.get("version"),
                "state": _norm_state(m.get("status")),
                "detail": str(m.get("detail", ""))[:500],
                "origin": str(m.get("origin", "builtin")),
                "visibility": str(m.get("visibility", "public")),
            }
        )
    return out or None


def run_doctor() -> dict[str, Any] | None:
    """Zero-cost orchestrator integration checks. None when unavailable."""
    if not cli_available("sklab-run"):
        return None
    try:
        data = run_cli_json("sklab-run", ["doctor", "--json"], timeout=60.0)
    except CliError:
        return None
    if not isinstance(data, dict):
        return None
    return data
