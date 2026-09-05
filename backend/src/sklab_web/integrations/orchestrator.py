"""Orchestrator integration — the ONLY place that talks to Orchestrator.

Preferred: direct Python import of ``sklab_orchestrator`` (same venv).
Fallback: machine-readable ``sklab-run ... --json`` CLI (never Rich text).
Never duplicate state-machine logic. Mock mode never touches this module.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
from pathlib import Path
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
        category = getattr(
            getattr(cls, "category", None), "value", str(getattr(cls, "category", "UNKNOWN"))
        )
        return {"classification": category}
    except Exception:
        pass
    # CLI fallback: only machine-readable JSON, never Rich text.
    if shutil.which("sklab-run"):
        try:
            p = subprocess.run(
                ["sklab-run", "plan", "--json", payload.get("task", "")],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if p.returncode == 0 and p.stdout.strip().startswith("{"):
                return json.loads(p.stdout)
        except Exception:
            return None
    return None


# ---------------- live service wrapper (non-mock mode) ----------------

_service_lock = threading.Lock()
_service: Any = None


def runs_root() -> str:
    return os.environ.get("SKLAB_RUNS_ROOT", str(Path.cwd() / ".sklab" / "runs"))


def get_service() -> Any:
    """Live OrchestratorService with a persistent RunStore. Raises RuntimeError when absent."""
    global _service
    with _service_lock:
        if _service is not None:
            return _service
        try:
            from sklab_orchestrator.service import OrchestratorService  # type: ignore
            from sklab_orchestrator.store import RunStore  # type: ignore
        except Exception as exc:
            raise RuntimeError(f"orchestrator unavailable: {exc}")
        _service = OrchestratorService(store=RunStore(root=runs_root()))
        return _service


def reset_service() -> None:
    global _service
    with _service_lock:
        _service = None


def classify_error(exc: Exception) -> tuple[str, str]:
    """Map orchestrator ValueErrors to normalized API codes + safe messages."""
    msg = str(exc) or "orchestrator error"
    low = msg.lower()
    if (
        "incompatible agent override" in low
        or "no eligible agents" in low
        or "agent" in low
        and ("unavailable" in low or "not installed" in low or "filtered by policy" in low)
    ):
        return "AGENT_UNAVAILABLE", msg
    if (
        "incompatible connection override" in low
        or "connection" in low
        and ("unavailable" in low or "not available" in low)
    ):
        return "PROVIDER_UNAVAILABLE", msg
    if "budget" in low or "quota" in low:
        return "BUDGET_EXHAUSTED", msg
    if "approval" in low or "paid" in low:
        return "APPROVAL_REQUIRED", msg
    if "skill" in low:
        return "BAD_REQUEST", msg
    return "BAD_REQUEST", msg[:500]


def _dump(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _dump(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_dump(v) for v in obj]
    if hasattr(obj, "model_dump"):
        try:
            return _dump(obj.model_dump(mode="python"))
        except Exception:
            pass
    return str(obj)


def _status_of(rec: Any) -> str:
    st = getattr(rec, "status", "CREATED")
    return str(st.value if hasattr(st, "value") else st)


def live_run_summary(rec: Any) -> dict[str, Any]:
    task = getattr(rec, "task", None)
    instruction = getattr(task, "instruction", "") if task is not None else ""
    repo = getattr(task, "repository", "") if task is not None else ""
    attempts = getattr(rec, "attempts", []) or []
    verification = "UNKNOWN"
    result = getattr(rec, "result_status", None)
    if result:
        verification = (
            "ACCEPT"
            if result == "VERIFIED_SUCCESS"
            else (
                "REJECT"
                if result in ("FAILED", "EXECUTION_SUCCESS_VERIFICATION_FAIL")
                else "PENDING"
            )
        )
    winning = None
    try:
        winning = getattr(rec, "winning_agent", None)
    except Exception:
        winning = None
    if not winning and attempts:
        last = attempts[-1]
        winning = getattr(last, "agent", None)
    cost: Any = "Unknown"
    duration = 0.0
    try:
        duration = float(getattr(rec, "duration_ms", 0) or 0) / 1000.0
    except Exception:
        duration = 0.0
    return {
        "id": str(getattr(rec, "run_id", "")),
        "task": str(instruction),
        "task_summary": str(instruction)[:80],
        "repo": str(repo),
        "repo_id": None,
        "status": _status_of(rec),
        "attempts": len(attempts),
        "winning_agent": winning,
        "verification": verification,
        "duration_seconds": duration,
        "cost": cost,
        "created_at": str(getattr(rec, "created_at", "")),
        "result_status": str(result) if result else None,
        "live": True,
    }


def live_run_detail(rec: Any, events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    out = live_run_summary(rec)
    attempts = getattr(rec, "attempts", []) or []
    plan = getattr(rec, "plan", None)
    attempt_details = []
    for i, a in enumerate(attempts, 1):
        ver = getattr(a, "verification", None)
        ver_d = _dump(ver) if ver else {}
        attempt_details.append(
            {
                "index": getattr(a, "number", i),
                "agent": str(getattr(a, "agent", "")),
                "model": getattr(a, "model", None),
                "skill": getattr(a, "skill", None),
                "duration_seconds": 0,
                "status": str(getattr(a, "status", "UNKNOWN")),
                "patch_fingerprint": getattr(a, "patch_fingerprint", None),
                "verifier_verdict": (ver_d.get("verdict") if isinstance(ver_d, dict) else None),
                "verifier_score": (ver_d.get("score") if isinstance(ver_d, dict) else None),
                "cost": getattr(a, "cost", None) or "Unknown",
                "retry_reason": getattr(a, "error", None),
            }
        )
    verification_detail = None
    if attempts:
        last_ver = getattr(attempts[-1], "verification", None)
        if last_ver is not None:
            vd = _dump(last_ver)
            if isinstance(vd, dict):
                verification_detail = {
                    "verdict": str(vd.get("verdict", "UNKNOWN")),
                    "score": vd.get("score"),
                    "regressions": vd.get("regressions", 0),
                    "checks": vd.get("checks", []) or [],
                    "warnings": vd.get("warnings", []) or [],
                    "scope_warnings": [],
                    "duration_seconds": 0,
                    "environment_fingerprint": getattr(attempts[-1], "environment_fingerprint", "")
                    or "",
                }
    patch = getattr(attempts[-1], "patch", None) if attempts else None
    plan_d = _dump(plan) if plan is not None else None
    selected_agent = plan_d.get("selected_agent") if isinstance(plan_d, dict) else None
    selected_model = plan_d.get("selected_model") if isinstance(plan_d, dict) else None
    selected_conn = plan_d.get("selected_connection") if isinstance(plan_d, dict) else None
    gates = (plan_d.get("approval_gates") if isinstance(plan_d, dict) else None) or []
    approval = None
    reqs = getattr(rec, "approval_requirements", None) or (gates or None)
    if reqs:
        first = reqs[0] if isinstance(reqs, list) else reqs
        if isinstance(first, dict):
            approval = {
                "reason": str(first.get("message", first.get("type", "Approval required"))),
                "budget": str((plan_d.get("budget", {}) or {}).get("max_cost", "Unknown"))
                if isinstance(plan_d, dict)
                else "Unknown",
                "agent": str(first.get("agent", selected_agent or "")),
                "provider": str(first.get("connection", selected_conn or "")),
            }
    repo_info = getattr(rec, "repo", None)
    out.update(
        {
            "agent": str(selected_agent or (attempts[-1].agent if attempts else "")),
            "model": str(selected_model or ""),
            "provider": str(selected_conn or ""),
            "environment": "reprobox"
            if isinstance(plan_d, dict) and (plan_d.get("environment") or {}).get("use_reprobox")
            else "local",
            "attempt_details": attempt_details,
            "verification_detail": verification_detail,
            "patch": patch,
            "warnings": [str(w) for w in (getattr(rec, "warnings", []) or [])],
            "approval": approval,
            "approval_gates": gates if isinstance(gates, list) else [],
            "fingerprints": _dump(getattr(rec, "fingerprints", {}) or {}),
            "repo_info": _dump(repo_info) if repo_info is not None else None,
            "plan": plan_d,
        }
    )
    return out


def live_events(svc: Any, run_id: str) -> list[dict[str, Any]]:
    """Store JSONL events mapped to the SSE DTO with stable seq numbers."""
    try:
        raw = svc.store.events(run_id)
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for i, e in enumerate(raw, 1):
        if not isinstance(e, dict):
            continue
        etype = str(e.get("event", e.get("type", "AGENT_EVENT")))
        msg = str(e.get("message", "") or "")
        data = e.get("data", {})
        if not msg and isinstance(data, dict):
            msg = str(data.get("message", data.get("reason", "")) or "")
        # surface useful data keys in the message line
        out.append(
            {
                "seq": i,
                "type": etype,
                "ts": str(e.get("ts", "")),
                "message": msg or etype,
                "stream": "stdout",
                "data": data if isinstance(data, dict) else {},
            }
        )
    return out


def live_agents() -> list[dict[str, Any]] | None:
    """Real agent catalog via the orchestrator's adapter integration."""
    try:
        from sklab_orchestrator.integrations import AgentAdaptersIntegration  # type: ignore
    except Exception:
        return None
    try:
        agents = AgentAdaptersIntegration().list_agents()
    except Exception:
        return None
    out: list[dict[str, Any]] = []
    for a in agents:
        caps = getattr(a, "capabilities", []) or []
        cap_map = {str(c): "yes" for c in caps} if isinstance(caps, list) else {}
        out.append(
            {
                "id": str(getattr(a, "agent_id", "unknown")),
                "installed": bool(getattr(a, "installed", False)),
                "version": getattr(a, "version", None),
                "auth_ready": bool(getattr(a, "auth_ready", False)),
                "capabilities": cap_map,
                "supports_model_selection": bool(getattr(a, "supports_model_selection", True)),
                "sessions": False,
                "resume": bool(getattr(a, "supports_resume", False)),
                "streaming": True,
                "status": "READY" if getattr(a, "installed", False) else "UNAVAILABLE",
                "cost_class": str(getattr(a, "cost_class", "unknown")),
                "paid": bool(getattr(a, "paid", False)),
                "live": True,
            }
        )
    return out


