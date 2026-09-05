"""Typed Pydantic schemas for the Web API. Single source of truth for the contract."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ComponentState = Literal["READY", "DEGRADED", "UNAVAILABLE", "NOT_INSTALLED", "UNKNOWN"]
ModuleState = Literal["READY", "DEGRADED", "UNAVAILABLE", "NOT_INSTALLED", "UNKNOWN"]
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
    "MODULE_NOT_INSTALLED",
    "MODULE_UNAVAILABLE",
    "PRIVATE_MODULE_UNAVAILABLE",
    "BROWSER_UNAVAILABLE",
    "ENGAGEMENT_NOT_FOUND",
    "CONTRACT_TOOL_UNAVAILABLE",
    "COMPILE_FAILED",
    "TEST_FAILED",
    "FUZZ_COUNTEREXAMPLE",
    "INVARIANT_FAILED",
    "UPGRADE_BLOCKED",
    "ASSURANCE_STALE",
    "MONITOR_DISCONNECTED",
    "INCIDENT_DATA_INCOMPLETE",
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
    # v0.2 security
    "SECURITY_SCAN_STARTED",
    "BROWSER_FLOW_STARTED",
    "API_DISCOVERED",
    "FINDING_CREATED",
    "SIMULATION_STARTED",
    "SIMULATION_COMPLETED",
    # v0.2 contracts
    "CONTRACT_COMPILE_STARTED",
    "CONTRACT_TEST_STARTED",
    "FUZZ_STARTED",
    "INVARIANT_RESULT",
    "UPGRADE_REVIEW_COMPLETED",
    # v0.2 protocols
    "PROTOCOL_MAP_READY",
    "SPEC_DERIVED",
    "INVARIANT_DERIVED",
    "ECONOMIC_SIM_STARTED",
    "ASSURANCE_UPDATED",
    "MONITOR_ALERT",
    "INCIDENT_RECONSTRUCTED",
]


class ApiError(BaseModel):
    code: str = "INTERNAL_ERROR"
    message: str = "Internal error"
    details: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    ok: bool = True
    mock_mode: bool = False
    version: str = "0.2.0"


class VersionResponse(BaseModel):
    web_ui: str = "0.2.0"
    api_schema: int = 2
    orchestrator: str | None = None
    agent_adapters: str | None = None
    provider_connections: str | None = None
    appsec_lab: str | None = None
    contract_toolkit: str | None = None
    protocol_intelligence: str | None = None
    sklab_cli: str | None = None


class ComponentStatus(BaseModel):
    state: ComponentState = "UNKNOWN"
    version: str | None = None
    detail: str = ""


class ModuleStatus(BaseModel):
    name: str = ""
    capability: str = ""
    state: ModuleState = "UNKNOWN"
    version: str | None = None
    detail: str = ""
    mock: bool = False


class SystemResponse(BaseModel):
    web_ui: ComponentStatus = ComponentStatus(state="READY", version="0.2.0")
    orchestrator: ComponentStatus = ComponentStatus()
    agent_adapters: ComponentStatus = ComponentStatus()
    provider_connections: ComponentStatus = ComponentStatus()
    repo_context: ComponentStatus = ComponentStatus()
    reprobox: ComponentStatus = ComponentStatus()
    patchbench: ComponentStatus = ComponentStatus()
    benchsuite: ComponentStatus = ComponentStatus()
    codetrials: ComponentStatus = ComponentStatus()
    promptbench: ComponentStatus = ComponentStatus()
    appsec_lab: ComponentStatus = ComponentStatus()
    contract_toolkit: ComponentStatus = ComponentStatus()
    protocol_intelligence: ComponentStatus = ComponentStatus()
    sklab_cli: ComponentStatus = ComponentStatus()


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


class RepoCloneRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
    destination: str | None = Field(default=None, max_length=80)


class RepoOpenRequest(BaseModel):
    path: str = Field(min_length=1, max_length=4096)


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
    # v0.3 operational sections (all optional; unknown keys ignored by clients)
    execution_policy: str = "safe"
    provider_default: str = ""
    agent_default: str = ""
    skill_auto_mode: str = "OFF"
    appsec_safe_limits: dict[str, Any] = Field(default_factory=dict)
    contract_tool_preferences: dict[str, Any] = Field(default_factory=dict)
    protocol_assurance_defaults: dict[str, Any] = Field(default_factory=dict)
    ui_preferences: dict[str, Any] = Field(default_factory=dict)


class LoginRequest(BaseModel):
    password: str | None = None
    token: str | None = None


# ---------------- v0.3: operational controls ----------------


class SkillAutoMode(BaseModel):
    mode: str = "OFF"


class EngagementCreateRequest(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    name: str = ""
    target_url: str = ""
    scope: str = ""
    trusted_auth_host: str = ""
    auth_mode: str = "none"


class BrowserLaunchRequest(BaseModel):
    headed: bool = False


class CaptureRequest(BaseModel):
    scenario: str = "normal-api"


class SimulationRequest(BaseModel):
    check: str = ""


class RetestRequest(BaseModel):
    ref: str = ""
    engagement: str = ""


class ContractProjectCreateRequest(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    kind: str = "custom"


class ContractImportRequest(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    files: dict[str, str] = Field(default_factory=dict)


class ContractRemediationRequest(BaseModel):
    ref: str = ""


class ProtocolCreateRequest(BaseModel):
    id: str = Field(min_length=1, max_length=64)


class ProtocolImportRequest(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    files: dict[str, str] = Field(default_factory=dict)


class EconomicRequest(BaseModel):
    scenario: str = "price-drop"
    seed: int = 42
    runs: int = 20


class UpgradeReviewRequest(BaseModel):
    old: str = ""
    new: str = ""


class AuditEntry(BaseModel):
    ts: str
    action: str
    detail: str = ""


# ---------------- v0.2: shared + Security / Contracts / Protocols ----------------

FindingStatus = Literal[
    "OPEN",
    "CONFIRMED",
    "LIKELY",
    "NEEDS_REVIEW",
    "FIXED",
    "FIXED_VERIFIED",
    "ACCEPTED_RISK",
    "FALSE_POSITIVE",
    "INCONCLUSIVE",
]
ImpactLevel = Literal["NONE", "LOW", "MEDIUM", "HIGH", "UNKNOWN"]
AssuranceState = Literal[
    "VERIFIED", "PARTIAL", "FAILED", "INCONCLUSIVE", "NOT_TESTED", "NOT_APPLICABLE"
]


class FindingModel(BaseModel):
    id: str
    source: str = "unknown"
    severity: str = "MEDIUM"
    confidence: str = "MEDIUM"
    title: str = ""
    endpoint: str | None = None
    flow: str | None = None
    contract: str | None = None
    function: str | None = None
    status: str = "OPEN"
    evidence_ref: str | None = None
    retest_status: str | None = None
    description: str = ""
    remediation: str = ""
    impact: dict[str, str] = Field(default_factory=dict)


class ReportRef(BaseModel):
    id: str
    kind: str = "markdown"
    title: str = ""
    created_at: str = ""
    artifact_id: str = ""


class SecurityEngagement(BaseModel):
    id: str
    name: str = ""
    status: str = "ACTIVE"
    scope_summary: str = ""
    created_at: str = ""
    last_run: str | None = None
    finding_count: int = 0
    report_status: str = "NONE"


class TrafficEntry(BaseModel):
    ts: str = ""
    method: str = "GET"
    host: str = ""
    path: str = ""
    status: int = 200
    kind: str = "REST"
    auth: str = "none"
    duration_ms: int = 0
    flow: str = ""


class ApiEndpoint(BaseModel):
    host: str = ""
    route: str = ""
    method: str = "GET"
    auth: str = "none"
    roles: dict[str, int] = Field(default_factory=dict)


class SimulationResult(BaseModel):
    id: str
    simulation: str = ""
    target: str = ""
    role: str = ""
    result: str = "INCONCLUSIVE"
    requests: int = 0
    duration_ms: int = 0
    impact: str = "UNKNOWN"
    evidence_ref: str | None = None


class ContractProject(BaseModel):
    id: str
    name: str = ""
    chain: str = "ethereum"
    toolchain: str = "foundry"
    compiler: str | None = None
    contracts: int = 0
    standards: list[str] = Field(default_factory=list)
    authorities: list[str] = Field(default_factory=list)
    last_build: str | None = None
    last_analysis: str | None = None
    status: str = "UNKNOWN"


class ContractSummary(BaseModel):
    id: str
    name: str = ""
    source: str = ""
    kind: str = "contract"
    standard: str | None = None
    upgradeability: str = "UNKNOWN"
    authorities: list[str] = Field(default_factory=list)
    functions: int = 0


class ToolStatus(BaseModel):
    id: str
    installed: bool = False
    version: str | None = None
    status: str = "UNKNOWN"
    capabilities: list[str] = Field(default_factory=list)


class ProtocolSummary(BaseModel):
    id: str
    chain: str = "ethereum"
    source_summary: str = ""
    assurance_freshness: str = "UNKNOWN"
    open_findings: int = 0
    critical_authorities: int = 0
    monitored: bool = False
    latest_upgrade: str | None = None
    active_alerts: int = 0


class AssuranceItem(BaseModel):
    check: str = ""
    state: str = "NOT_TESTED"
    detail: str = ""


class MonitorAlert(BaseModel):
    id: str
    kind: str = ""
    severity: str = "MEDIUM"
    message: str = ""
    ts: str = ""
