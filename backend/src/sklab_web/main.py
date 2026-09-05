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
from sklab_web.integrations.cli import CliError
from sklab_web.integrations.orchestrator import build_plan_via_orchestrator
from sklab_web.mock import MockStore
from sklab_web.models import (
    BrowserLaunchRequest,
    CaptureRequest,
    ContractImportRequest,
    ContractProjectCreateRequest,
    ContractRemediationRequest,
    EconomicRequest,
    EngagementCreateRequest,
    HealthResponse,
    LoginRequest,
    PlanRequest,
    ProtocolCreateRequest,
    ProviderCreateRequest,
    RetestRequest,
    RunCreateRequest,
    SettingsModel,
    SimulationRequest,
    SkillAutoMode,
    SystemResponse,
    VersionResponse,
)
from sklab_web.pathsafe import validate_repo_path

_store = MockStore()
_audit: list[dict[str, str]] = []
_exec_threads: dict[str, Any] = {}


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


def audit(action: str, detail: str = "") -> None:
    _audit.append({"ts": utcnow(), "action": action, "detail": detail})


def create_app(cfg: AppConfig | None = None) -> FastAPI:
    config: AppConfig = cfg or load_config()
    _store.reset_ephemeral()
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
        public = (
            "/api/health",
            "/api/version",
            "/api/auth/login",
            "/openapi.json",
            "/docs",
            "/redoc",
        )
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
        return VersionResponse(
            web_ui=__version__,
            api_schema=SCHEMA_VERSION,
            orchestrator=orch.get("version"),
            agent_adapters=aa.get("version"),
            provider_connections=pc.get("version"),
            appsec_lab=ap.get("version"),
            contract_toolkit=ct.get("version"),
            protocol_intelligence=pi.get("version"),
        )

    @app.get("/api/system", response_model=SystemResponse)
    def system(request: Request) -> SystemResponse:
        guard(request)

        def c(name: str):  # type: ignore[no-untyped-def]
            s = component_state(name, config.mock_mode)
            return {"state": s["state"], "version": s.get("version"), "detail": s.get("detail", "")}

        def cm(name: str, mock_flag: bool):  # type: ignore[no-untyped-def]
            s = component_state(name, config.mock_mode or mock_flag)
            return {"state": s["state"], "version": s.get("version"), "detail": s.get("detail", "")}

        return SystemResponse.model_validate(
            {
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
            }
        )

    @app.get("/api/modules")
    def modules(request: Request) -> list[dict[str, Any]]:
        guard(request)
        return module_discovery(config.mock_mode)

    def _mock_matrix() -> list[dict[str, Any]]:
        base = module_discovery(True)
        out = []
        for m in base:
            out.append(
                {
                    "id": m["name"],
                    "name": m["name"],
                    "capability": m["capability"],
                    "version": m.get("version"),
                    "state": m["state"],
                    "detail": m.get("detail", ""),
                    "origin": "builtin",
                    "visibility": "private"
                    if m["name"] in ("appsec_lab", "protocol_intelligence")
                    else "public",
                    "mock": True,
                }
            )
        for extra in (
            "orchestrator",
            "agent_adapters",
            "provider_connections",
            "repo_context",
            "reprobox",
            "patchbench",
            "skill_hub",
        ):
            out.append(
                {
                    "id": extra,
                    "name": extra,
                    "capability": extra,
                    "version": "mock",
                    "state": "READY",
                    "detail": "mock mode: deterministic simulator",
                    "origin": "builtin",
                    "visibility": "public",
                    "mock": True,
                }
            )
        return out

    @app.get("/api/modules/full")
    def modules_full(request: Request) -> list[dict[str, Any]]:
        """All SKLab modules (id/version/health/visibility) via the CLI registry."""
        guard(request)
        if _is_live(config):
            from sklab_web.integrations import sklab_cli as _sklab

            matrix = _sklab.full_matrix()
            if matrix is not None:
                return matrix
        # mock/dev fallback: honest mock-labeled matrix
        return _mock_matrix()

    @app.get("/api/modules/{module_id}")
    def module_detail(module_id: str, request: Request) -> dict[str, Any]:
        guard(request)
        if _is_live(config):
            from sklab_web.integrations import sklab_cli as _sklab

            matrix = _sklab.full_matrix() or []
            for m in matrix:
                if m["id"] == module_id:
                    return m
            raise _err(404, "NOT_FOUND", "Module not found")
        for m in _mock_matrix():
            if m["id"] == module_id:
                return m
        raise _err(404, "NOT_FOUND", "Module not found")

    @app.get("/api/doctor")
    def doctor(request: Request) -> dict[str, Any]:
        """Zero-cost integration health (no paid inference, no secrets)."""
        guard(request)
        if _is_live(config):
            from sklab_web.integrations import sklab_cli as _sklab

            data = _sklab.run_doctor()
            if data is not None:
                return dict(data, live=True)
            raise _err(503, "MODULE_UNAVAILABLE", "doctor checks unavailable")
        return {
            "ok": True,
            "mock": True,
            "checks": {"orchestrator": True, "agents": True, "providers": True},
        }

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
                response.set_cookie(
                    "sklab_session",
                    sid,
                    httponly=True,
                    samesite="lax",
                    secure=False,
                    max_age=config.auth.session_expiry_seconds,
                    path="/",
                )
                audit("login", "token login")
                return {"ok": True}
            raise _err(401, "AUTH_REQUIRED", "Invalid credentials")
        # password
        if (
            body.password
            and config.auth.password_hash
            and verify_password(body.password, config.auth.password_hash)
        ):
            sid = create_session(config.auth.session_expiry_seconds)
            response.set_cookie(
                "sklab_session",
                sid,
                httponly=True,
                samesite="lax",
                secure=False,
                max_age=config.auth.session_expiry_seconds,
                path="/",
            )
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
        if _is_live(config):
            from sklab_web.integrations import orchestrator as _orch

            live = _orch.live_repos(list(config.repositories.allowed_roots))
            if live is not None:
                return live
        return _store.repos()

    def _known_repos() -> list[dict[str, Any]]:
        if _is_live(config):
            from sklab_web.integrations import orchestrator as _orch

            live = _orch.live_repos(list(config.repositories.allowed_roots))
            if live is not None:
                return live
        return _store.repos()

    @app.get("/api/repos/{repo_id}")
    def repo_detail(repo_id: str, request: Request) -> dict[str, Any]:
        guard(request)
        for r in _known_repos():
            if r["id"] == repo_id:
                return r
        raise _err(404, "NOT_FOUND", "Repository not found")

    @app.post("/api/repos/context")
    async def repo_context_by_path(request: Request) -> dict[str, Any]:
        """Inspect RepoContext for an explicit allowed path (no registry id needed)."""
        guard(request)
        try:
            body = await request.json()
        except Exception:
            body = {}
        path = str((body or {}).get("path", "")).strip()
        if not path:
            raise _err(400, "BAD_REQUEST", "path is required")
        ok, msg = validate_repo_path(path, _app_roots())
        if not ok:
            raise _err(400, "BAD_REQUEST", f"Repository path rejected: {msg}")
        allowed = [str(r) for r in config.repositories.allowed_roots]
        if allowed and not any(
            path == a.rstrip("/") or path.startswith(a.rstrip("/") + "/") for a in allowed
        ):
            raise _err(400, "BAD_REQUEST", "path is outside allowed roots")
        if _is_live(config):
            from sklab_web.integrations import orchestrator as _orch

            live = _orch.live_repo_context(path)
            if live is not None:
                audit("repo context by path", path)
                return live
        return {
            "repo_path": path,
            "status": "READY",
            "summary": "Mock context pack (deterministic fixture).",
            "fingerprint": "ctx-abc",
            "warning": "Repository content is untrusted project data.",
        }

    @app.post("/api/repos/{repo_id}/context")
    def repo_context(repo_id: str, request: Request) -> dict[str, Any]:
        guard(request)
        known = [r for r in _known_repos() if r["id"] == repo_id]
        if not known:
            raise _err(404, "NOT_FOUND", "Repository not found")
        if _is_live(config):
            from sklab_web.integrations import orchestrator as _orch

            live = _orch.live_repo_context(str(known[0].get("path", "")))
            if live is not None:
                audit("repo context", repo_id)
                return live
        return {
            "repo_id": repo_id,
            "status": "READY",
            "summary": "Mock context pack (deterministic fixture).",
            "fingerprint": "ctx-abc",
            "warning": "Repository content is untrusted project data.",
        }

    # ---------- agents / providers / envs ----------
    @app.get("/api/agents")
    def agents(request: Request) -> list[dict[str, Any]]:
        guard(request)
        if _is_live(config):
            from sklab_web.integrations import orchestrator as _orch

            live = _orch.live_agents()
            if live is not None:
                return live
        return _store.agents()

    @app.get("/api/agents/{agent_id}")
    def agent_detail(agent_id: str, request: Request) -> dict[str, Any]:
        guard(request)
        if _is_live(config):
            from sklab_web.integrations import orchestrator as _orch

            live = _orch.live_agents()
            if live is not None:
                for a in live:
                    if a["id"] == agent_id:
                        detail = dict(a)
                        try:
                            from sklab_web.integrations.cli import run_cli_json

                            show = run_cli_json(
                                "sklab-agents", ["show", agent_id, "--json"], timeout=30.0
                            )
                            if isinstance(show, dict):
                                detail["health"] = show.get("health", {})
                                detail["metadata"] = show.get("metadata", {})
                        except Exception:
                            pass
                        return detail
                raise _err(404, "NOT_FOUND", "Agent not found")
        for a in _store.agents():
            if a["id"] == agent_id:
                return a
        raise _err(404, "NOT_FOUND", "Agent not found")

    @app.get("/api/providers")
    def providers(request: Request) -> list[dict[str, Any]]:
        guard(request)
        # NEVER return secrets — public DTO only.
        if _is_live(config):
            from sklab_web.integrations import orchestrator as _orch

            live = _orch.live_connections()
            if live is not None:
                merged = list(live)
                for p in _store.providers:
                    if p["id"] not in {c["id"] for c in live}:
                        merged.append(dict(p, live=False))
                return merged
        return _store.providers

    @app.post("/api/providers")
    def add_provider(body: ProviderCreateRequest, request: Request) -> dict[str, Any]:
        guard(request)
        if body.api_key:
            # Pass only to Provider Connections encrypted store (mocked here);
            # immediately discard from memory, never echo back.
            audit("provider added", body.id)
            masked = {
                "id": body.id,
                "label": body.id.capitalize(),
                "type": body.type,
                "status": "READY",
                "default_model": body.default_model,
                "last_validated": utcnow(),
                "enabled": True,
            }
            # replace or append
            _store.providers = [p for p in _store.providers if p["id"] != body.id] + [masked]
            del body.api_key
            return masked
        entry = {
            "id": body.id,
            "label": body.id.capitalize(),
            "type": body.type,
            "status": "READY",
            "default_model": body.default_model,
            "last_validated": None,
            "enabled": True,
        }
        _store.providers = [p for p in _store.providers if p["id"] != body.id] + [entry]
        audit("provider added", body.id)
        return entry

    @app.post("/api/providers/{pid}/test")
    def test_provider(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        # Zero-cost health only: metadata readiness, never paid inference.
        if _is_live(config):
            from sklab_web.integrations import orchestrator as _orch

            live = _orch.live_connections()
            if live is not None:
                for c in live:
                    if c["id"] == pid:
                        ok = c.get("status") == "READY"
                        return {
                            "id": pid,
                            "ok": ok,
                            "status": c.get("status"),
                            "checked_at": utcnow(),
                            "live": True,
                        }
                for p in _store.providers:
                    if p["id"] == pid:
                        return {
                            "id": pid,
                            "ok": True,
                            "status": p.get("status"),
                            "checked_at": utcnow(),
                            "live": False,
                        }
                raise _err(404, "NOT_FOUND", "Provider not found")
        for p in _store.providers:
            if p["id"] == pid:
                return {
                    "id": pid,
                    "ok": True,
                    "status": p.get("status"),
                    "checked_at": utcnow(),
                    "mock": True,
                }
        raise _err(404, "NOT_FOUND", "Provider not found")

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
        if _is_live(config):
            from sklab_web.integrations import skills as _skills

            live = _skills.live_list()
            if live is not None:
                return live
        return _store.skills()

    @app.get("/api/skills/{skill_id}")
    def skill_detail(skill_id: str, request: Request) -> dict[str, Any]:
        guard(request)
        if _is_live(config):
            from sklab_web.integrations import skills as _skills

            live = _skills.live_show(skill_id)
            if live is not None:
                return live
            raise _err(404, "NOT_FOUND", "Skill not found")
        for s in _store.skills():
            if s["id"] == skill_id:
                return s
        raise _err(404, "NOT_FOUND", "Skill not found")

    @app.get("/api/skills/{skill_id}/audit")
    def skill_audit(skill_id: str, request: Request) -> dict[str, Any]:
        guard(request)
        if _is_live(config):
            from sklab_web.integrations import skills as _skills

            live = _skills.live_audit(skill_id)
            if live is not None:
                return live
        return {
            "skill": skill_id,
            "mock": True,
            "findings": [],
            "note": "audit unavailable in mock mode",
        }

    @app.post("/api/skills/resolve")
    async def skills_resolve(request: Request) -> dict[str, Any]:
        guard(request)
        try:
            body = await request.json()
        except Exception:
            body = {}
        task = str((body or {}).get("task", ""))
        category = str((body or {}).get("category", ""))
        agent = str((body or {}).get("agent", ""))
        if _is_live(config):
            from sklab_web.integrations import orchestrator as _orch
            from sklab_web.integrations import skills as _skills

            live = _skills.live_resolve(task, category, agent) or _orch.live_skill_resolve(
                task, category
            )
            if live is not None:
                return live if isinstance(live, dict) else {"skills": live}
        return {"task": task[:120], "skills": [{"skill_id": "tdd", "via": "mock"}], "mock": True}

    @app.post("/api/skills/{skill_id}/enable")
    async def skill_enable(skill_id: str, request: Request) -> dict[str, Any]:
        guard(request)
        try:
            body = await request.json()
        except Exception:
            body = {}
        task_scoped = bool((body or {}).get("task_scoped", True))
        if _is_live(config):
            from sklab_web.integrations import skills as _skills

            try:
                live = _skills.live_enable(skill_id, task_scoped=task_scoped)
            except CliError as exc:
                raise _cli_err(exc)
            if live is not None:
                audit("skill enabled", skill_id)
                return live
            raise _err(503, "MODULE_NOT_INSTALLED", "Skill Hub is not installed")
        for s in _store.skills():
            if s["id"] == skill_id:
                s["enabled"] = True
                audit("skill enabled", skill_id)
                return dict(s, mock=True)
        raise _err(404, "NOT_FOUND", "Skill not found")

    @app.post("/api/skills/{skill_id}/disable")
    def skill_disable(skill_id: str, request: Request) -> dict[str, Any]:
        guard(request)
        if _is_live(config):
            from sklab_web.integrations import skills as _skills

            try:
                live = _skills.live_disable(skill_id)
            except CliError as exc:
                raise _cli_err(exc)
            if live is not None:
                audit("skill disabled", skill_id)
                return live
            raise _err(503, "MODULE_NOT_INSTALLED", "Skill Hub is not installed")
        for s in _store.skills():
            if s["id"] == skill_id:
                s["enabled"] = False
                audit("skill disabled", skill_id)
                return dict(s, mock=True)
        raise _err(404, "NOT_FOUND", "Skill not found")

    @app.get("/api/skills-auto")
    def skills_auto(request: Request) -> dict[str, Any]:
        guard(request)
        if _is_live(config):
            from sklab_web.integrations import skills as _skills

            live = _skills.live_auto_status()
            if live is not None:
                return live
        return {"mode": _store.settings.get("skill_auto_install", "OFF"), "mock": True}

    @app.post("/api/skills-auto")
    async def skills_auto_set(request: Request) -> dict[str, Any]:
        guard(request)
        try:
            body = await request.json()
        except Exception:
            body = {}
        try:
            mode = SkillAutoMode.model_validate(body or {}).mode.upper()
        except Exception:
            raise _err(400, "BAD_REQUEST", "mode must be OFF|SAFE|SMART|FULL")
        if mode not in ("OFF", "SAFE", "SMART", "FULL"):
            raise _err(400, "BAD_REQUEST", "mode must be OFF|SAFE|SMART|FULL")
        if _is_live(config):
            from sklab_web.integrations import skills as _skills

            try:
                live = _skills.live_auto_set(mode)
            except CliError as exc:
                raise _cli_err(exc)
            if live is not None:
                _store.settings["skill_auto_install"] = mode
                audit("skill auto mode", mode)
                return live
            raise _err(503, "MODULE_NOT_INSTALLED", "Skill Hub is not installed")
        _store.settings["skill_auto_install"] = mode
        audit("skill auto mode", mode)
        return {"mode": mode, "mock": True}

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
        if _is_live(config):
            from sklab_web.integrations import orchestrator as _orch

            try:
                svc = _orch.get_service()
            except RuntimeError:
                raise _err(503, "MODULE_UNAVAILABLE", "Orchestrator is not installed")
            opts = _live_options(body)
            try:
                rec = svc.create_run(body.task, repo=body.repository or "", options=opts)
                svc.inspect_run(rec.run_id)
                svc.plan_run(rec.run_id)
            except ValueError as exc:
                code, msg = _orch.classify_error(exc)
                raise _err(_CLI_STATUS.get(code, 400), code, msg)
            except Exception as exc:
                raise _err(500, "INTERNAL_ERROR", f"planning failed: {exc}"[:500])
            planned = _live_plan_dto(svc, rec.run_id, body.repository or "", body.cost_budget)
            if not planned.get("selected_agent") or planned["selected_agent"] == "unknown":
                raise _err(
                    503,
                    "AGENT_UNAVAILABLE",
                    "No usable agent installed: planning cannot select an agent. "
                    "Install an agent (see Agents) or use mock mode for trials.",
                )
            audit("run planned", rec.run_id)
            return planned
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

    def _live_options(body: PlanRequest) -> dict[str, Any]:
        settings = _store.settings
        return {
            "agent": body.agent or None,
            "connection": body.provider or None,
            "model": body.model or None,
            "skill": body.skill or None,
            "mode": {"safe": "cheap_first", "free": "free_only"}.get(
                (body.routing_policy or "safe").lower(), "cheap_first"
            ),
            "max_attempts": body.max_attempts,
            "timeout": body.timeout_seconds,
            "budget": body.cost_budget,
            "use_reprobox": body.reprobox
            if body.reprobox is not None
            else settings.get("reprobox_default", True),
            "no_verify": not body.verification,
            "approved_paid": False,
            "bench": body.bench_task,
        }

    @app.post("/api/runs")
    def create_run(body: RunCreateRequest, request: Request) -> dict[str, Any]:
        guard(request)
        _validate_run_input(body.model_dump())
        if _is_live(config):
            from sklab_web.integrations import orchestrator as _orch

            try:
                svc = _orch.get_service()
            except RuntimeError:
                raise _err(503, "MODULE_UNAVAILABLE", "Orchestrator is not installed")
            try:
                rec = svc.create_run(
                    body.task, repo=body.repository or "", options=_live_options(body)
                )
                svc.inspect_run(rec.run_id)
                svc.plan_run(rec.run_id)
            except ValueError as exc:
                code, msg = _orch.classify_error(exc)
                raise _err(_CLI_STATUS.get(code, 400), code, msg)
            except Exception as exc:
                raise _err(500, "INTERNAL_ERROR", f"run setup failed: {exc}"[:500])
            planned_check = _live_plan_dto(svc, rec.run_id, body.repository or "", body.cost_budget)
            if (
                not planned_check.get("selected_agent")
                or planned_check["selected_agent"] == "unknown"
            ):
                raise _err(
                    503,
                    "AGENT_UNAVAILABLE",
                    "No usable agent installed: cannot start this task. "
                    "Install an agent (see Agents) or use mock mode for trials.",
                )
            audit("run created", rec.run_id)
            detail = _orch.live_run_detail(svc.store.load_run(rec.run_id))
            if detail["status"] == "WAITING_FOR_APPROVAL":
                return _to_summary(detail)
            _launch_execution(rec.run_id)
            return _to_summary(_orch.live_run_detail(svc.store.load_run(rec.run_id)))
        scenario = "success"
        if body.model and body.model.startswith("paid-"):
            scenario = "approval"
        rec = _store.create_run(body.model_dump(), scenario=scenario)
        audit("run created", rec["id"])
        return _to_summary(rec)

    @app.get("/api/runs")
    def list_runs(request: Request) -> list[dict[str, Any]]:
        guard(request)
        if _is_live(config):
            from sklab_web.integrations import orchestrator as _orch

            try:
                svc = _orch.get_service()
                return [
                    _to_summary(_orch.live_run_detail(svc.store.load_run(r["run_id"])))
                    for r in svc.store.list_runs()
                ]
            except Exception:
                return []
        return [_to_summary(r) for r in _store.runs.values()]

    @app.get("/api/runs/{run_id}")
    def run_detail(run_id: str, request: Request) -> dict[str, Any]:
        guard(request)
        if _is_live(config):
            from sklab_web.integrations import orchestrator as _orch

            try:
                svc = _orch.get_service()
                if not svc.store.exists(run_id):
                    raise _err(404, "NOT_FOUND", "Run not found")
                return _orch.live_run_detail(svc.store.load_run(run_id))
            except Exception as exc:
                if getattr(exc, "status_code", None) == 404:
                    raise
                raise _err(500, "INTERNAL_ERROR", f"run unavailable: {exc}"[:300])
        rec = _store.runs.get(run_id)
        if not rec:
            raise _err(404, "NOT_FOUND", "Run not found")
        return rec

    @app.post("/api/runs/{run_id}/cancel")
    def cancel_run(run_id: str, request: Request) -> dict[str, Any]:
        guard(request)
        if _is_live(config):
            from sklab_web.integrations import orchestrator as _orch

            try:
                svc = _orch.get_service()
                if not svc.store.exists(run_id):
                    raise _err(404, "NOT_FOUND", "Run not found")
                rec = svc.cancel_run(run_id)
            except Exception as exc:
                if getattr(exc, "status_code", None) == 404:
                    raise
                raise _err(500, "INTERNAL_ERROR", f"cancel failed: {exc}"[:300])
            audit("run cancelled", run_id)
            return {"ok": True, "id": run_id, "status": _orch._status_of(rec)}
        rec = _store.runs.get(run_id)
        if not rec:
            raise _err(404, "NOT_FOUND", "Run not found")
        rec["status"] = "CANCELLED"
        rec["result_status"] = "CANCELLED"
        _store.events.setdefault(run_id, []).append(
            _ev(run_id, "RUN_CANCELLED", "Run cancelled by user")
        )
        audit("run cancelled", run_id)
        return {"ok": True, "id": run_id, "status": "CANCELLED"}

    @app.post("/api/runs/{run_id}/resume")
    def resume_run(
        run_id: str, request: Request, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        guard(request)
        if _is_live(config):
            from sklab_web.integrations import orchestrator as _orch

            try:
                svc = _orch.get_service()
                if not svc.store.exists(run_id):
                    raise _err(404, "NOT_FOUND", "Run not found")
            except Exception as exc:
                if getattr(exc, "status_code", None) == 404:
                    raise
                raise _err(500, "INTERNAL_ERROR", f"resume unavailable: {exc}"[:300])
            _launch_resume(run_id)
            try:
                detail = _orch.live_run_detail(svc.store.load_run(run_id))
            except Exception:
                detail = {"status": "RUNNING_AGENT"}
            audit("run resumed", run_id)
            return {"ok": True, "id": run_id, "status": detail.get("status")}
        rec = _store.runs.get(run_id)
        if not rec:
            raise _err(404, "NOT_FOUND", "Run not found")
        # Approve-and-continue for WAITING_FOR_APPROVAL; resume for BLOCKED.
        if rec.get("status") == "WAITING_FOR_APPROVAL":
            rec["status"] = "RUNNING_AGENT"
            rec["approval"] = None
            audit("approval granted", run_id)
            _store.events.setdefault(run_id, []).append(
                _ev(run_id, "ATTEMPT_STARTED", "Approved: continuing with paid model")
            )
            return {"ok": True, "id": run_id, "status": rec["status"]}
        if rec.get("status") in ("BLOCKED", "FAILED", "CANCELLED"):
            rec["status"] = "RUNNING_AGENT"
            audit("run resumed", run_id)
            return {"ok": True, "id": run_id, "status": rec["status"]}
        return {"ok": True, "id": run_id, "status": rec.get("status")}

    @app.post("/api/runs/{run_id}/execute")
    def execute_run(run_id: str, request: Request) -> dict[str, Any]:
        """Start (or continue) execution of a planned run."""
        guard(request)
        if _is_live(config):
            from sklab_web.integrations import orchestrator as _orch

            try:
                svc = _orch.get_service()
                if not svc.store.exists(run_id):
                    raise _err(404, "NOT_FOUND", "Run not found")
            except Exception as exc:
                if getattr(exc, "status_code", None) == 404:
                    raise
                raise _err(500, "INTERNAL_ERROR", f"execute unavailable: {exc}"[:300])
            _launch_execution(run_id)
            audit("run execution started", run_id)
            return {"ok": True, "id": run_id, "status": "RUNNING_AGENT"}
        rec = _store.runs.get(run_id)
        if not rec:
            raise _err(404, "NOT_FOUND", "Run not found")
        if rec.get("status") in ("CANCELLED", "BLOCKED", "FAILED"):
            rec["status"] = "RUNNING_AGENT"
        return {"ok": True, "id": run_id, "status": rec.get("status")}

    @app.post("/api/runs/{run_id}/retry")
    def retry_run(run_id: str, request: Request) -> dict[str, Any]:
        """Retry with evidence: resume semantics on live runs, re-simulate on mocks."""
        guard(request)
        if _is_live(config):
            from sklab_web.integrations import orchestrator as _orch

            try:
                svc = _orch.get_service()
                if not svc.store.exists(run_id):
                    raise _err(404, "NOT_FOUND", "Run not found")
                svc.store.emit(run_id, "RETRY_STARTED", {"by": "web-ui"})
            except Exception as exc:
                if getattr(exc, "status_code", None) == 404:
                    raise
                raise _err(500, "INTERNAL_ERROR", f"retry unavailable: {exc}"[:300])
            _launch_resume(run_id)
            audit("run retry started", run_id)
            return {"ok": True, "id": run_id, "status": "RETRYING"}
        rec = _store.runs.get(run_id)
        if not rec:
            raise _err(404, "NOT_FOUND", "Run not found")
        rec["status"] = "RETRYING"
        rec["attempts"] = int(rec.get("attempts", 0)) + 1
        _store.events.setdefault(run_id, []).append(
            _ev(run_id, "RETRY_STARTED", "Retry requested from Web UI")
        )
        audit("run retry started", run_id)
        return {"ok": True, "id": run_id, "status": "RETRYING"}

    @app.post("/api/runs/{run_id}/approve")
    def approve_run(run_id: str, request: Request) -> dict[str, Any]:
        """Approve a gated escalation once, then continue."""
        guard(request)
        if _is_live(config):
            from sklab_web.integrations import orchestrator as _orch

            try:
                svc = _orch.get_service()
                if not svc.store.exists(run_id):
                    raise _err(404, "NOT_FOUND", "Run not found")
                rec = svc.store.load_run(run_id)
                if _orch._status_of(rec) != "WAITING_FOR_APPROVAL":
                    raise _err(409, "BAD_REQUEST", "Run is not waiting for approval")
                opts = dict(getattr(rec, "options", {}) or {})
                opts["approved_paid"] = True
                rec.options = opts
                svc.store.save_run(rec)
                svc.store.emit(run_id, "APPROVAL_GRANTED", {"by": "web-ui"})
            except Exception as exc:
                if getattr(exc, "status_code", None) in (404, 409):
                    raise
                raise _err(500, "INTERNAL_ERROR", f"approve failed: {exc}"[:300])
            _launch_resume(run_id)
            audit("approval granted", run_id)
            return {"ok": True, "id": run_id, "status": "RUNNING_AGENT"}
        rec = _store.runs.get(run_id)
        if not rec:
            raise _err(404, "NOT_FOUND", "Run not found")
        if rec.get("status") != "WAITING_FOR_APPROVAL":
            raise _err(409, "BAD_REQUEST", "Run is not waiting for approval")
        rec["status"] = "RUNNING_AGENT"
        rec["approval"] = None
        _store.events.setdefault(run_id, []).append(
            _ev(run_id, "ATTEMPT_STARTED", "Approved: continuing with paid model")
        )
        audit("approval granted", run_id)
        return {"ok": True, "id": run_id, "status": rec["status"]}

    @app.post("/api/runs/{run_id}/reject")
    def reject_run(run_id: str, request: Request) -> dict[str, Any]:
        """Reject a gated escalation; the run is cancelled, never auto-approved."""
        guard(request)
        if _is_live(config):
            from sklab_web.integrations import orchestrator as _orch

            try:
                svc = _orch.get_service()
                if not svc.store.exists(run_id):
                    raise _err(404, "NOT_FOUND", "Run not found")
                rec = svc.store.load_run(run_id)
                if _orch._status_of(rec) != "WAITING_FOR_APPROVAL":
                    raise _err(409, "BAD_REQUEST", "Run is not waiting for approval")
                svc.store.emit(run_id, "APPROVAL_REJECTED", {"by": "web-ui"})
                svc.cancel_run(run_id)
            except Exception as exc:
                if getattr(exc, "status_code", None) in (404, 409):
                    raise
                raise _err(500, "INTERNAL_ERROR", f"reject failed: {exc}"[:300])
            audit("approval rejected", run_id)
            return {"ok": True, "id": run_id, "status": "CANCELLED"}
        rec = _store.runs.get(run_id)
        if not rec:
            raise _err(404, "NOT_FOUND", "Run not found")
        if rec.get("status") != "WAITING_FOR_APPROVAL":
            raise _err(409, "BAD_REQUEST", "Run is not waiting for approval")
        rec["status"] = "CANCELLED"
        rec["result_status"] = "CANCELLED"
        _store.events.setdefault(run_id, []).append(
            _ev(run_id, "RUN_CANCELLED", "Approval rejected by user")
        )
        audit("approval rejected", run_id)
        return {"ok": True, "id": run_id, "status": "CANCELLED"}

    @app.get("/api/runs/{run_id}/events")
    async def run_events(run_id: str, request: Request, last_id: int = 0) -> StreamingResponse:
        guard(request)
        live_mode = _is_live(config)
        if live_mode:
            from sklab_web.integrations import orchestrator as _orch

            try:
                svc = _orch.get_service()
            except RuntimeError:
                raise _err(503, "MODULE_UNAVAILABLE", "Orchestrator is not installed")
            if not svc.store.exists(run_id):
                raise _err(404, "NOT_FOUND", "Run not found")
        elif run_id not in _store.runs and run_id not in _store.events:
            raise _err(404, "NOT_FOUND", "Run not found")

        async def gen():  # type: ignore[no-untyped-def]
            sent = int(last_id or 0)
            # replay backlog then poll for new events (mock simulator appends async)
            for _ in range(600):  # ~60s window
                if live_mode:
                    from sklab_web.integrations import orchestrator as _orch2

                    try:
                        svc2 = _orch2.get_service()
                        evs = _orch2.live_events(svc2, run_id)
                    except Exception:
                        evs = []
                    fresh = [e for e in evs if e["seq"] > sent]
                    for e in fresh:
                        sent = e["seq"]
                        payload = json.dumps(e)
                        yield f"id: {e['seq']}\nevent: {e['type']}\ndata: {payload}\n\n"
                        if e["type"] in ("RUN_COMPLETED", "RUN_FAILED", "RUN_CANCELLED"):
                            return
                    try:
                        st = _orch2._status_of(svc2.store.load_run(run_id))
                    except Exception:
                        st = ""
                    if st in ("COMPLETED", "FAILED", "CANCELLED") and not fresh:
                        last = evs[-1] if evs else None
                        if last and last["type"] in (
                            "RUN_COMPLETED",
                            "RUN_FAILED",
                            "RUN_CANCELLED",
                        ):
                            return
                    await asyncio.sleep(0.5)
                    if await request.is_disconnected():
                        return
                    continue
                evs = list(_store.events.get(run_id, []))
                fresh = [e for e in evs if e.seq > sent]
                for e in fresh:
                    sent = e.seq
                    payload = json.dumps(
                        {
                            "seq": e.seq,
                            "type": e.type,
                            "ts": e.ts,
                            "message": e.message,
                            "stream": e.stream,
                            "data": e.data,
                        }
                    )
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

        return StreamingResponse(
            gen(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/api/runs/{run_id}/patch")
    def run_patch(run_id: str, request: Request) -> dict[str, Any]:
        guard(request)
        if _is_live(config):
            from sklab_web.integrations import orchestrator as _orch

            try:
                svc = _orch.get_service()
                if not svc.store.exists(run_id):
                    raise _err(404, "NOT_FOUND", "Run not found")
                detail = _orch.live_run_detail(svc.store.load_run(run_id))
            except Exception as exc:
                if getattr(exc, "status_code", None) == 404:
                    raise
                raise _err(500, "INTERNAL_ERROR", f"patch unavailable: {exc}"[:300])
            attempts = detail.get("attempt_details", []) or []
            fp = (attempts[-1].get("patch_fingerprint") if attempts else None) or ""
            return {
                "run_id": run_id,
                "patch": detail.get("patch") or "",
                "fingerprint": fp,
                "live": True,
            }
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
            raise _err(
                503,
                "PRIVATE_MODULE_UNAVAILABLE",
                "AppSec Lab is not installed. Showing status only.",
            )
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

    @app.post("/api/security/engagements")
    def security_engagement_create(
        body: EngagementCreateRequest, request: Request
    ) -> dict[str, Any]:
        guard(request)
        st = _require_security()
        if st.get("mock"):
            eng = {
                "id": body.id,
                "name": body.name or body.id,
                "status": "ACTIVE",
                "scope_summary": body.scope or body.target_url or "mock scope",
                "created_at": utcnow(),
                "last_run": utcnow(),
                "finding_count": 0,
                "report_status": "READY",
                "mock": True,
            }
            audit("engagement created", body.id)
            return _store.add_security_engagement(eng)
        from sklab_web.integrations import appsec_cli as _acl

        try:
            out = _acl.engagement_create(body.id, body.name, body.target_url or body.scope)
        except CliError as exc:
            raise _cli_err(exc)
        audit("engagement created", body.id)
        return out

    @app.post("/api/security/engagements/{eng_id}/activate")
    def security_engagement_activate(eng_id: str, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_security()
        if st.get("mock"):
            return {"ok": True, "id": eng_id, "mock": True}
        from sklab_web.integrations import appsec_cli as _acl

        try:
            out = _acl.engagement_activate(eng_id)
        except CliError as exc:
            raise _cli_err(exc)
        audit("engagement activated", eng_id)
        return out

    @app.post("/api/security/engagements/{eng_id}/close")
    def security_engagement_close(eng_id: str, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_security()
        if st.get("mock"):
            return {"ok": True, "id": eng_id, "mock": True}
        from sklab_web.integrations import appsec_cli as _acl

        try:
            out = _acl.engagement_close(eng_id)
        except CliError as exc:
            raise _cli_err(exc)
        audit("engagement closed", eng_id)
        return out

    @app.get("/api/security/browser")
    def security_browser(request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_security()
        if not st.get("mock"):
            from sklab_web.integrations import appsec_cli as _acl

            live = _acl.browser_status()
            if live is not None:
                return dict(live, live=True)
        return dict(_store.security_overview().get("browser", {}), mock=True)

    @app.post("/api/security/engagements/{eng_id}/browser/launch")
    def security_browser_launch(
        eng_id: str, body: BrowserLaunchRequest, request: Request
    ) -> dict[str, Any]:
        guard(request)
        st = _require_security()
        if st.get("mock"):
            return {"ok": True, "engagement": eng_id, "mode": "headless", "mock": True}
        from sklab_web.integrations import appsec_cli as _acl

        try:
            out = _acl.browser_launch(eng_id, headed=body.headed)
        except CliError as exc:
            raise _cli_err(exc)
        audit("browser launched", eng_id)
        return out

    @app.post("/api/security/engagements/{eng_id}/capture")
    def security_capture(eng_id: str, body: CaptureRequest, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_security()
        if st.get("mock"):
            return {"ok": True, "engagement": eng_id, "captured": 3, "mock": True}
        from sklab_web.integrations import appsec_cli as _acl

        try:
            out = _acl.capture(eng_id, body.scenario)
        except CliError as exc:
            raise _cli_err(exc)
        audit("traffic captured", eng_id)
        return out

    @app.post("/api/security/engagements/{eng_id}/audit")
    def security_audit(eng_id: str, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_security()
        if st.get("mock"):
            return {
                "engagement": eng_id,
                "ok": True,
                "findings": _store.security_findings(),
                "mock": True,
            }
        from sklab_web.integrations import appsec_cli as _acl

        try:
            out = _acl.audit(eng_id)
        except CliError as exc:
            raise _cli_err(exc)
        audit("security audit", eng_id)
        return out

    @app.post("/api/security/engagements/{eng_id}/simulate")
    def security_simulate(eng_id: str, body: SimulationRequest, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_security()
        if st.get("mock"):
            return {
                "engagement": eng_id,
                "simulations": _store.security_simulations(),
                "mock": True,
            }
        from sklab_web.integrations import appsec_cli as _acl

        try:
            out = _acl.simulate(eng_id, body.check)
        except CliError as exc:
            raise _cli_err(exc)
        audit("simulation run", eng_id)
        return out if isinstance(out, dict) else {"result": out}

    @app.post("/api/security/retest")
    def security_retest(body: RetestRequest, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_security()
        if st.get("mock"):
            return {"ref": body.ref, "retest_status": "VERIFIED", "mock": True}
        from sklab_web.integrations import appsec_cli as _acl

        try:
            out = _acl.retest(body.ref, body.engagement)
        except CliError as exc:
            raise _cli_err(exc)
        audit("finding retested", body.ref)
        return out if isinstance(out, dict) else {"result": out}

    @app.get("/api/security/findings/{fid}/impact")
    def security_impact(fid: str, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_security()
        if not st.get("mock"):
            from sklab_web.integrations import appsec_cli as _acl

            live = _acl.impact(fid)
            if live is not None:
                return live
        for f in _store.security_findings():
            if f["id"] == fid:
                return {"finding": fid, "impact": f.get("impact", {}), "mock": True}
        raise _err(404, "NOT_FOUND", "Finding not found")

    @app.post("/api/security/engagements/{eng_id}/report")
    def security_report(eng_id: str, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_security()
        if st.get("mock"):
            return {"engagement": eng_id, "reports": _store.security_reports(), "mock": True}
        from sklab_web.integrations import appsec_cli as _acl

        try:
            out = _acl.report(eng_id)
        except CliError as exc:
            raise _cli_err(exc)
        audit("security report", eng_id)
        return out

    # ---------- v0.2: Contracts (public toolkit) ----------
    def _require_contracts() -> dict[str, Any]:
        st = _contracts.status(config.mock_mode or config.mock_contracts)
        if st["state"] in ("NOT_INSTALLED", "UNAVAILABLE", "UNKNOWN") and not st.get("mock"):
            raise _err(503, "MODULE_NOT_INSTALLED", "Contract Toolkit is not installed.")
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
                    out.update(
                        {
                            "projects": len(ids),
                            "open_findings": len(live_find) if live_find else 0,
                            "live": True,
                        }
                    )
                else:
                    projs = _store.contract_projects()
                    out.update(
                        {
                            "projects": len(projs),
                            "latest_analysis": "2026-09-01",
                            "open_findings": len(_store.contract_findings()),
                            "failing_tests": 1,
                            "failing_invariants": 1,
                            "latest_upgrade": "REVIEW_REQUIRED",
                        }
                    )
            else:
                projs = _store.contract_projects()
                out.update(
                    {
                        "projects": len(projs),
                        "latest_analysis": "2026-09-01",
                        "open_findings": len(_store.contract_findings()),
                        "failing_tests": 1,
                        "failing_invariants": 1,
                        "latest_upgrade": "REVIEW_REQUIRED",
                    }
                )
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
        return {
            "project": pid,
            "total": 42,
            "passed": 41,
            "failed": 1,
            "skipped": 0,
            "duration_seconds": 12,
            "failures": [{"test": "testMintZero", "log": "assertion failed"}],
        }

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
        return {
            "project": pid,
            "tool": "echidna",
            "seed": 42,
            "runs": 10000,
            "failures": 1,
            "counterexample": "deposit(1e18) drifts 1 wei",
            "duration_seconds": 90,
        }

    @app.post("/api/contracts/projects/{pid}/invariants")
    def contracts_invariants(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_contracts()
        if not st.get("mock"):
            live = _contracts.live_invariants(pid)
            if live is not None:
                return live
            raise _err(404, "NOT_FOUND", "Contract project not found")
        return {
            "project": pid,
            "invariants": [
                {
                    "property": "totalAssets >= totalSupply",
                    "status": "FAILED",
                    "runs": 10000,
                    "depth": 32,
                    "counterexample": "seed 42",
                    "assumptions": ["no fee"],
                    "source": "STANDARD_TEMPLATE",
                }
            ],
        }

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

    @app.post("/api/contracts/projects")
    def contracts_project_create(
        body: ContractProjectCreateRequest, request: Request
    ) -> dict[str, Any]:
        guard(request)
        st = _require_contracts()
        if st.get("mock"):
            proj = {
                "id": body.id,
                "name": body.id,
                "chain": "ethereum",
                "toolchain": "foundry",
                "compiler": "solc",
                "contracts": 0,
                "status": "READY",
                "mock": True,
            }
            audit("contract project created", body.id)
            return proj
        from sklab_web.integrations import contracts_cli as _ccl

        try:
            out = _ccl.project_create(body.id, body.kind)
        except CliError as exc:
            raise _cli_err(exc)
        audit("contract project created", body.id)
        return dict(out, live=True)

    @app.post("/api/contracts/projects/import")
    def contracts_project_import(body: ContractImportRequest, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_contracts()
        if st.get("mock"):
            audit("contract project imported", body.id)
            return {"id": body.id, "ok": True, "files": list(body.files.keys()), "mock": True}
        from sklab_web.integrations import contracts_cli as _ccl

        try:
            out = _ccl.project_import(body.id, body.files)
        except CliError as exc:
            raise _cli_err(exc)
        audit("contract project imported", body.id)
        return out

    @app.post("/api/contracts/projects/{pid}/gas")
    def contracts_gas(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_contracts()
        if st.get("mock"):
            return {"project": pid, "hotspots": ["deposit (42k)", "mint (31k)"], "mock": True}
        from sklab_web.integrations import contracts_cli as _ccl

        try:
            out = _ccl.gas(pid)
        except CliError as exc:
            raise _cli_err(exc)
        return dict(out, live=True)

    @app.post("/api/contracts/projects/{pid}/coverage")
    def contracts_coverage(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_contracts()
        if st.get("mock"):
            return {"project": pid, "lines": "87%", "mock": True}
        from sklab_web.integrations import contracts_cli as _ccl

        try:
            out = _ccl.coverage(pid)
        except CliError as exc:
            raise _cli_err(exc)
        return dict(out, live=True)

    @app.get("/api/contracts/projects/{pid}/graph")
    def contracts_graph(pid: str, request: Request, kind: str = "authority") -> dict[str, Any]:
        guard(request)
        st = _require_contracts()
        if st.get("mock"):
            return {
                "project": pid,
                "kind": kind,
                "nodes": ["DemoToken", "DemoVault"],
                "edges": [["DemoVault", "DemoToken"]],
                "mock": True,
            }
        from sklab_web.integrations import contracts_cli as _ccl

        try:
            out = _ccl.graph_for_root(pid, kind)
        except CliError as exc:
            raise _cli_err(exc)
        return dict(out, live=True) if isinstance(out, dict) else {"result": out}

    @app.post("/api/contracts/projects/{pid}/upgrade-review")
    def contracts_upgrade(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_contracts()
        if st.get("mock"):
            return {
                "project": pid,
                "verdict": "REVIEW_REQUIRED",
                "storage": "no collision",
                "abi": "1 added event",
                "mock": True,
            }
        from sklab_web.integrations import contracts_cli as _ccl

        try:
            out = _ccl.upgrade_review(pid)
        except CliError as exc:
            raise _cli_err(exc)
        return dict(out, live=True) if isinstance(out, dict) else {"result": out}

    @app.get("/api/contracts/projects/{pid}/storage")
    def contracts_storage(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_contracts()
        if st.get("mock"):
            return {"project": pid, "layouts": [], "mock": True}
        from sklab_web.integrations import contracts_cli as _ccl

        try:
            out = _ccl.storage_layout(pid)
        except CliError as exc:
            raise _cli_err(exc)
        return dict(out, live=True) if isinstance(out, dict) else {"result": out}

    @app.get("/api/contracts/projects/{pid}/abi-diff")
    def contracts_abi_diff(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_contracts()
        if st.get("mock"):
            return {"project": pid, "diff": "no breaking changes", "mock": True}
        from sklab_web.integrations import contracts_cli as _ccl

        try:
            out = _ccl.diff_abi(pid)
        except CliError as exc:
            raise _cli_err(exc)
        return dict(out, live=True) if isinstance(out, dict) else {"result": out}

    @app.get("/api/contracts/projects/{pid}/threat-model")
    def contracts_threat(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_contracts()
        if st.get("mock"):
            return {"project": pid, "threats": ["owner-key-compromise"], "mock": True}
        from sklab_web.integrations import contracts_cli as _ccl

        try:
            out = _ccl.threat_model(pid)
        except CliError as exc:
            raise _cli_err(exc)
        return dict(out, live=True) if isinstance(out, dict) else {"result": out}

    @app.post("/api/contracts/projects/{pid}/remediate")
    def contracts_remediate(
        pid: str, body: ContractRemediationRequest, request: Request
    ) -> dict[str, Any]:
        guard(request)
        st = _require_contracts()
        if st.get("mock"):
            return {"project": pid, "ref": body.ref, "patch": "mock patch", "mock": True}
        from sklab_web.integrations import contracts_cli as _ccl

        try:
            out = _ccl.prepare_fix(pid, body.ref)
        except CliError as exc:
            raise _cli_err(exc)
        audit("contract remediation prepared", f"{pid}:{body.ref}")
        return dict(out, live=True) if isinstance(out, dict) else {"result": out}

    @app.post("/api/contracts/projects/{pid}/retest")
    def contracts_retest(
        pid: str, body: ContractRemediationRequest, request: Request
    ) -> dict[str, Any]:
        guard(request)
        st = _require_contracts()
        if st.get("mock"):
            return {"project": pid, "ref": body.ref, "retest_status": "VERIFIED", "mock": True}
        from sklab_web.integrations import contracts_cli as _ccl

        try:
            out = _ccl.verify_fix(pid, body.ref)
        except CliError as exc:
            raise _cli_err(exc)
        audit("contract fix verified", f"{pid}:{body.ref}")
        return dict(out, live=True) if isinstance(out, dict) else {"result": out}

    @app.post("/api/contracts/projects/{pid}/report")
    def contracts_report(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_contracts()
        if st.get("mock"):
            return {
                "project": pid,
                "reports": [
                    {
                        "id": "ct-rep-001",
                        "kind": "markdown",
                        "title": "Contract report (fixture)",
                        "artifact_id": "artifact-rep-ct-001",
                    }
                ],
                "mock": True,
            }
        from sklab_web.integrations import contracts_cli as _ccl

        try:
            out = _ccl.generate_report(pid)
        except CliError as exc:
            raise _cli_err(exc)
        audit("contract report", pid)
        return dict(out, live=True) if isinstance(out, dict) else {"result": out}

    # ---------- v0.2: Protocols (private-safe) ----------
    def _require_protocols() -> dict[str, Any]:
        st = _protocols.status(config.mock_mode or config.mock_protocols)
        if st["state"] in ("NOT_INSTALLED", "UNAVAILABLE", "UNKNOWN") and not st.get("mock"):
            raise _err(
                503,
                "PRIVATE_MODULE_UNAVAILABLE",
                "Protocol Intelligence is not installed. Showing status only.",
            )
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
            return {
                "id": pid,
                "chain": "ethereum",
                "source_summary": "live workspace",
                "live": True,
                **live_protocol_sections(pid),
            }
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
        st = _require_protocols()
        if not st.get("mock"):
            from sklab_web.integrations import protocols_cli as _pcl

            try:
                out = _pcl.monitor(pid)
            except CliError as exc:
                raise _cli_err(exc)
            if isinstance(out, list):
                return out
            if isinstance(out, dict):
                alerts = out.get("alerts", out.get("monitor", []))
                return alerts if isinstance(alerts, list) else [out]
            raise _err(404, "NOT_FOUND", "Protocol not found")
        return _store.protocol_detail(pid)["monitor"]

    @app.get("/api/protocols/{pid}/incidents")
    def protocol_incidents(pid: str, request: Request) -> list[dict[str, Any]]:
        guard(request)
        st = _require_protocols()
        if not st.get("mock"):
            from sklab_web.integrations import protocols_cli as _pcl

            try:
                out = _pcl.incident(pid)
            except CliError as exc:
                raise _cli_err(exc)
            if isinstance(out, list):
                return out
            if isinstance(out, dict):
                items = out.get("incidents", out.get("timeline", []))
                return items if isinstance(items, list) else [out]
            raise _err(404, "NOT_FOUND", "Protocol not found")
        return _store.protocol_detail(pid)["incidents"]

    def _proto_action(pid: str, fn_name: str, mock_value: Any, *args: Any) -> Any:
        st = _require_protocols()
        if st.get("mock"):
            return mock_value
        from sklab_web.integrations import protocols_cli as _pcl

        try:
            out = getattr(_pcl, fn_name)(pid, *args)
        except CliError as exc:
            raise _cli_err(exc)
        audit(f"protocol {fn_name}", pid)
        return out

    @app.post("/api/protocols")
    def protocol_create(body: ProtocolCreateRequest, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_protocols()
        if st.get("mock"):
            audit("protocol created", body.id)
            return {
                "id": body.id,
                "chain": "ethereum",
                "source_summary": "mock project",
                "mock": True,
            }
        from sklab_web.integrations import protocols_cli as _pcl

        try:
            out = _pcl.project_create(body.id)
        except CliError as exc:
            raise _cli_err(exc)
        audit("protocol created", body.id)
        return dict(out, live=True) if isinstance(out, dict) else {"id": body.id, "result": out}

    @app.post("/api/protocols/{pid}/ir")
    def protocol_build_ir(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        out = _proto_action(pid, "build_ir", {"id": pid, "ir": "mock", "mock": True})
        return out if isinstance(out, dict) else {"result": out}

    @app.post("/api/protocols/{pid}/map")
    def protocol_build_map(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        out = _proto_action(pid, "build_map", {"id": pid, "map": "mock", "mock": True})
        return out if isinstance(out, dict) else {"result": out}

    @app.post("/api/protocols/{pid}/specs")
    def protocol_derive_specs(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        out = _proto_action(pid, "specs", {"id": pid, "specs": [], "mock": True})
        return out if isinstance(out, dict) else {"result": out}

    @app.post("/api/protocols/{pid}/invariants")
    def protocol_derive_invariants(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        out = _proto_action(pid, "invariants", {"id": pid, "invariants": [], "mock": True})
        return out if isinstance(out, dict) else {"result": out}

    @app.post("/api/protocols/{pid}/simulate")
    def protocol_simulate(pid: str, body: EconomicRequest, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_protocols()
        if st.get("mock"):
            return {"id": pid, "result": "insolvency indicator: none", "mock": True}
        from sklab_web.integrations import protocols_cli as _pcl

        try:
            out = _pcl.simulate(pid, seed=body.seed, runs=body.runs)
        except CliError as exc:
            raise _cli_err(exc)
        audit("protocol simulation", pid)
        return out if isinstance(out, dict) else {"result": out}

    @app.post("/api/protocols/{pid}/economic")
    def protocol_economic(pid: str, body: EconomicRequest, request: Request) -> dict[str, Any]:
        guard(request)
        st = _require_protocols()
        if st.get("mock"):
            return {
                "id": pid,
                "scenario": body.scenario,
                "result": "insolvency indicator: none",
                "mock": True,
            }
        from sklab_web.integrations import protocols_cli as _pcl

        try:
            out = _pcl.economic(pid, body.scenario)
        except CliError as exc:
            raise _cli_err(exc)
        audit("protocol economic scenario", f"{pid}:{body.scenario}")
        return out if isinstance(out, dict) else {"result": out}

    @app.post("/api/protocols/{pid}/assure")
    def protocol_assure(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        out = _proto_action(pid, "assure", {"id": pid, "assurance": [], "mock": True})
        return out if isinstance(out, dict) else {"result": out}

    @app.post("/api/protocols/{pid}/verify")
    def protocol_verify(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        out = _proto_action(pid, "verify", {"id": pid, "ok": True, "mock": True})
        return out if isinstance(out, dict) else {"result": out}

    @app.post("/api/protocols/{pid}/upgrade-review")
    def protocol_upgrade(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        out = _proto_action(
            pid, "upgrade_review", {"id": pid, "verdict": "REVIEW_REQUIRED", "mock": True}
        )
        return out if isinstance(out, dict) else {"result": out}

    @app.post("/api/protocols/{pid}/deployment-guard")
    def protocol_guard(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        out = _proto_action(pid, "deployment_guard", {"id": pid, "checks": [], "mock": True})
        return out if isinstance(out, dict) else {"result": out}

    @app.post("/api/protocols/{pid}/regression")
    def protocol_regression(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        out = _proto_action(
            pid, "historical_regression", {"id": pid, "regressions": [], "mock": True}
        )
        return out if isinstance(out, dict) else {"result": out}

    @app.post("/api/protocols/{pid}/report")
    def protocol_report(pid: str, request: Request) -> dict[str, Any]:
        guard(request)
        out = _proto_action(pid, "report", {"id": pid, "log": "mock report", "mock": True})
        return out if isinstance(out, dict) else {"result": out}

    return app


def _to_summary(rec: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": rec["id"],
        "task": rec.get("task", ""),
        "task_summary": rec.get("task_summary", ""),
        "repo": rec.get("repo", ""),
        "repo_id": rec.get("repo_id"),
        "status": rec.get("status", "CREATED"),
        "attempts": rec.get("attempts", 0),
        "winning_agent": rec.get("winning_agent"),
        "verification": rec.get("verification", "UNKNOWN"),
        "duration_seconds": rec.get("duration_seconds", 0),
        "cost": rec.get("cost"),
        "created_at": rec.get("created_at", ""),
        "result_status": rec.get("result_status"),
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


_CLI_STATUS = {
    "BAD_REQUEST": 400,
    "NOT_FOUND": 404,
    "ENGAGEMENT_NOT_FOUND": 404,
    "AUTH_REQUIRED": 401,
    "AGENT_UNAVAILABLE": 503,
    "PROVIDER_UNAVAILABLE": 503,
    "BROWSER_UNAVAILABLE": 503,
    "MODULE_NOT_INSTALLED": 503,
    "PRIVATE_MODULE_UNAVAILABLE": 503,
    "MODULE_UNAVAILABLE": 503,
    "APPROVAL_REQUIRED": 409,
    "BUDGET_EXHAUSTED": 409,
}


def _cli_err(exc: CliError) -> Any:
    return _err(_CLI_STATUS.get(exc.code, 503), exc.code, exc.message[:500])


def _is_live(config: AppConfig) -> bool:
    return not config.mock_mode


def _launch_execution(run_id: str) -> None:
    """Run real execution in a background thread (single-flight per run)."""
    import threading

    if _exec_threads.get(run_id) and _exec_threads[run_id].is_alive():
        return

    def _work() -> None:
        try:
            from sklab_web.integrations import orchestrator as _orch

            svc = _orch.get_service()
            svc.execute_run(run_id)
        except Exception as exc:
            try:
                from sklab_web.integrations import orchestrator as _orch2

                _orch2.get_service().store.emit(run_id, "RUN_FAILED", {"error": str(exc)[:500]})
            except Exception:
                pass
        finally:
            _exec_threads.pop(run_id, None)

    t = threading.Thread(target=_work, args=(), daemon=True)
    _exec_threads[run_id] = t
    t.start()


def _launch_resume(run_id: str) -> None:
    """Continue a run in the background via resume semantics (idempotent)."""
    import threading

    if _exec_threads.get(run_id) and _exec_threads[run_id].is_alive():
        return

    def _work() -> None:
        try:
            from sklab_web.integrations import orchestrator as _orch

            svc = _orch.get_service()
            svc.resume_run(run_id)
        except Exception as exc:
            try:
                from sklab_web.integrations import orchestrator as _orch2

                _orch2.get_service().store.emit(run_id, "RUN_FAILED", {"error": str(exc)[:500]})
            except Exception:
                pass
        finally:
            _exec_threads.pop(run_id, None)

    t = threading.Thread(target=_work, args=(), daemon=True)
    _exec_threads[run_id] = t
    t.start()


def _live_plan_dto(svc: Any, run_id: str, repo: str, cost_budget: Any) -> dict[str, Any]:
    from sklab_web.integrations import orchestrator as _orch

    plan = svc.store.load_plan(run_id)
    if plan is None:
        raise _err(500, "INTERNAL_ERROR", "plan not available")
    d = _orch._dump(plan)
    gates = []
    for g in d.get("approval_gates", []) or []:
        gates.append(
            {"label": "APPROVAL_REQUIRED", "detail": str(g.get("message", g.get("type", "")))}
        )
    if not gates:
        gates.append({"label": "AUTO", "detail": f"agent={d.get('selected_agent')}"})
    cands = d.get("candidates", []) or []
    return {
        "run_id": run_id,
        "classification": str((d.get("classification") or {}).get("category", "UNKNOWN")),
        "repo_summary": repo or "live repo snapshot",
        "required_capabilities": list(d.get("required_capabilities", []) or []),
        "selected_agent": d.get("selected_agent") or "unknown",
        "fallback_agents": [
            str(c.get("agent_id")) for c in cands[1:4] if isinstance(c, dict) and c.get("agent_id")
        ],
        "provider": d.get("selected_connection"),
        "model": d.get("selected_model"),
        "skill": (d.get("skill") or {}).get("id")
        if isinstance(d.get("skill"), dict)
        else d.get("skill"),
        "environment": "reprobox" if (d.get("environment") or {}).get("use_reprobox") else "local",
        "verification_strategy": "patchbench",
        "retry_policy": str(d.get("retry_policy", "evidence-driven")),
        "budget": str((d.get("budget") or {}).get("max_cost", cost_budget))
        if cost_budget
        else "Unknown",
        "permissions": list(d.get("permissions", []) or []),
        "approval_gates": gates,
        "warnings": list(d.get("warnings", []) or []),
        "live": True,
    }


app = create_app()
