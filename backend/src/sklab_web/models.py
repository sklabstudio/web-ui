"""Typed Pydantic schemas for the Web API. Single source of truth for the contract."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ComponentState = Literal["READY", "DEGRADED", "UNAVAILABLE", "UNKNOWN"]
ErrorCode = Literal[
    "AUTH_REQUIRED",
    "PROVIDER_UNAVAILABLE",
    "AGENT_UNAVAILABLE",
    "FREE_LIMIT_REACHED",
    "BUDGET_EXHAUSTED",
    "APPROVAL_REQUIRED",
    "NO_PROGRESS",
    "VERIFICATION_FAILED",
    "RUN_CANCELLED",
    "INTERNAL_ERROR",
    "NOT_FOUND",
    "BAD_REQUEST",
    "FORBIDDEN",
]

EVENT_TYPES = [
    "RUN_CREATED",
    "INSPECTION_STARTED",
    "INSPECTION_COMPLETED",
    "PLAN_CREATED",
    "AGENT_SELECTED",
    "PROVIDER_SELECTED",
    "WORKSPACE_READY",
    "ATTEMPT_STARTED",
    "AGENT_EVENT",
    "PATCH_CAPTURED",
    "VERIFICATION_STARTED",
    "VERIFICATION_COMPLETED",
    "RETRY_DECIDED",
    "BUDGET_WARNING",
    "APPROVAL_REQUIRED",
    "RUN_COMPLETED",
    "RUN_FAILED",
    "RUN_CANCELLED",
]


class ApiError(BaseModel):
    code: str = "INTERNAL_ERROR"
    message: str = "Internal error"
    details: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    ok: bool = True
    mock_mode: bool = False
    version: str = "0.1.0"


class VersionResponse(BaseModel):
    web_ui: str = "0.1.0"
    api_schema: int = 1
    orchestrator: str | None = None
    agent_adapters: str | None = None
    provider_connections: str | None = None


class ComponentStatus(BaseModel):
    state: ComponentState = "UNKNOWN"
    version: str | None = None
    detail: str = ""


class SystemResponse(BaseModel):
    web_ui: ComponentStatus = ComponentStatus(state="READY", version="0.1.0")
    orchestrator: ComponentStatus = ComponentStatus()
    agent_adapters: ComponentStatus = ComponentStatus()
    provider_connections: ComponentStatus = ComponentStatus()
    repo_context: ComponentStatus = ComponentStatus()
    reprobox: ComponentStatus = ComponentStatus()
    patchbench: ComponentStatus = ComponentStatus()
    benchsuite: ComponentStatus = ComponentStatus()
    codetrials: ComponentStatus = ComponentStatus()
    promptbench: ComponentStatus = ComponentStatus()


class RepoSummary(BaseModel):
    id: str
    name: str
    path: str
    branch: str | None = None
    dirty: bool = False
    stack: list[str] = Field(default_factory=list)
    last_run_id: str | None = None
    warnings: list[str] = Field(default_factory=list)
    context_status: str = "UNKNOWN"


class AgentSummary(BaseModel):
    id: str
    installed: bool = False
    version: str | None = None
    auth_ready: bool = False
    capabilities: dict[str, str] = Field(default_factory=dict)
    supports_model_selection: bool = False
    sessions: bool = False
    resume: bool = False
    streaming: bool = False
    status: str = "UNKNOWN"
    cost_class: str = "unknown"


class ProviderSummary(BaseModel):
    id: str
    label: str = ""
    type: str = "api_key"
    status: str = "UNKNOWN"
    default_model: str | None = None
    last_validated: str | None = None
    enabled: bool = True


class ProviderCreateRequest(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    type: str = "api_key"
    api_key: str | None = None
    default_model: str | None = None


class EnvironmentSummary(BaseModel):
    name: str
    executor: str = "unknown"
    fingerprint: str = ""
    image: str = ""
    python_version: str | None = None
    node_version: str | None = None
    network_mode: str = "none"
    lock_status: str = "unknown"
    warnings: list[str] = Field(default_factory=list)
    last_verified: str | None = None


class BenchmarkTask(BaseModel):
    id: str
    title: str
    stack: str = ""
    category: str = ""
    difficulty: str = ""
    version: str = "0.1.0"
    fingerprint: str = ""


class CodeTrialSummary(BaseModel):
    id: str
    task: str = ""
    agents: list[str] = Field(default_factory=list)
    winner: str | None = None
    tie: bool = False
    verified: bool = False
    cost: str | None = None


class PromptExperimentSummary(BaseModel):
    id: str
    name: str = ""
    variants: int = 0
    success_rate: float | None = None
    median_score: float | None = None
    winner: str | None = None


class SkillSummary(BaseModel):
    id: str
    enabled: bool = True
    category: str = "general"
    source: str = "builtin"
    trust_level: str = "verified"
    permissions: list[str] = Field(default_factory=list)
    version: str = "0.1.0"


class PlanRequest(BaseModel):
    repository: str = ""
    repo_id: str | None = None
    task: str = Field(min_length=1, max_length=20000)
    agent: str | None = None
    model: str | None = None
    provider: str | None = None
    skill: str | None = None
    routing_policy: str = "safe"
    max_attempts: int = 3
    timeout_seconds: int = 1200
    cost_budget: float | None = None
    reprobox: bool = True
    verification: bool = True
    bench_task: str | None = None


class PlanGate(BaseModel):
    label: Literal["AUTO", "USER_OVERRIDE", "UNAVAILABLE", "APPROVAL_REQUIRED"]
    detail: str = ""


class PlanResponse(BaseModel):
    classification: str = "UNKNOWN"
    repo_summary: str = ""
    required_capabilities: list[str] = Field(default_factory=list)
    selected_agent: str = "unknown"
    fallback_agents: list[str] = Field(default_factory=list)
    provider: str | None = None
    model: str | None = None
    skill: str | None = None
    environment: str = "default"
    verification_strategy: str = "patchbench"
    retry_policy: str = "evidence-driven"
    budget: str = "unknown"
    permissions: list[str] = Field(default_factory=list)
    approval_gates: list[PlanGate] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RunCreateRequest(PlanRequest):
    pass


class AttemptSummary(BaseModel):
    index: int
    agent: str = ""
    model: str | None = None
    skill: str | None = None
    duration_seconds: float = 0
    status: str = "UNKNOWN"
    patch_fingerprint: str | None = None
    verifier_verdict: str | None = None
    verifier_score: float | None = None
    cost: str | None = None
    retry_reason: str | None = None


class VerificationSummary(BaseModel):
    verdict: str = "UNKNOWN"
    score: float | None = None
    regressions: int | None = None
    checks: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    scope_warnings: list[str] = Field(default_factory=list)
    duration_seconds: float = 0
    environment_fingerprint: str = ""


class RunSummary(BaseModel):
    id: str
    task: str = ""
    task_summary: str = ""
    repo: str = ""
    repo_id: str | None = None
    status: str = "CREATED"
    attempts: int = 0
    winning_agent: str | None = None
    verification: str = "UNKNOWN"
    duration_seconds: float = 0
    cost: str | None = None
    created_at: str = ""
    result_status: str | None = None


class RunDetail(RunSummary):
    agent: str | None = None
    model: str | None = None
    provider: str | None = None
    environment: str | None = None
    attempt_details: list[AttemptSummary] = Field(default_factory=list)
    verification_detail: VerificationSummary | None = None
    patch: str | None = None
    warnings: list[str] = Field(default_factory=list)
    approval: dict[str, Any] | None = None
    fingerprints: dict[str, str] = Field(default_factory=dict)


class RunEvent(BaseModel):
    seq: int
    type: str = "AGENT_EVENT"
    ts: str = ""
    message: str = ""
    stream: str = "stdout"
    data: dict[str, Any] = Field(default_factory=dict)


class SettingsModel(BaseModel):
    default_routing_policy: str = "safe"
    max_attempts: int = 3
    default_timeout_seconds: int = 1200
    default_budget: float | None = None
    require_approval_for_paid: bool = True
    reprobox_default: bool = True
    verification_default: bool = True
    auto_apply_patch: bool = False
    auto_push: bool = False
    skill_auto_install: str = "OFF"
    allowed_repo_roots: list[str] = Field(default_factory=list)


class LoginRequest(BaseModel):
    password: str | None = None
    token: str | None = None


class AuditEntry(BaseModel):
    ts: str
    action: str
    detail: str = ""
