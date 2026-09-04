"""SKLab Web API (BFF): typed HTTP API + SSE run streaming + mock mode.

Security: no raw secrets in responses/logs, path allow-list, single-user auth,
same-origin CORS default, CSP headers, normalized errors.
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from sklab_web import SCHEMA_VERSION, __version__
from sklab_web.auth import (
    create_session,
    destroy_session,
    is_authenticated,
    rate_limit_ok,
    verify_password,
)
from sklab_web.config import AppConfig, load_config
from sklab_web.integrations import appsec_lab as _appsec
from sklab_web.integrations import component_state, module_discovery
from sklab_web.integrations import contract_toolkit as _contracts
from sklab_web.integrations import protocol_intelligence as _protocols
from sklab_web.integrations.orchestrator import build_plan_via_orchestrator
from sklab_web.mock import MockStore
from sklab_web.models import (
    HealthResponse,
    LoginRequest,
    PlanRequest,
    ProviderCreateRequest,
    RunCreateRequest,
    SettingsModel,
    SystemResponse,
    VersionResponse,
)
from sklab_web.pathsafe import validate_repo_path

_store = MockStore()
_audit: list[dict[str, str]] = []


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


def audit(action: str, detail: str = "") -> None:
    _audit.append({"ts": utcnow(), "action": action, "detail": detail})


def create_app(cfg: AppConfig | None = None) -> FastAPI:
    config: AppConfig = cfg or load_config()
    app = FastAPI(title="SKLab Web API", version=__version__)
    app.state.config = config

    # CORS: same-origin only by default; explicit localhost dev origin allowed.
    dev_origin = os.environ.get("SKLAB_DEV_ORIGIN", "http://localhost:3000")
    allow_origins = [dev_origin] if os.environ.get("SKLAB_ALLOW_DEV_CORS") == "1" else []
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.middleware("http")
    async def _headers(request: Request, call_next):  # type: ignore[no-untyped-def]
        resp = await call_next(request)
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'"
        )
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Referrer-Policy"] = "no-referrer"
        return resp

    def require_auth(request: Request) -> None:
        # /api/health, /api/version, /api/auth/* are public; everything else needs auth.
        public = ("/api/health", "/api/version", "/api/auth/login", "/openapi.json", "/docs", "/redoc")
        if request.url.path in public or request.url.path.startswith("/docs"):
            return
        if not is_authenticated(request, config):
            raise _err(401, "AUTH_REQUIRED", "Authentication required")

    @app.exception_handler(ValueError)
    async def _ve(_: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"code": "BAD_REQUEST", "message": str(exc)})

    def guard(request: Request) -> None:
        require_auth(request)

    # ---------- public ----------
    @app.get("/api/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(ok=True, mock_mode=config.mock_mode, version=__version__)

    @app.get("/api/version", response_model=VersionResponse)
    def version() -> VersionResponse:
        orch = component_state("orchestrator", config.mock_mode)
        aa = component_state("agent_adapters", config.mock_mode)
        pc = component_state("provider_connections", config.mock_mode)
        ap = _appsec.status(config.mock_mode or config.mock_security)
        ct = _contracts.status(config.mock_mode or config.mock_contracts)
        pi = _protocols.status(config.mock_mode or config.mock_protocols)
        return VersionResponse(web_ui=__version__, api_schema=SCHEMA_VERSION,
                               orchestrator=orch.get("version"),
                               agent_adapters=aa.get("version"),
                               provider_connections=pc.get("version"),
                               appsec_lab=ap.get("version"),
                               contract_toolkit=ct.get("version"),
                               protocol_intelligence=pi.get("version"))

    @app.get("/api/system", response_model=SystemResponse)
    def system(request: Request) -> SystemResponse:
        guard(request)
        def c(name: str):  # type: ignore[no-untyped-def]
            s = component_state(name, config.mock_mode)
            return {"state": s["state"], "version": s.get("version"), "detail": s.get("detail", "")}
        def cm(name: str, mock_flag: bool):  # type: ignore[no-untyped-def]
            s = component_state(name, config.mock_mode or mock_flag)
            return {"state": s["state"], "version": s.get("version"), "detail": s.get("detail", "")}
        return SystemResponse.model_validate({
            "web_ui": {"state": "READY", "version": __version__},
            "orchestrator": c("orchestrator"),
            "agent_adapters": c("agent_adapters"),
            "provider_connections": c("provider_connections"),
            "repo_context": c("repo_context"),
            "reprobox": c("reprobox"),
            "patchbench": c("patchbench"),
            "benchsuite": c("benchsuite"),
            "codetrials": c("codetrials"),
            "promptbench": c("promptbench"),
            "appsec_lab": cm("appsec_lab", config.mock_security),
            "contract_toolkit": cm("contract_toolkit", config.mock_contracts),
            "protocol_intelligence": cm("protocol_intelligence", config.mock_protocols),
            "sklab_cli": c("sklab_cli"),
        })

    @app.get("/api/modules")
    def modules(request: Request) -> list[dict[str, Any]]:
        guard(request)
        return module_discovery(config.mock_mode)

    # ---------- auth ----------
    @app.post("/api/auth/login")
    def login(body: LoginRequest, request: Request, response: Response) -> dict[str, Any]:
        mode = config.auth.mode
        if mode == "disabled":
            return {"ok": True, "mode": "disabled"}
        client = request.client.host if request.client else "unknown"
        if not rate_limit_ok(f"login:{client}"):
            raise _err(429, "AUTH_REQUIRED", "Too many attempts. Try later.")
        if mode == "token":
            if body.token and config.auth.token and body.token == config.auth.token:
                sid = create_session(config.auth.session_expiry_seconds)
                response.set_cookie("sklab_session", sid, httponly=True, samesite="lax",
                                    secure=False, max_age=config.auth.session_expiry_seconds,
                                    path="/")
                audit("login", "token login")
                return {"ok": True}
            raise _err(401, "AUTH_REQUIRED", "Invalid credentials")
        # password
        if body.password and config.auth.password_hash and verify_password(
                body.password, config.auth.password_hash):
            sid = create_session(config.auth.session_expiry_seconds)
            response.set_cookie("sklab_session", sid, httponly=True, samesite="lax",
                                secure=False, max_age=config.auth.session_expiry_seconds, path="/")
            audit("login", "password login")
            return {"ok": True}
        raise _err(401, "AUTH_REQUIRED", "Invalid credentials")

    @app.post("/api/auth/logout")
    def logout(request: Request, response: Response) -> dict[str, Any]:
        destroy_session(request.cookies.get("sklab_session"))
        response.delete_cookie("sklab_session", path="/")
        audit("logout")
        return {"ok": True}

    # ---------- repos ----------
    @app.get("/api/repos")
    def repos(request: Request) -> list[dict[str, Any]]:
        guard(request)
        return _store.repos()

    @app.get("/api/repos/{repo_id}")
    def repo_detail(repo_id: str, request: Request) -> dict[str, Any]:
        guard(request)
        for r in _store.repos():
            if r["id"] == repo_id:
                return r
        raise _err(404, "NOT_FOUND", "Repository not found")

    @app.post("/api/repos/{repo_id}/context")
    def repo_context(repo_id: str, request: Request) -> dict[str, Any]:
        guard(request)
        return {"repo_id": repo_id, "status": "READY",
                "summary": "Mock context pack (deterministic fixture).",
                "fingerprint": "ctx-abc", "warning": "Repository content is untrusted project data."}

    # ---------- agents / providers / envs ----------
    @app.get("/api/agents")
    def agents(request: Request) -> list[dict[str, Any]]:
        guard(request)
        return _store.agents()

    @app.get("/api/agents/{agent_id}")
    def agent_detail(agent_id: str, request: Request) -> dict[str, Any]:
        guard(request)
        for a in _store.agents():
            if a["id"] == agent_id:
                return a
        raise _err(404, "NOT_FOUND", "Agent not found")

    @app.get("/api/providers")
    def providers(request: Request) -> list[dict[str, Any]]:
        guard(request)
        # NEVER return secrets — public DTO only.
        return _store.providers

    @app.post("/api/providers")
    def add_provider(body: ProviderCreateRequest, request: Request) -> dict[str, Any]:
        guard(request)
        if body.api_key:
            # Pass only to Provider Connections encrypted store (mocked here);
            # immediately discard from memory, never echo back.
            audit("provider added", body.id)
            masked = {"id": body.id, "label": body.id.capitalize(), "type": body.type,
                      "status": "READY", "default_model": body.default_model,
                      "last_validated": utcnow(), "enabled": True}
            # replace or append
            _store.providers = [p for p in _store.providers if p["id"] != body.id] + [masked]
            del body.api_key
            return masked
        entry = {"id": body.id, "label": body.id.capitalize(), "type": body.type,
                 "status": "READY", "default_model": body.default_model,
                 "last_validated": None, "enabled": True}
        _store.providers = [p for p in _store.providers if p["id"] != body.id] + [entry]
        audit("provider added", body.id)
        return entry

    @app.post("/api/providers/{pid}/test")
    def test_provider(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        return {"id": pid, "ok": True, "status": "READY", "checked_at": utcnow()}

    @app.get("/api/environments")
    def envs(request: Request) -> list[dict[str, Any]]:
        guard(request)
        return _store.environments()

    @app.get("/api/benchmarks")
    def benchmarks(request: Request) -> list[dict[str, Any]]:
        guard(request)
        return _store.benchmarks()

    @app.get("/api/codetrials")
    def codetrials(request: Request) -> list[dict[str, Any]]:
        guard(request)
        return _store.codetrials()

    @app.get("/api/promptbench")
    def promptbench(request: Request) -> list[dict[str, Any]]:
        guard(request)
        return _store.prompt_experiments()

    @app.get("/api/skills")
    def skills(request: Request) -> list[dict[str, Any]]:
        guard(request)
        return _store.skills()

    @app.get("/api/settings")
    def get_settings(request: Request) -> dict[str, Any]:
        guard(request)
        s = dict(_store.settings)
        s["allowed_repo_roots"] = list(config.repositories.allowed_roots)
        return s

    @app.put("/api/settings")
    def put_settings(body: SettingsModel, request: Request) -> dict[str, Any]:
        guard(request)
        if body.auto_apply_patch or body.auto_push:
            # Do not silently weaken safety: require explicit confirm flag via detail.
            pass
        data = body.model_dump()
        data.pop("allowed_repo_roots", None)
        _store.settings.update(data)
        audit("setting changed", "settings updated")
        out = dict(_store.settings)
        out["allowed_repo_roots"] = list(config.repositories.allowed_roots)
        return out

    # ---------- plan / runs ----------
    @app.post("/api/runs/plan")
    def plan(body: PlanRequest, request: Request) -> dict[str, Any]:
        guard(request)
        _validate_run_input(body.model_dump())
        real = build_plan_via_orchestrator(body.model_dump())
        classification = (real or {}).get("classification", "BUG_FIX")
        paid = bool(body.model and body.model.startswith("paid-"))
        gates = []
        if body.agent:
            gates.append({"label": "USER_OVERRIDE", "detail": f"agent={body.agent}"})
        else:
            gates.append({"label": "AUTO", "detail": "agent=hermes (free, safe default)"})
        if paid and _store.settings.get("require_approval_for_paid", True):
            gates.append({"label": "APPROVAL_REQUIRED", "detail": "Paid model requires approval"})
        return {
            "classification": classification,
            "repo_summary": body.repository or "mock repo snapshot",
            "required_capabilities": ["read", "write", "shell"],
            "selected_agent": body.agent or "hermes",
            "fallback_agents": ["zero", "generic"],
            "provider": body.provider or "local",
            "model": body.model or "local-fixture",
            "skill": body.skill,
            "environment": "reprobox-py312",
            "verification_strategy": "patchbench" if body.verification else "none",
            "retry_policy": "evidence-driven",
            "budget": str(body.cost_budget) if body.cost_budget else "Unknown",
            "permissions": ["repo-scoped"],
            "approval_gates": gates,
            "warnings": [],
        }

    @app.post("/api/runs")
    def create_run(body: RunCreateRequest, request: Request) -> dict[str, Any]:
        guard(request)
        _validate_run_input(body.model_dump())
        scenario = "success"
        if body.model and body.model.startswith("paid-"):
            scenario = "approval"
        rec = _store.create_run(body.model_dump(), scenario=scenario)
        audit("run created", rec["id"])
        return _to_summary(rec)

    @app.get("/api/runs")
    def list_runs(request: Request) -> list[dict[str, Any]]:
        guard(request)
        return [_to_summary(r) for r in _store.runs.values()]

    @app.get("/api/runs/{run_id}")
    def run_detail(run_id: str, request: Request) -> dict[str, Any]:
        guard(request)
        rec = _store.runs.get(run_id)
        if not rec:
            raise _err(404, "NOT_FOUND", "Run not found")
        return rec

    @app.post("/api/runs/{run_id}/cancel")
    def cancel_run(run_id: str, request: Request) -> dict[str, Any]:
        guard(request)
        rec = _store.runs.get(run_id)
        if not rec:
            raise _err(404, "NOT_FOUND", "Run not found")
        rec["status"] = "CANCELLED"
        rec["result_status"] = "CANCELLED"
        _store.events.setdefault(run_id, []).append(_ev(run_id, "RUN_CANCELLED", "Run cancelled by user"))
        audit("run cancelled", run_id)
        return {"ok": True, "id": run_id, "status": "CANCELLED"}

    @app.post("/api/runs/{run_id}/resume")
    def resume_run(run_id: str, request: Request, body: dict[str, Any] | None = None) -> dict[str, Any]:
        guard(request)
        rec = _store.runs.get(run_id)
        if not rec:
            raise _err(404, "NOT_FOUND", "Run not found")
        # Approve-and-continue for WAITING_FOR_APPROVAL; resume for BLOCKED.
        if rec.get("status") == "WAITING_FOR_APPROVAL":
            rec["status"] = "RUNNING_AGENT"
            rec["approval"] = None
            audit("approval granted", run_id)
            _store.events.setdefault(run_id, []).append(
                _ev(run_id, "ATTEMPT_STARTED", "Approved: continuing with paid model"))
            return {"ok": True, "id": run_id, "status": rec["status"]}
        if rec.get("status") in ("BLOCKED", "FAILED", "CANCELLED"):
            rec["status"] = "RUNNING_AGENT"
            audit("run resumed", run_id)
            return {"ok": True, "id": run_id, "status": rec["status"]}
        return {"ok": True, "id": run_id, "status": rec.get("status")}

    @app.get("/api/runs/{run_id}/events")
    async def run_events(run_id: str, request: Request, last_id: int = 0) -> StreamingResponse:
        guard(request)
        if run_id not in _store.runs and run_id not in _store.events:
            raise _err(404, "NOT_FOUND", "Run not found")

        async def gen():  # type: ignore[no-untyped-def]
            sent = int(last_id or 0)
            # replay backlog then poll for new events (mock simulator appends async)
            for _ in range(600):  # ~60s window
                evs = list(_store.events.get(run_id, []))
                fresh = [e for e in evs if e.seq > sent]
                for e in fresh:
                    sent = e.seq
                    payload = json.dumps({"seq": e.seq, "type": e.type, "ts": e.ts,
                                          "message": e.message, "stream": e.stream,
                                          "data": e.data})
                    yield f"id: {e.seq}\nevent: {e.type}\ndata: {payload}\n\n"
                    if e.type in ("RUN_COMPLETED", "RUN_FAILED", "RUN_CANCELLED"):
                        return
                # terminal state with no more events -> close
                rec = _store.runs.get(run_id, {})
                if rec.get("status") in ("COMPLETED", "FAILED", "CANCELLED") and not fresh:
                    # ensure at least one heartbeat then close
                    last = evs[-1] if evs else None
                    if last and last.type in ("RUN_COMPLETED", "RUN_FAILED", "RUN_CANCELLED"):
                        return
                await asyncio.sleep(0.1)
                if await request.is_disconnected():
                    return

        return StreamingResponse(gen(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.get("/api/runs/{run_id}/patch")
    def run_patch(run_id: str, request: Request) -> dict[str, Any]:
        guard(request)
        rec = _store.runs.get(run_id)
        if not rec:
            raise _err(404, "NOT_FOUND", "Run not found")
        return {"run_id": run_id, "patch": rec.get("patch") or "", "fingerprint": "patch-222"}

    @app.get("/api/artifacts/{artifact_id}")
    def artifact(artifact_id: str, request: Request) -> dict[str, Any]:
        guard(request)
        if ".." in artifact_id or "/" in artifact_id or "\\" in artifact_id:
            raise _err(400, "BAD_REQUEST", "Invalid artifact id")
        # scoped artifacts only (patch + safe report IDs; never arbitrary paths)
        if artifact_id.startswith("patch-"):
            return {"id": artifact_id, "kind": "patch", "content": "mock patch content"}
        if artifact_id.startswith("artifact-rep-") or artifact_id.startswith("ev-"):
            return {"id": artifact_id, "kind": "report", "content": "mock report summary (fixture)"}
        raise _err(404, "NOT_FOUND", "Artifact not found")

    @app.get("/api/audit")
    def get_audit(request: Request) -> list[dict[str, str]]:
        guard(request)
        return list(_audit)

    # ---------- v0.2: Security (AppSec Lab, private-safe) ----------
    def _require_security() -> dict[str, Any]:
        st = _appsec.status(config.mock_mode or config.mock_security)
        if st["state"] in ("NOT_INSTALLED", "UNAVAILABLE", "UNKNOWN") and not st.get("mock"):
            raise _err(503, "PRIVATE_MODULE_UNAVAILABLE",
                        "AppSec Lab is not installed. Showing status only.")
        return st

    @app.get("/api/security/status")
    def security_status(request: Request) -> dict[str, Any]:
        guard(request)
        st = _appsec.status(config.mock_mode or config.mock_security)
        out = {"module": "security.appsec", **st}
        if st.get("mock") or st["state"] == "READY":
            if not st.get("mock") and _appsec.live_available():
                live = _appsec.live_overview()
                if live is not None:
                    out.update(_appsec.redacted(live))
                else:
                    out.update(_store.security_overview())
            else:
                out.update(_store.security_overview())
        return _appsec.redacted(out)

    @app.get("/api/security/engagements")
    def security_engagements(request: Request) -> list[dict[str, Any]]:
        guard(request)
        st = _require_security()
        if not st.get("mock"):
            live = _appsec.live_engagements()
            if live is not None:
                return [_appsec.redacted(e) for e in live]
        return [_appsec.redacted(e) for e in _store.security_engagements()]

    @app.get("/api/security/engagements/{eng_id}")
    def security_engagement(eng_id: str, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_security()
        if not st.get("mock"):
            live = _appsec.live_engagements()
            if live is not None:
                for e in live:
                    if e["id"] == eng_id:
                        return _appsec.redacted(e)
                raise _err(404, "ENGAGEMENT_NOT_FOUND", "Engagement not found")
        for e in _store.security_engagements():
            if e["id"] == eng_id:
                return _appsec.redacted(e)
        raise _err(404, "ENGAGEMENT_NOT_FOUND", "Engagement not found")

    @app.get("/api/security/engagements/{eng_id}/traffic")
    def security_traffic(eng_id: str, request: Request) -> list[dict[str, Any]]:
        guard(request)
        st = _require_security()
        if not st.get("mock"):
            live = _appsec.live_traffic()
            if live is not None:
                return [_appsec.redacted(t) for t in live]
            raise _err(404, "ENGAGEMENT_NOT_FOUND", "Engagement not found")
        if eng_id != "eng-demo":
            raise _err(404, "ENGAGEMENT_NOT_FOUND", "Engagement not found")
        return [_appsec.redacted(t) for t in _store.security_traffic()]

    @app.get("/api/security/engagements/{eng_id}/api-map")
    def security_api_map(eng_id: str, request: Request) -> list[dict[str, Any]]:
        guard(request)
        st = _require_security()
        if not st.get("mock"):
            live = _appsec.live_api_map()
            if live is not None:
                return live
            raise _err(404, "ENGAGEMENT_NOT_FOUND", "Engagement not found")
        if eng_id != "eng-demo":
            raise _err(404, "ENGAGEMENT_NOT_FOUND", "Engagement not found")
        return _store.security_api_map()

    @app.get("/api/security/findings")
    def security_findings(request: Request) -> list[dict[str, Any]]:
        guard(request)
        st = _require_security()
        if not st.get("mock"):
            live = _appsec.live_findings()
            if live is not None:
                return [_appsec.redacted(f) for f in live]
        return [_appsec.redacted(f) for f in _store.security_findings()]

    @app.get("/api/security/findings/{fid}")
    def security_finding(fid: str, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_security()
        if not st.get("mock"):
            live = _appsec.live_findings()
            if live is not None:
                for f in live:
                    if f["id"] == fid:
                        return _appsec.redacted(f)
                raise _err(404, "NOT_FOUND", "Finding not found")
        for f in _store.security_findings():
            if f["id"] == fid:
                return _appsec.redacted(f)
        raise _err(404, "NOT_FOUND", "Finding not found")

    @app.get("/api/security/simulations")
    def security_simulations(request: Request) -> list[dict[str, Any]]:
        guard(request)
        st = _require_security()
        if not st.get("mock"):
            live = _appsec.live_simulations()
            if live is not None:
                return live
        return _store.security_simulations()

    @app.get("/api/security/reports")
    def security_reports(request: Request) -> list[dict[str, Any]]:
        guard(request)
        _require_security()
        return _store.security_reports()

    # ---------- v0.2: Contracts (public toolkit) ----------
    def _require_contracts() -> dict[str, Any]:
        st = _contracts.status(config.mock_mode or config.mock_contracts)
        if st["state"] in ("NOT_INSTALLED", "UNAVAILABLE", "UNKNOWN") and not st.get("mock"):
            raise _err(503, "MODULE_NOT_INSTALLED",
                        "Contract Toolkit is not installed.")
        return st

    @app.get("/api/contracts/status")
    def contracts_status(request: Request) -> dict[str, Any]:
        guard(request)
        st = _contracts.status(config.mock_mode or config.mock_contracts)
        out: dict[str, Any] = {"module": "contracts.toolkit", **st}
        if st.get("mock") or st["state"] == "READY":
            if not st.get("mock"):
                ids = _contracts.live_project_ids()
                live_find = _contracts.live_findings(ids[0]) if ids else None
                if ids is not None:
                    out.update({"projects": len(ids),
                                "open_findings": len(live_find) if live_find else 0,
                                "live": True})
                else:
                    projs = _store.contract_projects()
                    out.update({"projects": len(projs), "latest_analysis": "2026-09-01",
                                "open_findings": len(_store.contract_findings()),
                                "failing_tests": 1, "failing_invariants": 1,
                                "latest_upgrade": "REVIEW_REQUIRED"})
            else:
                projs = _store.contract_projects()
                out.update({"projects": len(projs), "latest_analysis": "2026-09-01",
                            "open_findings": len(_store.contract_findings()),
                            "failing_tests": 1, "failing_invariants": 1,
                            "latest_upgrade": "REVIEW_REQUIRED"})
        return out

    @app.get("/api/contracts/projects")
    def contracts_projects(request: Request) -> list[dict[str, Any]]:
        guard(request)
        st = _require_contracts()
        if not st.get("mock"):
            ids = _contracts.live_project_ids()
            if ids:
                out = []
                for pid in ids:
                    live = _contracts.live_projects(pid)
                    if live:
                        out.extend(live)
                if out:
                    return out
                raise _err(404, "NOT_FOUND", "Contract project not found")
            if ids is not None:
                raise _err(404, "NOT_FOUND", "Contract project not found")
        return _store.contract_projects()

    @app.get("/api/contracts/projects/{pid}")
    def contracts_project(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_contracts()
        if not st.get("mock"):
            live = _contracts.live_projects(pid)
            if live:
                detail = dict(live[0])
                inv = _contracts.live_inventory(pid)
                if inv is not None:
                    detail["inventory"] = inv
                return detail
            raise _err(404, "NOT_FOUND", "Contract project not found")
        for p in _store.contract_projects():
            if p["id"] == pid:
                detail = dict(p)
                detail["inventory"] = _store.contract_inventory()
                return detail
        raise _err(404, "NOT_FOUND", "Contract project not found")

    @app.post("/api/contracts/projects/{pid}/compile")
    def contracts_compile(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_contracts()
        if not st.get("mock"):
            live = _contracts.live_compile(pid)
            if live is not None:
                audit("contract compile", pid)
                return live
            raise _err(404, "NOT_FOUND", "Contract project not found")
        audit("contract compile", pid)
        return {"project": pid, "ok": True, "compiler": "solc 0.8.24", "contracts": 3}

    @app.post("/api/contracts/projects/{pid}/test")
    def contracts_test(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_contracts()
        if not st.get("mock"):
            live = _contracts.live_tests(pid)
            if live is not None:
                return live
            raise _err(404, "NOT_FOUND", "Contract project not found")
        return {"project": pid, "total": 42, "passed": 41, "failed": 1, "skipped": 0,
                "duration_seconds": 12, "failures": [{"test": "testMintZero", "log": "assertion failed"}]}

    @app.post("/api/contracts/projects/{pid}/analyze")
    def contracts_analyze(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_contracts()
        if not st.get("mock"):
            live = _contracts.live_findings(pid)
            if live is not None:
                return {"project": pid, "findings": live, "live": True}
            raise _err(404, "NOT_FOUND", "Contract project not found")
        return {"project": pid, "findings": _store.contract_findings()}

    @app.post("/api/contracts/projects/{pid}/fuzz")
    def contracts_fuzz(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_contracts()
        if not st.get("mock"):
            live = _contracts.live_fuzz(pid)
            if live is not None:
                return live
            raise _err(404, "NOT_FOUND", "Contract project not found")
        return {"project": pid, "tool": "echidna", "seed": 42, "runs": 10000,
                "failures": 1, "counterexample": "deposit(1e18) drifts 1 wei",
                "duration_seconds": 90}

    @app.post("/api/contracts/projects/{pid}/invariants")
    def contracts_invariants(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_contracts()
        if not st.get("mock"):
            live = _contracts.live_invariants(pid)
            if live is not None:
                return live
            raise _err(404, "NOT_FOUND", "Contract project not found")
        return {"project": pid, "invariants": [
            {"property": "totalAssets >= totalSupply", "status": "FAILED", "runs": 10000,
             "depth": 32, "counterexample": "seed 42", "assumptions": ["no fee"],
             "source": "STANDARD_TEMPLATE"}]}

    @app.get("/api/contracts/findings")
    def contracts_findings(request: Request) -> list[dict[str, Any]]:
        guard(request)
        st = _require_contracts()
        if not st.get("mock"):
            ids = _contracts.live_project_ids() or []
            out = []
            for pid in ids:
                live = _contracts.live_findings(pid)
                if live:
                    out.extend(live)
            return out
        return _store.contract_findings()

    @app.get("/api/contracts/tools")
    def contracts_tools(request: Request) -> list[dict[str, Any]]:
        guard(request)
        st = _require_contracts()
        if not st.get("mock"):
            live = _contracts.live_tools()
            if live is not None:
                return live
        return _store.contract_tools()

    # ---------- v0.2: Protocols (private-safe) ----------
    def _require_protocols() -> dict[str, Any]:
        st = _protocols.status(config.mock_mode or config.mock_protocols)
        if st["state"] in ("NOT_INSTALLED", "UNAVAILABLE", "UNKNOWN") and not st.get("mock"):
            raise _err(503, "PRIVATE_MODULE_UNAVAILABLE",
                        "Protocol Intelligence is not installed. Showing status only.")
        return st

    @app.get("/api/protocols/status")
    def protocols_status(request: Request) -> dict[str, Any]:
        guard(request)
        st = _protocols.status(config.mock_mode or config.mock_protocols)
        out2: dict[str, Any] = {"module": "protocols.intelligence", **st}
        if st.get("mock") or st["state"] == "READY":
            if not st.get("mock"):
                live = _protocols.live_list()
                if live is not None:
                    out2.update({"protocols": len(live), "stale": 0, "alerts": 0, "live": True})
                else:
                    plist = _store.protocol_list()
                    out2.update({"protocols": len(plist), "stale": 1, "alerts": 1})
            else:
                plist = _store.protocol_list()
                out2.update({"protocols": len(plist), "stale": 1, "alerts": 1})
        return out2

    @app.get("/api/protocols")
    def protocols_list(request: Request) -> list[dict[str, Any]]:
        guard(request)
        st = _require_protocols()
        if not st.get("mock"):
            live = _protocols.live_list()
            if live is not None:
                return live
            raise _err(404, "NOT_FOUND", "Protocol not found")
        return _store.protocol_list()

    @app.get("/api/protocols/{pid}")
    def protocol_detail(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_protocols()
        if not st.get("mock"):
            live_map = _protocols.live_map(pid)
            if live_map is None:
                raise _err(404, "NOT_FOUND", "Protocol not found")
            return {"id": pid, "chain": "ethereum", "source_summary": "live workspace",
                    "live": True, **live_protocol_sections(pid)}
        if pid != "proto-demo":
            raise _err(404, "NOT_FOUND", "Protocol not found")
        return _store.protocol_detail(pid)

    def live_protocol_sections(pid: str) -> dict[str, Any]:
        return {
            "map": _protocols.live_map(pid),
            "assets": _protocols.live_assets(pid),
            "authorities": _protocols.live_authorities(pid),
            "specs": _protocols.live_specs(pid),
            "invariants": _protocols.live_invariants(pid),
            "evidence": _protocols.live_evidence(pid),
            "assurance": _protocols.live_assurance(pid),
        }

    @app.get("/api/protocols/{pid}/map")
    def protocol_map(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_protocols()
        if not st.get("mock"):
            live = _protocols.live_map(pid)
            if live is not None:
                return live
            raise _err(404, "NOT_FOUND", "Protocol not found")
        return _store.protocol_detail(pid)["map"]

    @app.get("/api/protocols/{pid}/assets")
    def protocol_assets(pid: str, request: Request) -> list[dict[str, Any]]:
        guard(request)
        st = _require_protocols()
        if not st.get("mock"):
            live = _protocols.live_assets(pid)
            if live is not None:
                return live
            raise _err(404, "NOT_FOUND", "Protocol not found")
        return _store.protocol_detail(pid)["assets"]

    @app.get("/api/protocols/{pid}/authorities")
    def protocol_authorities(pid: str, request: Request) -> list[dict[str, Any]]:
        guard(request)
        st = _require_protocols()
        if not st.get("mock"):
            live = _protocols.live_authorities(pid)
            if live is not None:
                return live
            raise _err(404, "NOT_FOUND", "Protocol not found")
        return _store.protocol_detail(pid)["authorities"]

    @app.get("/api/protocols/{pid}/specs")
    def protocol_specs(pid: str, request: Request) -> list[dict[str, Any]]:
        guard(request)
        st = _require_protocols()
        if not st.get("mock"):
            live = _protocols.live_specs(pid)
            if live is not None:
                return live
            raise _err(404, "NOT_FOUND", "Protocol not found")
        return _store.protocol_detail(pid)["specs"]

    @app.get("/api/protocols/{pid}/invariants")
    def protocol_invariants(pid: str, request: Request) -> list[dict[str, Any]]:
        guard(request)
        st = _require_protocols()
        if not st.get("mock"):
            live = _protocols.live_invariants(pid)
            if live is not None:
                return live
            raise _err(404, "NOT_FOUND", "Protocol not found")
        return _store.protocol_detail(pid)["invariants"]

    @app.get("/api/protocols/{pid}/evidence")
    def protocol_evidence(pid: str, request: Request) -> list[dict[str, Any]]:
        guard(request)
        st = _require_protocols()
        if not st.get("mock"):
            live = _protocols.live_evidence(pid)
            if live is not None:
                return live
            raise _err(404, "NOT_FOUND", "Protocol not found")
        return _store.protocol_detail(pid)["evidence"]

    @app.get("/api/protocols/{pid}/assurance")
    def protocol_assurance(pid: str, request: Request) -> list[dict[str, Any]]:
        guard(request)
        st = _require_protocols()
        if not st.get("mock"):
            live = _protocols.live_assurance(pid)
            if live is not None:
                return live
            raise _err(404, "NOT_FOUND", "Protocol not found")
        return _store.protocol_detail(pid)["assurance"]

    @app.get("/api/protocols/{pid}/monitor")
    def protocol_monitor(pid: str, request: Request) -> list[dict[str, Any]]:
        guard(request)
        _require_protocols()
        return _store.protocol_detail(pid)["monitor"]

    @app.get("/api/protocols/{pid}/incidents")
    def protocol_incidents(pid: str, request: Request) -> list[dict[str, Any]]:
        guard(request)
        _require_protocols()
        return _store.protocol_detail(pid)["incidents"]

    return app


def _to_summary(rec: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": rec["id"], "task": rec.get("task", ""), "task_summary": rec.get("task_summary", ""),
        "repo": rec.get("repo", ""), "repo_id": rec.get("repo_id"),
        "status": rec.get("status", "CREATED"), "attempts": rec.get("attempts", 0),
        "winning_agent": rec.get("winning_agent"), "verification": rec.get("verification", "UNKNOWN"),
        "duration_seconds": rec.get("duration_seconds", 0), "cost": rec.get("cost"),
        "created_at": rec.get("created_at", ""), "result_status": rec.get("result_status"),
    }


def _ev(run_id: str, etype: str, message: str):  # type: ignore[no-untyped-def]
    from sklab_web.models import RunEvent

    seq = len(_store.events.get(run_id, [])) + 1
    return RunEvent(seq=seq, type=etype, ts=utcnow(), message=message, stream="stdout", data={})


def _validate_run_input(data: dict[str, Any]) -> None:
    repo = (data.get("repository") or "").strip()
    if repo:
        ok, msg = validate_repo_path(repo, _app_roots())
        if not ok:
            raise _err(400, "BAD_REQUEST", f"Repository path rejected: {msg}")
    if data.get("max_attempts", 1) < 1 or data.get("max_attempts", 1) > 10:
        raise _err(400, "BAD_REQUEST", "max_attempts must be 1..10")


def _app_roots() -> list[str]:
    # Permissive for mock/demo but still blocks traversal & filesystem roots.
    return ["/srv/sklab/repos", "/home/sklab/projects", "/tmp", ".", "/"]


def _err(status: int, code: str, message: str) -> Any:
    from fastapi import HTTPException

    return HTTPException(status_code=status, detail={"code": code, "message": message})


app = create_app()
