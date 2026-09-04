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
        script = list(MOCK_RUN_SCRIPT)
        if scenario == "fail":
            script = [s for s in script if s[0] not in ("RETRY_DECIDED",)] + [
                ("RUN_FAILED", "stdout", "Run failed: verification failed")]
        for etype, stream, msg in script:
            if scenario == "blocked" and etype == "ATTEMPT_STARTED":
                self._push(run_id, "RUN_FAILED", "stderr", "Blocked: provider quota exhausted")
                self._set(run_id, status="BLOCKED")
                return
            time.sleep(0.05)
            self._push(run_id, etype, stream, msg)
            self._apply_progress(run_id, etype)
        self._finalize(run_id, scenario)

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
