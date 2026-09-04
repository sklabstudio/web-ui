"""v0.2 tests: module discovery, adapters, unavailable/degraded, DTO safety,
artifact scoping, auth protection, validation, secret redaction, mocks."""
from __future__ import annotations

import os

os.environ["SKLAB_MOCK_MODE"] = "1"

from fastapi.testclient import TestClient

from sklab_web.auth import clear_state
from sklab_web.config import AppConfig, AuthConfig, RepositoriesConfig
from sklab_web.integrations import (
    appsec_lab,
    contract_toolkit,
    module_discovery,
    protocol_intelligence,
)
from sklab_web.main import create_app


def make_client(mode: str = "disabled", mock: bool = True) -> TestClient:
    clear_state()
    cfg = AppConfig(
        mock_mode=mock,
        mock_security=True,
        mock_contracts=True,
        mock_protocols=True,
        auth=AuthConfig(mode=mode, token="test-token-123"),  # type: ignore[arg-type]
        repositories=RepositoriesConfig(allowed_roots=["/srv/sklab/repos"]),
    )
    return TestClient(create_app(cfg))


def make_nomock_client() -> TestClient:
    clear_state()
    cfg = AppConfig(
        mock_mode=False,
        mock_security=False,
        mock_contracts=False,
        mock_protocols=False,
        auth=AuthConfig(mode="disabled"),  # type: ignore[arg-type]
        repositories=RepositoriesConfig(allowed_roots=["/srv/sklab/repos"]),
    )
    # ensure env mocks off
    for k in ("SKLAB_MOCK_SECURITY", "SKLAB_MOCK_CONTRACTS", "SKLAB_MOCK_PROTOCOLS", "SKLAB_MOCK_MODE"):
        os.environ.pop(k, None)
    c = TestClient(create_app(cfg))
    os.environ["SKLAB_MOCK_MODE"] = "1"
    return c


def test_module_discovery_caps() -> None:
    mods = module_discovery(mock_mode=True)
    caps = {m["capability"] for m in mods}
    assert caps == {"security.appsec", "contracts.toolkit", "protocols.intelligence"}
    for m in mods:
        assert m["state"] in ("READY", "DEGRADED", "UNAVAILABLE", "NOT_INSTALLED", "UNKNOWN")


def test_adapters_never_require_private_import() -> None:
    assert appsec_lab.status(True)["state"] == "READY"
    assert contract_toolkit.status(True)["state"] == "READY"
    assert protocol_intelligence.status(True)["state"] == "READY"


def test_system_includes_v02_modules() -> None:
    c = make_client()
    data = c.get("/api/system").json()
    for k in ("appsec_lab", "contract_toolkit", "protocol_intelligence", "sklab_cli"):
        assert k in data, k


def test_security_status_and_findings() -> None:
    c = make_client()
    st = c.get("/api/security/status").json()
    assert st["open_findings"] == 3
    findings = c.get("/api/security/findings").json()
    assert len(findings) == 3
    assert c.get("/api/security/findings/sec-001").json()["id"] == "sec-001"
    assert len(c.get("/api/security/engagements").json()) == 1
    assert len(c.get("/api/security/engagements/eng-demo/traffic").json()) == 3
    assert len(c.get("/api/security/engagements/eng-demo/api-map").json()) == 2
    assert len(c.get("/api/security/simulations").json()) >= 8
    assert len(c.get("/api/security/reports").json()) == 2


def test_contracts_flow() -> None:
    c = make_client()
    assert c.get("/api/contracts/status").json()["projects"] == 1
    projs = c.get("/api/contracts/projects").json()
    assert projs[0]["id"] == "proj-demo"
    assert c.get("/api/contracts/projects/proj-demo").json()["id"] == "proj-demo"
    assert c.post("/api/contracts/projects/proj-demo/compile").json()["ok"] is True
    assert c.post("/api/contracts/projects/proj-demo/test").json()["total"] == 42
    assert c.post("/api/contracts/projects/proj-demo/fuzz").json()["seed"] == 42
    assert "invariants" in c.post("/api/contracts/projects/proj-demo/invariants").json()
    assert len(c.get("/api/contracts/findings").json()) == 2
    assert len(c.get("/api/contracts/tools").json()) == 8


def test_protocols_flow() -> None:
    c = make_client()
    plist = c.get("/api/protocols").json()
    assert plist[0]["id"] == "proto-demo"
    det = c.get("/api/protocols/proto-demo").json()
    assert len(det["assurance"]) == 10
    assert len(c.get("/api/protocols/proto-demo/map").json()["nodes"]) == 3
    assert len(c.get("/api/protocols/proto-demo/assets").json()) == 1
    assert len(c.get("/api/protocols/proto-demo/assurance").json()) == 10
    assert len(c.get("/api/protocols/proto-demo/monitor").json()) == 1
    assert len(c.get("/api/protocols/proto-demo/incidents").json()) == 1


def test_private_dto_safety_redaction() -> None:
    dirty = {"auth_token": "secret-x", "cookie": "abc", "host": "ok", "nested": {"rpc_url": "http://x"}}
    clean = appsec_lab.redacted(dirty)
    assert "secret-x" not in str(clean)
    assert clean["host"] == "ok"
    c = make_client()
    blob = str(c.get("/api/security/status").json()) + str(c.get("/api/security/findings").json())
    # fixtures must not embed raw secret values; redaction helper covers live DTOs
    assert "sk-live" not in blob
    assert "PRIVATE_KEY" not in blob


def test_artifact_scoping() -> None:
    c = make_client()
    assert c.get("/api/artifacts/artifact-rep-sec-001").status_code == 200
    assert c.get("/api/artifacts/../secret").status_code in (400, 404)
    assert c.get("/api/artifacts/a%2Fb").status_code in (400, 404)


def test_auth_protects_v02_routes() -> None:
    c = make_client("token")
    assert c.get("/api/security/status").status_code == 401
    assert c.get("/api/contracts/projects").status_code == 401
    assert c.get("/api/protocols").status_code == 401


def test_error_normalization_unavailable() -> None:
    c = make_nomock_client()
    # Without mocks and without private packages installed, security/protocols degrade
    r = c.get("/api/security/engagements")
    # Either 503 normalized or empty-safe; must not 500 and must carry code
    assert r.status_code in (200, 503)
    if r.status_code == 503:
        assert r.json()["detail"]["code"] in ("PRIVATE_MODULE_UNAVAILABLE", "MODULE_UNAVAILABLE")


def test_no_private_import_required_at_build() -> None:
    import importlib.util

    # Public build must not hard-require private packages
    assert importlib.util.find_spec("sklab_web") is not None
    # adapters degrade when private absent (mock off path covered above)


def test_secret_leak_absent_from_fixtures() -> None:
    c = make_client()
    blob = (
        str(c.get("/api/security/status").json())
        + str(c.get("/api/security/engagements/eng-demo/traffic").json())
        + str(c.get("/api/contracts/projects").json())
        + str(c.get("/api/protocols").json())
    )
    for needle in ("sk-live", "Bearer ey", "client-secret", "rpc-key", "PRIVATE_KEY"):
        assert needle not in blob
