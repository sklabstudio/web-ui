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


def live_available(mock_mode: bool = False) -> bool:
    """True when the real private module is installed and mocks are off."""
    if mock_mode or _mock_enabled():
        return False
    ok, _ = _private_available()
    return ok


def _scenario_events(scenario: str = "normal-api") -> list:
    from sklab_appsec_lab.core.mock import mock_events

    try:
        return mock_events(scenario)
    except Exception:
        from sklab_appsec_lab.core.mock import mock_events as _me

        return _me("normal-api")


def live_engagements() -> list[dict[str, Any]] | None:
    """Real engagement registry (read-only). None when module missing/empty."""
    try:
        from sklab_appsec_lab.engagements.store import list_engagements, load_engagement
    except Exception:
        return None
    try:
        ids = list_engagements() or []
    except Exception:
        return None
    if not ids:
        return None
    out: list[dict[str, Any]] = []
    for eng_id in ids:
        try:
            eng = load_engagement(eng_id)
            dto = eng.model_dump(mode="python") if hasattr(eng, "model_dump") else {}
        except Exception:
            continue
        meta = dto.get("engagement", {}) if isinstance(dto, dict) else {}
        scope = dto.get("scope", {}) if isinstance(dto, dict) else {}
        domains = scope.get("domains", []) if isinstance(scope, dict) else []
        out.append({
            "id": str(meta.get("id", eng_id)),
            "name": str(meta.get("name", eng_id)),
            "status": str(meta.get("status", "ACTIVE")).upper(),
            "scope_summary": ", ".join(domains) if domains else "local fixture scope",
            "created_at": str(meta.get("created_at", "")),
            "last_run": str(meta.get("updated_at", meta.get("created_at", ""))),
            "finding_count": 0,
            "report_status": "READY",
            "live": True,
        })
    return out or None


def _capture(scenario: str = "normal-api"):  # type: ignore[no-untyped-def]
    from sklab_appsec_lab.traffic.capture import TrafficCapture

    cap = TrafficCapture()
    for event in _scenario_events(scenario):
        try:
            cap.record(event)
        except Exception:
            continue
    return cap


def live_traffic(scenario: str = "normal-api") -> list[dict[str, Any]] | None:
    """Real traffic DTOs (already redacted by the module). None on failure."""
    try:
        cap = _capture(scenario)
        rows = cap.to_dto()
    except Exception:
        return None
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        out.append({
            "ts": str(row.get("timestamp", "")),
            "method": str(row.get("method", "")),
            "host": str(row.get("host", "")),
            "path": str(row.get("path", "")),
            "status": row.get("status", 0),
            "kind": str(row.get("type", "REST")).upper(),
            "auth": "bearer-ref" if row.get("auth") else "none",
            "duration_ms": row.get("duration", 0),
            "flow": str(row.get("flow", "")),
            "live": True,
        })
    return out or None


def live_api_map(scenario: str = "normal-api") -> list[dict[str, Any]] | None:
    """Real endpoint inventory. None on failure."""
    try:
        from sklab_appsec_lab.api_map import build_inventory, inventory_to_dict

        cap = _capture(scenario)
        endpoints = inventory_to_dict(build_inventory(cap.events))
    except Exception:
        return None
    out: list[dict[str, Any]] = []
    for ep in endpoints:
        if not isinstance(ep, dict):
            continue
        roles = ep.get("status_behavior", {}) or {}
        out.append({
            "host": str(ep.get("host", "")),
            "route": str(ep.get("route_pattern", "")),
            "method": str(ep.get("method", "")),
            "auth": "required" if ep.get("auth_required") else "none",
            "roles": dict(roles) if isinstance(roles, dict) else {},
            "live": True,
        })
    return out or None


def live_findings(engagement_id: str = "", scenario: str = "normal-api") -> list[dict[str, Any]] | None:
    """Real analyzer findings normalized to the Web UI DTO. None on failure."""
    try:
        from sklab_appsec_lab.analyzers import (
            analyze_cors,
            analyze_errors,
            analyze_security_headers,
        )

        cap = _capture(scenario)
        findings = []
        findings += analyze_security_headers(cap.events, engagement_id)
        findings += analyze_cors(cap.events, engagement_id)
        findings += analyze_errors(cap.events, engagement_id)
    except Exception:
        return None
    out: list[dict[str, Any]] = []
    for f in findings:
        try:
            dto = f.model_dump(mode="python") if hasattr(f, "model_dump") else dict(f)
        except Exception:
            continue
        if not isinstance(dto, dict):
            continue
        impact = dto.get("impact", {}) or {}
        if not isinstance(impact, dict):
            impact = {}
        method = str(dto.get("http_method", ""))
        endpoint = str(dto.get("endpoint", ""))
        out.append({
            "id": str(dto.get("id", "")),
            "source": "appsec",
            "severity": str(dto.get("severity", "MEDIUM")),
            "confidence": str(dto.get("confidence", "NEEDS_REVIEW")),
            "title": str(dto.get("title", "")),
            "endpoint": f"{method} {endpoint}".strip() or endpoint,
            "flow": str(dto.get("browser_flow", "")),
            "status": str(dto.get("status", "OPEN")),
            "evidence_ref": str((dto.get("evidence", {}) or {}).get("id", dto.get("id", ""))),
            "retest_status": str(dto.get("retest_status", "NOT_RUN")),
            "description": str(dto.get("description", "")),
            "remediation": str(dto.get("remediation", "")),
            "impact": {k: str(v) for k, v in impact.items()},
            "live": True,
        })
    return out or None


def live_overview(scenario: str = "normal-api") -> dict[str, Any] | None:
    """Real overview counts derived from live traffic/findings. None on failure."""
    traffic = live_traffic(scenario)
    api_map = live_api_map(scenario)
    findings = live_findings("", scenario)
    if traffic is None or api_map is None or findings is None:
        return None
    open_findings = [f for f in findings if f.get("status") not in ("FIXED_VERIFIED", "FIXED")]
    return {
        "active_engagement": "live",
        "target_scope": f"live capture ({len(api_map)} routes)",
        "api_endpoints": len(api_map),
        "open_findings": len(open_findings),
        "captured_requests": len(traffic),
        "latest_simulation": "ANALYZER_SUITE",
        "live": True,
    }


def live_simulations() -> list[dict[str, Any]] | None:
    """Real safe simulations (bounded, no destructive actions). None on failure."""
    try:
        from sklab_appsec_lab.simulations import run_simulations

        rows = run_simulations()
    except Exception:
        return None
    out: list[dict[str, Any]] = []
    for i, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            continue
        out.append({
            "id": str(row.get("id", f"sim-{i:03d}")),
            "simulation": str(row.get("simulation", row.get("name", "UNKNOWN"))),
            "target": str(row.get("target", "")),
            "role": str(row.get("role", "")),
            "result": str(row.get("result", row.get("verdict", "UNKNOWN"))),
            "requests": row.get("requests", 0),
            "duration_ms": row.get("duration_ms", 0),
            "impact": str(row.get("impact", "LOW")),
            "evidence_ref": str(row.get("evidence_ref", row.get("id", ""))),
            "live": True,
        })
    return out or None


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
