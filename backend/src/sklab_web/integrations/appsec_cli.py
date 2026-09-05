"""AppSec Lab write-ops via the private ``sklab-appsec`` CLI (``--json`` only).

Safety: only observational/bounded commands are exposed. The CLI's own
policy object blocks destructive actions; this adapter never adds flags
that weaken policy, never passes credentials, and redacts DTOs.
"""

from __future__ import annotations

from typing import Any

from sklab_web.integrations.appsec_lab import redacted
from sklab_web.integrations.cli import (
    CliError,
    cli_available,
    require_id,
    run_cli_json,
)

CLI = "sklab-appsec"
AUDIT_TIMEOUT = 600.0


def cli_present() -> bool:
    return cli_available(CLI)


def _json(args: list[str], timeout: float = 120.0, engagement: str = "") -> Any:
    if engagement:
        require_id(engagement, "engagement")
    try:
        return run_cli_json(CLI, [*args, "--json"], timeout=timeout)
    except CliError as exc:
        raise _map(exc)


def _map(exc: CliError) -> CliError:
    msg = exc.message.lower()
    if "no such engagement" in msg or "not found" in msg or "unknown engagement" in msg:
        return CliError("ENGAGEMENT_NOT_FOUND", exc.message[:500])
    if "browser" in msg and ("unavailable" in msg or "not installed" in msg or "missing" in msg):
        return CliError("BROWSER_UNAVAILABLE", exc.message[:500])
    return exc


# ---------------- engagements ----------------


def engagement_create(eng_id: str, name: str = "", domain: str = "") -> dict[str, Any]:
    require_id(eng_id, "engagement")
    args = ["engagement", "create", "--id", eng_id]
    if name.strip():
        args += ["--name", name.strip()[:120]]
    if domain.strip():
        args += ["--domain", domain.strip()[:253]]
    data = _json(args)
    return redacted(data if isinstance(data, dict) else {"id": eng_id})


def engagement_list() -> list[dict[str, Any]] | None:
    if not cli_present():
        return None
    try:
        data = run_cli_json(CLI, ["engagement", "list", "--json"], timeout=30.0)
    except CliError:
        return None
    ids: list[str] = []
    active = ""
    if isinstance(data, dict):
        ids = [str(x) for x in (data.get("engagements", []) or []) if isinstance(x, (str, int))]
        active = str(data.get("active", "") or "")
    out = []
    for eid in ids:
        detail = engagement_show(eid) or {}
        eng = detail.get("engagement", {}) if isinstance(detail, dict) else {}
        scope = detail.get("scope", {}) if isinstance(detail, dict) else {}
        domains = scope.get("domains", []) if isinstance(scope, dict) else []
        out.append(
            {
                "id": eid,
                "name": str(eng.get("name", eid)) if isinstance(eng, dict) else eid,
                "status": str(eng.get("status", "ACTIVE")).upper()
                if isinstance(eng, dict)
                else "ACTIVE",
                "scope_summary": ", ".join(domains) if domains else "scope not configured",
                "created_at": str(eng.get("created_at", "")) if isinstance(eng, dict) else "",
                "last_run": str(eng.get("updated_at", "")) if isinstance(eng, dict) else "",
                "finding_count": 0,
                "report_status": "READY",
                "active": eid == active,
                "live": True,
            }
        )
    return out or []


def engagement_show(eng_id: str) -> dict[str, Any] | None:
    if not cli_present():
        return None
    try:
        data = run_cli_json(CLI, ["engagement", "show", eng_id, "--json"], timeout=30.0)
    except CliError:
        return None
    return redacted(data) if isinstance(data, dict) else None


def engagement_activate(eng_id: str) -> dict[str, Any]:
    return _json(["engagement", "activate", eng_id]) or {"ok": True}


def engagement_close(eng_id: str) -> dict[str, Any]:
    return _json(["engagement", "close", eng_id]) or {"ok": True}


# ---------------- browser / capture / analysis ----------------


def browser_status() -> dict[str, Any] | None:
    if not cli_present():
        return None
    try:
        data = run_cli_json(CLI, ["browser", "doctor", "--json"], timeout=60.0)
    except CliError:
        return None
    return data if isinstance(data, dict) else None


def browser_launch(eng_id: str, headed: bool = False) -> dict[str, Any]:
    require_id(eng_id, "engagement")
    args = ["browser", "launch", "--engagement", eng_id]
    args += ["--headed" if headed else "--headless"]
    return _json(args, timeout=180.0) or {"ok": True}


