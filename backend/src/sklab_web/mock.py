"""Deterministic mock store: fixtures + fake run event simulator.

Mock scenarios: idle, active-success, retrying, approval-required,
blocked-quota, failed-verification, verified-success,
provider-auth-required, agent-unavailable.
"""
from __future__ import annotations

import itertools
import threading
import time
from datetime import UTC, datetime
from typing import Any

from sklab_web.models import (
    RunEvent,
)

MOCK_RUN_SCRIPT: list[tuple[str, str, str]] = [
    ("INSPECTION_STARTED", "stdout", "Inspecting repository snapshot..."),
    ("INSPECTION_COMPLETED", "stdout", "Repo signals: python, fastapi. Fingerprint r-abc123"),
    ("PLAN_CREATED", "stdout", "Plan created: BUG_FIX/HIGH. Agent Hermes selected (free)."),
    ("AGENT_SELECTED", "stdout", "Agent selected: hermes (free, auth ready)"),
    ("PROVIDER_SELECTED", "stdout", "Provider selected: local (free, no key required)"),
    ("WORKSPACE_READY", "stdout", "Workspace ready in ReproBox env reprobox-py312"),
    ("ATTEMPT_STARTED", "stdout", "Attempt 1 started (hermes)"),
    ("AGENT_EVENT", "stdout", "Reading src/auth.py ..."),
    ("AGENT_EVENT", "stdout", "Applying minimal patch to fix token expiry check"),
    ("AGENT_EVENT", "stderr", "warning: unused import in legacy helper (non-fatal)"),
    ("PATCH_CAPTURED", "stdout", "Patch captured: 2 files, +24/-6 fp=patch-111"),
    ("VERIFICATION_STARTED", "stdout", "PatchBench verification started"),
    ("VERIFICATION_COMPLETED", "stdout", "REJECT: new regression in test_auth_timeout"),
    ("RETRY_DECIDED", "stdout", "Retry decided: same agent + exact verifier evidence"),
    ("ATTEMPT_STARTED", "stdout", "Attempt 2 started (hermes)"),
    ("AGENT_EVENT", "stdout", "Fixing regression with verifier evidence attached"),
    ("PATCH_CAPTURED", "stdout", "Patch captured: 1 file, +8/-2 fp=patch-222"),
    ("VERIFICATION_STARTED", "stdout", "PatchBench verification started"),
    ("VERIFICATION_COMPLETED", "stdout", "ACCEPT 94/100, 0 regressions"),
    ("RUN_COMPLETED", "stdout", "Run completed: VERIFIED_SUCCESS"),
]

FINAL_PATCH = """diff --git a/src/auth.py b/src/auth.py
index 111..222 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -12,7 +12,9 @@ def validate_token(tok, now):
-    return tok.exp > now
+    if not tok or not tok.exp:
+        return False
+    return tok.exp > now + 30
"""


class MockStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._seq = itertools.count(1)
        self.runs: dict[str, dict[str, Any]] = {}
        self.events: dict[str, list[RunEvent]] = {}
        self.audit: list[dict[str, str]] = []
        self.settings: dict[str, Any] = {
            "default_routing_policy": "safe",
            "max_attempts": 3,
            "default_timeout_seconds": 1200,
            "default_budget": None,
            "require_approval_for_paid": True,
            "reprobox_default": True,
            "verification_default": True,
            "auto_apply_patch": False,
            "auto_push": False,
            "skill_auto_install": "OFF",
            "allowed_repo_roots": ["/srv/sklab/repos"],
        }
        self.providers: list[dict[str, Any]] = [
            {"id": "local", "label": "Local", "type": "local", "status": "READY",
             "default_model": "local-fixture", "last_validated": None, "enabled": True},
            {"id": "openai", "label": "OpenAI", "type": "api_key", "status": "NOT_CONFIGURED",
             "default_model": "gpt-4o-mini", "last_validated": None, "enabled": True},
            {"id": "anthropic", "label": "Anthropic", "type": "api_key", "status": "NOT_CONFIGURED",
             "default_model": "claude-3-5-sonnet", "last_validated": None, "enabled": True},
        ]
        self._seed_history()
        self._sec_engs: list[dict[str, Any]] | None = None

    # ---------- seed ----------
    def _seed_history(self) -> None:
        r = self._new_run_record(
            task="Fix flaky auth timeout test",
            repo="/srv/sklab/repos/demo",
            status="COMPLETED",
            result_status="VERIFIED_SUCCESS",
            agent="hermes",
            verification="ACCEPT",
        )
        r["attempt_details"] = [
            {"index": 1, "agent": "hermes", "model": "local-fixture",
             "duration_seconds": 42, "status": "FAILED",
             "patch_fingerprint": "patch-111", "verifier_verdict": "REJECT",
             "verifier_score": 61, "cost": "Unknown", "retry_reason": "New regression in test_auth_timeout"},
            {"index": 2, "agent": "hermes", "model": "local-fixture",
             "duration_seconds": 31, "status": "COMPLETED",
             "patch_fingerprint": "patch-222", "verifier_verdict": "ACCEPT",
             "verifier_score": 94, "cost": "Unknown", "retry_reason": None},
        ]
        r["verification_detail"] = {
            "verdict": "ACCEPT", "score": 94, "regressions": 0,
            "checks": [
                {"name": "Tests", "status": "PASS"},
                {"name": "Typecheck", "status": "PASS"},
                {"name": "Build", "status": "PASS"},
            ],
            "warnings": [], "scope_warnings": [],
            "duration_seconds": 12, "environment_fingerprint": "env-py312-abc",
        }
        r["patch"] = FINAL_PATCH

    def _new_run_record(self, task: str, repo: str, status: str,
                        result_status: str | None, agent: str,
                        verification: str) -> dict[str, Any]:
        rid = f"run-{next(self._seq):04d}"
        now = datetime.now(UTC).isoformat()
        rec: dict[str, Any] = {
            "id": rid, "task": task, "task_summary": task[:80], "repo": repo,
            "repo_id": "demo", "status": status, "attempts": 1,
            "winning_agent": agent, "verification": verification,
            "duration_seconds": 73, "cost": "Unknown", "created_at": now,
            "result_status": result_status, "agent": agent, "model": "local-fixture",
            "provider": "local", "environment": "reprobox-py312",
            "attempt_details": [], "verification_detail": None,
            "patch": None, "warnings": [], "approval": None,
            "fingerprints": {"repo": "r-abc123", "env": "env-py312-abc"},
        }
        with self._lock:
            self.runs[rid] = rec
            self.events[rid] = []
        return rec

    # ---------- runs ----------
    def create_run(self, payload: dict[str, Any], scenario: str = "success") -> dict[str, Any]:
        rec = self._new_run_record(
            task=payload.get("task", ""),
            repo=payload.get("repository", ""),
            status="RUNNING_AGENT",
            result_status=None,
            agent=payload.get("agent") or "hermes",
            verification="PENDING",
        )
        # paid-approval scenario: immediately gate
        if scenario == "approval" or (payload.get("model") or "").startswith("paid-"):
            rec["status"] = "WAITING_FOR_APPROVAL"
            rec["approval"] = {
                "reason": "Paid model required",
                "budget": "$0.50",
                "agent": rec["agent"],
                "provider": payload.get("provider") or "openai",
            }
            with self._lock:
                self.events[rec["id"]].append(RunEvent(
                    seq=1, type="APPROVAL_REQUIRED", ts=datetime.now(UTC).isoformat(),
                    message="Paid model required. Estimated/max budget: $0.50",
                    data=dict(rec["approval"])))
            return rec
        if scenario == "blocked":
            rec["status"] = "BLOCKED"
        # launch deterministic simulator thread
        t = threading.Thread(target=self._simulate, args=(rec["id"], scenario), daemon=True)
        t.start()
        return rec

    def _simulate(self, run_id: str, scenario: str) -> None:
        import os as _os

        try:
            step = max(0.005, float(_os.environ.get("SKLAB_MOCK_STEP_MS", "50")) / 1000.0)
        except ValueError:
            step = 0.05
        script = list(MOCK_RUN_SCRIPT)
        if scenario == "fail":
            script = [s for s in script if s[0] not in ("RETRY_DECIDED",)] + [
                ("RUN_FAILED", "stdout", "Run failed: verification failed")]
        for etype, stream, msg in script:
            if self._is_cancelled(run_id):
                return
            if scenario == "blocked" and etype == "ATTEMPT_STARTED":
                self._push(run_id, "RUN_FAILED", "stderr", "Blocked: provider quota exhausted")
                self._set(run_id, status="BLOCKED")
                return
            time.sleep(step)
            if self._is_cancelled(run_id):
                return
            self._push(run_id, etype, stream, msg)
            self._apply_progress(run_id, etype)
        if not self._is_cancelled(run_id):
            self._finalize(run_id, scenario)

    def _is_cancelled(self, run_id: str) -> bool:
        with self._lock:
            rec = self.runs.get(run_id)
            return bool(rec) and rec.get("status") == "CANCELLED"

    def _push(self, run_id: str, etype: str, stream: str, message: str) -> int:
        with self._lock:
            evs = self.events.setdefault(run_id, [])
            seq = len(evs) + 1
            evs.append(RunEvent(seq=seq, type=etype, ts=datetime.now(UTC).isoformat(),
                                message=message, stream=stream, data={}))
            return seq

    def _set(self, run_id: str, **kw: Any) -> None:
        with self._lock:
            if run_id in self.runs:
                self.runs[run_id].update(kw)

    def _apply_progress(self, run_id: str, etype: str) -> None:
        mapping = {
            "INSPECTION_STARTED": "INSPECTING",
            "PLAN_CREATED": "PLANNING",
            "WORKSPACE_READY": "PREPARING",
            "ATTEMPT_STARTED": "RUNNING_AGENT",
            "PATCH_CAPTURED": "CAPTURING_PATCH",
            "VERIFICATION_STARTED": "VERIFYING",
            "RETRY_DECIDED": "RETRYING",
        }
        if etype in mapping:
            self._set(run_id, status=mapping[etype])

    def _finalize(self, run_id: str, scenario: str) -> None:
        if scenario == "fail":
            self._set(run_id, status="FAILED", result_status="FAILED",
                      verification="REJECT", attempts=1)
            return
        self._set(run_id, status="COMPLETED", result_status="VERIFIED_SUCCESS",
                   verification="ACCEPT", attempts=2, winning_agent="hermes",
                   patch=FINAL_PATCH,
                   verification_detail={
                       "verdict": "ACCEPT", "score": 94, "regressions": 0,
                       "checks": [{"name": "Tests", "status": "PASS"},
                                  {"name": "Typecheck", "status": "PASS"},
                                  {"name": "Build", "status": "PASS"}],
                       "warnings": [], "scope_warnings": [],
                       "duration_seconds": 12, "environment_fingerprint": "env-py312-abc"},
                   attempt_details=[
                       {"index": 1, "agent": "hermes", "model": "local-fixture",
                        "duration_seconds": 42, "status": "FAILED",
                        "patch_fingerprint": "patch-111", "verifier_verdict": "REJECT",
                        "verifier_score": 61, "cost": "Unknown",
                        "retry_reason": "New regression in test_auth_timeout"},
                       {"index": 2, "agent": "hermes", "model": "local-fixture",
                        "duration_seconds": 31, "status": "COMPLETED",
                        "patch_fingerprint": "patch-222", "verifier_verdict": "ACCEPT",
                        "verifier_score": 94, "cost": "Unknown", "retry_reason": None}],
                   fingerprints={"repo": "r-abc123", "env": "env-py312-abc", "patch": "patch-222"})

    # ---------- static fixtures ----------
    def repos(self) -> list[dict[str, Any]]:
        return [{
            "id": "demo", "name": "demo", "path": "/srv/sklab/repos/demo",
            "branch": "main", "dirty": False, "stack": ["python", "fastapi"],
            "last_run_id": next(iter(self.runs), None), "warnings": [],
            "context_status": "READY"}]

    def agents(self) -> list[dict[str, Any]]:
        caps = {"Files Read": "yes", "Files Write": "yes", "Shell": "yes",
                "MCP": "unknown", "Skills": "yes", "Sessions": "yes",
                "Resume": "yes", "Streaming": "yes", "Model Selection": "yes"}
        return [
            {"id": "hermes", "installed": True, "version": "0.1.0", "auth_ready": True,
             "capabilities": caps, "supports_model_selection": True, "sessions": True,
             "resume": True, "streaming": True, "status": "READY", "cost_class": "free"},
            {"id": "zero", "installed": True, "version": "0.1.0", "auth_ready": True,
             "capabilities": caps, "supports_model_selection": True, "sessions": True,
             "resume": True, "streaming": True, "status": "READY", "cost_class": "free"},
            {"id": "opencode", "installed": False, "version": None, "auth_ready": False,
             "capabilities": {}, "supports_model_selection": True, "sessions": False,
             "resume": False, "streaming": True, "status": "UNAVAILABLE", "cost_class": "unknown"},
            {"id": "codex", "installed": False, "version": None, "auth_ready": False,
             "capabilities": {}, "supports_model_selection": True, "sessions": False,
             "resume": False, "streaming": False, "status": "UNAVAILABLE", "cost_class": "high"},
            {"id": "claude-code", "installed": False, "version": None, "auth_ready": False,
             "capabilities": {}, "supports_model_selection": True, "sessions": False,
             "resume": False, "streaming": False, "status": "UNAVAILABLE", "cost_class": "high"},
            {"id": "gemini-cli", "installed": False, "version": None, "auth_ready": False,
             "capabilities": {}, "supports_model_selection": True, "sessions": False,
             "resume": False, "streaming": False, "status": "UNAVAILABLE", "cost_class": "unknown"},
            {"id": "generic", "installed": True, "version": "0.1.0", "auth_ready": False,
             "capabilities": {"Files Read": "yes", "Files Write": "unknown"},
             "supports_model_selection": False, "sessions": False, "resume": False,
             "streaming": False, "status": "DEGRADED", "cost_class": "unknown"},
        ]

    def environments(self) -> list[dict[str, Any]]:
        return [{
            "name": "reprobox-py312", "executor": "docker", "fingerprint": "env-py312-abc",
            "image": "sklab/reprobox:py312", "python_version": "3.12",
            "node_version": "22", "network_mode": "none", "lock_status": "locked",
            "warnings": [], "last_verified": datetime.now(UTC).isoformat()}]

    def benchmarks(self) -> list[dict[str, Any]]:
        return [{
            "id": "bench-auth-001", "title": "Fix auth timeout regression",
            "stack": "python", "category": "BUG_FIX", "difficulty": "easy",
            "version": "0.1.0", "fingerprint": "b-001"}]

    def skills(self) -> list[dict[str, Any]]:
        return [
            {"id": "tdd", "enabled": True, "category": "workflow", "source": "builtin",
             "trust_level": "verified", "permissions": ["read", "write"], "version": "0.1.0"},
            {"id": "safe-refactor", "enabled": True, "category": "workflow",
             "source": "builtin", "trust_level": "verified",
             "permissions": ["read"], "version": "0.1.0"},
        ]

    def codetrials(self) -> list[dict[str, Any]]:
        return [{"id": "ct-001", "task": "auth timeout fix",
                 "agents": ["hermes", "zero"], "winner": "hermes",
                 "tie": False, "verified": True, "cost": "Unknown"}]

    def prompt_experiments(self) -> list[dict[str, Any]]:
        return [{"id": "pb-001", "name": "timeout-fix-prompts", "variants": 3,
                 "success_rate": 0.66, "median_score": 88, "winner": "v2"}]

    # ---------------- v0.2: Security fixtures ----------------
    def security_overview(self) -> dict[str, Any]:
        return {
            "status": {"state": "READY", "version": "mock-0.2.0"},
            "active_engagement": "eng-demo",
            "target_scope": "local fixture target (2 hosts, 14 routes)",
            "browser": {"engine": "chromium", "mode": "headless", "url": "http://localhost:3000/",
                        "flow": "login→profile", "title": "Fixture App", "role": "user",
                        "captured_requests": 128},
            "api_endpoints": 14, "open_findings": 3, "verified_fixes": 1,
            "latest_simulation": "ROLE_BOUNDARY_CHECK", "latest_report": "rep-sec-001",
        }

    def security_engagements(self) -> list[dict[str, Any]]:
        if self._sec_engs is None:
            self._sec_engs = [{
                "id": "eng-demo", "name": "Local fixture audit", "status": "ACTIVE",
                "scope_summary": "2 hosts, 14 routes, roles guest/user/admin",
                "created_at": "2026-08-01T00:00:00+00:00", "last_run": "2026-09-01T00:00:00+00:00",
                "finding_count": 3, "report_status": "READY",
            }]
        return self._sec_engs

    def add_security_engagement(self, eng: dict[str, Any]) -> dict[str, Any]:
        engs = [e for e in self.security_engagements() if e["id"] != eng["id"]] + [eng]
        self._sec_engs = engs
        return eng

    def reset_ephemeral(self) -> None:
        """Drop request-created fixtures (fresh app instances start deterministic)."""
        self._sec_engs = None

    def security_traffic(self) -> list[dict[str, Any]]:
        return [
            {"ts": "2026-09-01T00:00:01+00:00", "method": "GET", "host": "fixture.local",
             "path": "/api/profile", "status": 200, "kind": "REST", "auth": "bearer-ref",
             "duration_ms": 42, "flow": "login→profile"},
            {"ts": "2026-09-01T00:00:02+00:00", "method": "GET", "host": "fixture.local",
             "path": "/api/admin", "status": 403, "kind": "REST", "auth": "bearer-ref",
             "duration_ms": 18, "flow": "role-check"},
            {"ts": "2026-09-01T00:00:03+00:00", "method": "POST", "host": "fixture.local",
             "path": "/graphql", "status": 200, "kind": "GraphQL", "auth": "bearer-ref",
             "duration_ms": 61, "flow": "data-fetch"},
        ]

    def security_api_map(self) -> list[dict[str, Any]]:
        return [
            {"host": "fixture.local", "route": "/api/profile", "method": "GET",
             "auth": "required", "roles": {"Guest": 401, "User": 200, "Manager": 200, "Admin": 200}},
            {"host": "fixture.local", "route": "/api/admin", "method": "GET",
             "auth": "required", "roles": {"Guest": 401, "User": 403, "Manager": 403, "Admin": 200}},
        ]

    def security_findings(self) -> list[dict[str, Any]]:
        return [
            {"id": "sec-001", "source": "appsec", "severity": "HIGH", "confidence": "HIGH",
             "title": "Role boundary inconsistency on /api/admin", "endpoint": "GET /api/admin",
             "flow": "role-check", "status": "OPEN", "evidence_ref": "ev-sec-001",
             "retest_status": "NOT_RUN", "description": "Manager role returns 403 while admin returns 200; verify intended policy.",
             "remediation": "Enforce server-side role check; add regression test.",
             "impact": {"data_confidentiality": "MEDIUM", "privilege_impact": "MEDIUM",
                        "account_impact": "LOW", "service_impact": "NONE",
                        "cross_tenant_impact": "NONE", "credential_exposure": "NONE",
                        "environment_scope": "LOCAL", "data_integrity": "LOW",
                        "persistence_possible": "NONE"}},
            {"id": "sec-002", "source": "appsec", "severity": "MEDIUM", "confidence": "MEDIUM",
             "title": "CORS policy permissive on fixture origin", "endpoint": "GET /api/profile",
             "flow": "login→profile", "status": "CONFIRMED", "evidence_ref": "ev-sec-002",
             "retest_status": "NOT_RUN", "description": "Fixture allows extra origin; tighten allow-list.",
             "remediation": "Restrict Access-Control-Allow-Origin to trusted origins.",
             "impact": {"data_confidentiality": "LOW", "privilege_impact": "NONE",
                        "account_impact": "NONE", "service_impact": "NONE",
                        "cross_tenant_impact": "NONE", "credential_exposure": "NONE",
                        "environment_scope": "LOCAL", "data_integrity": "NONE",
                        "persistence_possible": "NONE"}},
            {"id": "sec-003", "source": "appsec", "severity": "LOW", "confidence": "HIGH",
             "title": "Missing cache-control on profile API", "endpoint": "GET /api/profile",
             "flow": "login→profile", "status": "FIXED_VERIFIED", "evidence_ref": "ev-sec-003",
             "retest_status": "VERIFIED", "description": "Cache headers added and retested.",
             "remediation": "Set Cache-Control: no-store on authenticated responses.",
             "impact": {"data_confidentiality": "LOW", "privilege_impact": "NONE",
                        "account_impact": "NONE", "service_impact": "NONE",
                        "cross_tenant_impact": "NONE", "credential_exposure": "NONE",
                        "environment_scope": "LOCAL", "data_integrity": "NONE",
                        "persistence_possible": "NONE"}},
        ]

    def security_simulations(self) -> list[dict[str, Any]]:
        sims = ["AUTH_REQUIRED_CHECK", "ROLE_BOUNDARY_CHECK", "OBJECT_ACCESS_CHECK",
                "CORS_POLICY_CHECK", "RATE_LIMIT_RESILIENCE_CHECK", "ERROR_LEAK_CHECK",
                "HEADER_POLICY_CHECK", "CACHE_CONTROL_CHECK"]
        return [{"id": f"sim-{i:03d}", "simulation": s, "target": "GET /api/admin",
                 "role": "user", "result": "PASS" if i % 3 else "FINDING",
                 "requests": 6 + i, "duration_ms": 120 + i * 10,
                 "impact": "LOW", "evidence_ref": f"ev-sim-{i:03d}"}
                for i, s in enumerate(sims, 1)]

    def security_reports(self) -> list[dict[str, Any]]:
        return [
            {"id": "rep-sec-001", "kind": "markdown", "title": "Executive summary (fixture)",
             "created_at": "2026-09-01T00:00:00+00:00", "artifact_id": "artifact-rep-sec-001"},
            {"id": "rep-sec-002", "kind": "json", "title": "Findings JSON (fixture)",
             "created_at": "2026-09-01T00:00:00+00:00", "artifact_id": "artifact-rep-sec-002"},
        ]

    # ---------------- v0.2: Contracts fixtures ----------------
    def contract_projects(self) -> list[dict[str, Any]]:
        return [{
            "id": "proj-demo", "name": "demo-token", "chain": "ethereum",
            "toolchain": "foundry", "compiler": "solc 0.8.24",
            "contracts": 3, "standards": ["ERC-20", "Ownable"],
            "authorities": ["Owner"], "last_build": "2026-09-01T00:00:00+00:00",
            "last_analysis": "2026-09-01T00:00:00+00:00", "status": "READY",
        }]

    def contract_inventory(self) -> list[dict[str, Any]]:
        return [
            {"id": "c-token", "name": "DemoToken", "source": "src/DemoToken.sol",
             "kind": "contract", "standard": "ERC-20", "upgradeability": "UUPS",
             "authorities": ["Owner"], "functions": 8},
            {"id": "c-vault", "name": "DemoVault", "source": "src/DemoVault.sol",
             "kind": "contract", "standard": "ERC-4626", "upgradeability": "NON_UPGRADEABLE",
             "authorities": ["Owner", "Keeper"], "functions": 6},
        ]

    def contract_findings(self) -> list[dict[str, Any]]:
        return [
            {"id": "ct-001", "source": "slither", "severity": "MEDIUM", "confidence": "HIGH",
             "title": "Missing zero-address check in mint", "contract": "DemoToken",
             "function": "mint", "status": "OPEN", "evidence_ref": "ev-ct-001",
             "description": "mint() does not reject address(0).", "remediation": "Require to != address(0).",
             "impact": {}},
            {"id": "ct-002", "source": "echidna", "severity": "HIGH", "confidence": "MEDIUM",
             "title": "Fuzz counterexample: share-price drift", "contract": "DemoVault",
             "function": "deposit", "status": "CONFIRMED", "evidence_ref": "ev-ct-002",
             "description": "Bounded fuzz found accounting drift seed 42.", "remediation": "Fix rounding order.",
             "impact": {}},
        ]

    def contract_tools(self) -> list[dict[str, Any]]:
        tools = ["Foundry", "Hardhat", "solc", "Slither", "Echidna", "Mythril", "Halmos", "Anvil"]
        return [{"id": t.lower(), "installed": i < 4, "version": "mock-1.0" if i < 4 else None,
                 "status": "READY" if i < 4 else "NOT_INSTALLED",
                 "capabilities": ["compile", "test"] if t == "Foundry" else ["analyze"]}
                for i, t in enumerate(tools)]

    # ---------------- v0.2: Protocols fixtures ----------------
    def protocol_list(self) -> list[dict[str, Any]]:
        return [{
            "id": "proto-demo", "chain": "ethereum",
            "source_summary": "2 contracts + 1 oracle (synthetic fixture)",
            "assurance_freshness": "STALE", "open_findings": 2,
            "critical_authorities": 1, "monitored": True,
            "latest_upgrade": "v1.2.0", "active_alerts": 1,
        }]

    def protocol_detail(self, pid: str) -> dict[str, Any]:
        base = self.protocol_list()[0].copy()
        base["id"] = pid
        base.update({
            "map": {"nodes": ["DemoToken", "DemoVault", "PriceOracle"],
                    "edges": [["DemoVault", "DemoToken"], ["DemoVault", "PriceOracle"]]},
            "assets": [{"asset": "USDC", "source": "User", "destination": "DemoVault",
                        "trigger": "deposit", "authority": "User", "constraint": "share math"}],
            "authorities": [{"authority": "Owner", "capability": "upgrade",
                             "target": "DemoVault", "direct": True, "evidence": "proxy admin",
                             "confidence": "HIGH", "blast_radius": "HIGH"}],
            "dependencies": [{"dependency": "PriceOracle", "type": "PRICE", "protocol": "demo-oracle",
                              "role": "valuation", "trust": "single source", "criticality": "HIGH"}],
            "specs": [{"statement": "deposit mints proportional shares", "source": "code+test",
                       "confidence": "HIGH", "machine_checkable": True, "assumptions": ["no fee"],
                       "status": "VALIDATED"}],
            "invariants": [{"invariant": "totalAssets >= totalSupply", "status": "BOUNDED_VERIFIED",
                            "source": "STANDARD_TEMPLATE", "tool": "echidna",
                            "assumptions": ["no rebase"], "last_verified": "2026-09-01",
                            "evidence": "ev-pi-001"}],
            "evidence": [{"from": "Finding ct-002", "to": "Invariant totalAssets",
                          "via": "fuzz seed 42"}],
            "economic": {"config": "price -30%, liquidity -50%", "result": "insolvency indicator: none",
                         "bad_debt": "0", "scenarios": ["Price -30%", "Large withdrawal"]},
            "upgrade": {"verdict": "REVIEW_REQUIRED", "storage": "no collision",
                        "abi": "1 added event", "permissions": "unchanged"},
            "guard": [{"item": "proxy admin", "state": "READY"}, {"item": "timelock", "state": "MISSING"}],
            "monitor": [{"id": "al-001", "kind": "ORACLE_CHANGED", "severity": "HIGH",
                         "message": "Oracle address changed (fixture)", "ts": "2026-09-01T00:00:00+00:00"}],
            "incidents": [{"id": "inc-001", "title": "Synthetic oracle delay",
                           "timeline": ["oracle stale", "alert fired", "guard paused deposits"],
                           "blast_radius": "MEDIUM"}],
            "assurance": [
                {"check": "Compilation", "state": "VERIFIED", "detail": "solc 0.8.24"},
                {"check": "Unit Tests", "state": "VERIFIED", "detail": "42/42"},
                {"check": "Static Analysis", "state": "VERIFIED", "detail": "slither"},
                {"check": "Fuzz Coverage", "state": "PARTIAL", "detail": "bounded 10k runs"},
                {"check": "Critical Invariants", "state": "VERIFIED", "detail": "3/3 bounded"},
                {"check": "Formal Proofs", "state": "PARTIAL", "detail": "1/2 halmos"},
                {"check": "Upgrade Safety", "state": "VERIFIED", "detail": "no storage collision"},
                {"check": "Economic Model", "state": "PARTIAL", "detail": "2 scenarios"},
                {"check": "External Dependencies", "state": "INCONCLUSIVE", "detail": "oracle single-source"},
                {"check": "On-chain Config", "state": "VERIFIED", "detail": "chain-id 1"},
            ],
            "freshness": {"stale": True, "reason": "Oracle config changed",
                          "action": "Re-run affected checks"},
        })
        return base