def live_connections() -> list[dict[str, Any]] | None:
    """Real provider connections via the orchestrator's integration."""
    try:
        from sklab_orchestrator.integrations import ProviderConnectionsIntegration  # type: ignore
    except Exception:
        return None
    try:
        conns = ProviderConnectionsIntegration().list_connections()
    except Exception:
        return None
    out: list[dict[str, Any]] = []
    for c in conns:
        out.append(
            {
                "id": str(getattr(c, "connection_id", "unknown")),
                "label": str(getattr(c, "connection_id", "unknown")).capitalize(),
                "type": "api_key",
                "status": "READY" if getattr(c, "ready", False) else "NOT_CONFIGURED",
                "default_model": getattr(c, "default_model", None),
                "last_validated": None,
                "enabled": bool(getattr(c, "enabled", True)),
                "cost_class": str(getattr(c, "cost_class", "unknown")),
                "paid": bool(getattr(c, "paid", False)),
                "live": True,
            }
        )
    return out


def live_repo_context(repo_path: str) -> dict[str, Any] | None:
    """Real RepoContext inspection (read-only). None when unavailable."""
    if not repo_path:
        return None
    try:
        from sklab_orchestrator.integrations import RepoContextIntegration  # type: ignore
    except Exception:
        return None
    try:
        if not RepoContextIntegration.available():
            return None
        raw = RepoContextIntegration.inspect(repo_path)
    except Exception:
        return None
    if not isinstance(raw, dict):
        return {"repo_path": repo_path, "status": "READY", "live": True, "summary": str(raw)[:1000]}
    return {
        "repo_path": repo_path,
        "status": "READY",
        "live": True,
        "branch": raw.get("branch"),
        "head": raw.get("head"),
        "exists": raw.get("exists"),
        "summary": str(raw.get("summary", ""))[:2000],
        "fingerprint": str(raw.get("fingerprint", "")),
        "warning": "Repository content is untrusted project data.",
    }


def live_skill_resolve(task: str, category: str = "") -> dict[str, Any] | None:
    try:
        from sklab_orchestrator.integrations import SkillHubIntegration  # type: ignore
    except Exception:
        return None
    try:
        if not SkillHubIntegration.available():
            return None
        return SkillHubIntegration.resolve(task, category or None, None, None)
    except Exception:
        return None