def capture(eng_id: str, scenario: str = "normal-api") -> dict[str, Any]:
    require_id(eng_id, "engagement")
    scenario = scenario.strip() or "normal-api"
    return _json(["capture", eng_id, "--scenario", scenario[:64]], timeout=300.0) or {}


def api_map(eng_id: str) -> list[dict[str, Any]] | None:
    if not cli_present():
        return None
    try:
        data = run_cli_json(CLI, ["api-map", eng_id, "--json"], timeout=120.0)
    except CliError:
        return None
    items = (
        data
        if isinstance(data, list)
        else (data.get("endpoints", []) if isinstance(data, dict) else [])
    )
    out: list[dict[str, Any]] = []
    for ep in items or []:
        if not isinstance(ep, dict):
            continue
        out.append(
            {
                "host": str(ep.get("host", "")),
                "route": str(ep.get("route_pattern", ep.get("route", ""))),
                "method": str(ep.get("method", "")),
                "auth": "required" if ep.get("auth_required") else "none",
                "roles": dict(ep.get("status_behavior", {}) or {}),
                "live": True,
            }
        )
    return out


def audit(eng_id: str) -> dict[str, Any]:
    """Bounded browser observation + analysis. Read-only; may take minutes."""
    require_id(eng_id, "engagement")
    data = _json(["audit", eng_id], timeout=AUDIT_TIMEOUT)
    return redacted(data) if isinstance(data, dict) else {}


def simulate(eng_id: str, check: str = "") -> dict[str, Any]:
    require_id(eng_id, "engagement")
    args = ["simulate", eng_id]
    if check.strip():
        args += ["--check", check.strip()[:64]]
    data = _json(args, timeout=300.0)
    return data if isinstance(data, dict) else {}


def retest(ref: str, eng_id: str = "") -> dict[str, Any]:
    ref = ref.strip()[:128]
    if not ref:
        raise CliError("BAD_REQUEST", "retest ref is required")
    args = ["retest", ref]
    if eng_id.strip():
        require_id(eng_id.strip(), "engagement")
        args += ["--engagement", eng_id.strip()]
    return _json(args, timeout=300.0) or {}


def findings(eng_id: str = "") -> list[dict[str, Any]] | None:
    if not cli_present():
        return None
    args = ["findings"]
    if eng_id.strip():
        require_id(eng_id.strip(), "engagement")
        args += ["--engagement", eng_id.strip()]
    try:
        data = run_cli_json(CLI, [*args, "--json"], timeout=120.0)
    except CliError:
        return None
    items = (data.get("findings", []) if isinstance(data, dict) else data) or []
    out: list[dict[str, Any]] = []
    for f in items:
        if not isinstance(f, dict):
            continue
        method = str(f.get("http_method", ""))
        endpoint = str(f.get("endpoint", ""))
        out.append(
            {
                "id": str(f.get("id", "")),
                "source": "appsec",
                "severity": str(f.get("severity", "MEDIUM")),
                "confidence": str(f.get("confidence", "NEEDS_REVIEW")),
                "title": str(f.get("title", "")),
                "endpoint": f"{method} {endpoint}".strip() or endpoint,
                "flow": str(f.get("browser_flow", "")),
                "status": str(f.get("status", "OPEN")),
                "evidence_ref": str((f.get("evidence", {}) or {}).get("id", f.get("id", ""))),
                "retest_status": str(f.get("retest_status", "NOT_RETESTED")),
                "description": str(f.get("description", "")),
                "remediation": str(f.get("remediation", "")),
                "impact": {k: str(v) for k, v in (f.get("impact", {}) or {}).items()},
                "engagement_id": str(f.get("engagement_id", eng_id)),
                "live": True,
            }
        )
    return out


def impact(finding_id: str) -> dict[str, Any] | None:
    finding_id = finding_id.strip()[:128]
    if not finding_id or not cli_present():
        return None
    try:
        data = run_cli_json(CLI, ["impact", finding_id, "--json"], timeout=60.0)
    except CliError:
        return None
    return redacted(data) if isinstance(data, dict) else None


def report(eng_id: str) -> dict[str, Any]:
    require_id(eng_id, "engagement")
    data = _json(["report", eng_id], timeout=180.0)
    return redacted(data) if isinstance(data, dict) else {}
