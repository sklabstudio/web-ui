"""v0.3 tests: run controls, skills ops, module matrix, and write-op
endpoints in mock mode (deterministic; live paths covered on the VPS)."""

from __future__ import annotations

import os

os.environ["SKLAB_MOCK_MODE"] = "1"

from fastapi.testclient import TestClient

from sklab_web.auth import clear_state
from sklab_web.config import AppConfig, AuthConfig, RepositoriesConfig
from sklab_web.main import create_app


def make_client(mode: str = "disabled") -> TestClient:
    clear_state()
    cfg = AppConfig(
        mock_mode=True,
        mock_security=True,
        mock_contracts=True,
        mock_protocols=True,
        auth=AuthConfig(mode=mode, token="test-token-123"),  # type: ignore[arg-type]
        repositories=RepositoriesConfig(allowed_roots=["/srv/sklab/repos"]),
    )
    return TestClient(create_app(cfg))


def test_run_controls_mock() -> None:
    c = make_client()
    run = c.post("/api/runs", json={"repository": "/srv/sklab/repos/demo", "task": "x"}).json()
    rid = run["id"]
    assert c.post(f"/api/runs/{rid}/execute").json()["ok"] is True
    retried = c.post(f"/api/runs/{rid}/retry").json()
    assert retried["status"] == "RETRYING"
    # approve/reject on non-gated run -> 409, never 500
    assert c.post(f"/api/runs/{rid}/approve").status_code == 409
    assert c.post(f"/api/runs/{rid}/reject").status_code == 409
    paid = c.post(
        "/api/runs", json={"repository": "/srv/sklab/repos/demo", "task": "x", "model": "paid-gpt"}
    ).json()
    assert paid["status"] == "WAITING_FOR_APPROVAL"
    assert c.post(f"/api/runs/{paid['id']}/approve").json()["status"] == "RUNNING_AGENT"
    paid2 = c.post(
        "/api/runs", json={"repository": "/srv/sklab/repos/demo", "task": "x", "model": "paid-gpt"}
    ).json()
    assert c.post(f"/api/runs/{paid2['id']}/reject").json()["status"] == "CANCELLED"


def test_skills_ops_mock() -> None:
    c = make_client()
    skills = c.get("/api/skills").json()
    assert len(skills) == 2
    assert c.get("/api/skills/tdd").json()["id"] == "tdd"
    assert c.get("/api/skills/nope").status_code == 404
    assert c.post("/api/skills/tdd/disable").json()["enabled"] is False
    assert c.post("/api/skills/tdd/enable", json={"task_scoped": True}).json()["enabled"] is True
    assert c.post("/api/skills/resolve", json={"task": "fix bug"}).status_code == 200
    assert c.get("/api/skills-auto").json()["mode"] == "OFF"
    assert c.post("/api/skills-auto", json={"mode": "SAFE"}).json()["mode"] == "SAFE"
    assert c.post("/api/skills-auto", json={"mode": "bogus"}).status_code == 400


def test_modules_full_and_doctor_mock() -> None:
    c = make_client()
    full = c.get("/api/modules/full").json()
    ids = {m["id"] for m in full}
    assert {"orchestrator", "agent_adapters", "appsec_lab", "skill_hub"} <= ids
    assert all(m["mock"] for m in full)
    assert c.get("/api/modules/orchestrator").json()["id"] == "orchestrator"
    assert c.get("/api/modules/nope").status_code == 404
    assert c.get("/api/doctor").json()["ok"] is True


def test_appsec_write_ops_mock() -> None:
    c = make_client()
    eng = c.post(
        "/api/security/engagements", json={"id": "eng-t1", "name": "t", "target_url": "http://x/"}
    ).json()
    assert eng["id"] == "eng-t1"
    assert c.post("/api/security/engagements/eng-t1/activate").json()["ok"] is True
    assert c.post("/api/security/engagements/eng-t1/close").json()["ok"] is True
    assert c.get("/api/security/browser").status_code == 200
    assert c.post("/api/security/engagements/eng-t1/browser/launch", json={}).json()["ok"] is True
    assert c.post("/api/security/engagements/eng-t1/capture", json={}).json()["ok"] is True
    assert c.post("/api/security/engagements/eng-t1/audit", json={}).json()["ok"] is True
    assert "simulations" in c.post("/api/security/engagements/eng-t1/simulate", json={}).json()
    assert (
        c.post("/api/security/retest", json={"ref": "sec-001"}).json()["retest_status"]
        == "VERIFIED"
    )
    assert "impact" in c.get("/api/security/findings/sec-001/impact").json()
    assert "reports" in c.post("/api/security/engagements/eng-t1/report", json={}).json()
    # invalid engagement id never 500s
    assert c.post("/api/security/engagements/../x/activate").status_code in (400, 404, 503)


def test_contracts_write_ops_mock() -> None:
    c = make_client()
    assert (
        c.post("/api/contracts/projects", json={"id": "proj-t1", "kind": "token"}).json()["id"]
        == "proj-t1"
    )
    imp = c.post(
        "/api/contracts/projects/import",
        json={"id": "proj-t2", "files": {"T.sol": "contract T {}"}},
    ).json()
    assert imp["ok"] is True
    assert "hotspots" in c.post("/api/contracts/projects/proj-demo/gas", json={}).json()
    assert "lines" in c.post("/api/contracts/projects/proj-demo/coverage", json={}).json()
    assert "nodes" in c.get("/api/contracts/projects/proj-demo/graph").json()
    assert "verdict" in c.post("/api/contracts/projects/proj-demo/upgrade-review", json={}).json()
    assert "layouts" in c.get("/api/contracts/projects/proj-demo/storage").json()
    assert "diff" in c.get("/api/contracts/projects/proj-demo/abi-diff").json()
    assert "threats" in c.get("/api/contracts/projects/proj-demo/threat-model").json()
    assert (
        "patch"
        in c.post("/api/contracts/projects/proj-demo/remediate", json={"ref": "ct-001"}).json()
    )
    assert (
        "retest_status"
        in c.post("/api/contracts/projects/proj-demo/retest", json={"ref": "ct-001"}).json()
    )
    assert "reports" in c.post("/api/contracts/projects/proj-demo/report", json={}).json()


def test_protocols_write_ops_mock() -> None:
    c = make_client()
    assert c.post("/api/protocols", json={"id": "proto-t1"}).json()["id"] == "proto-t1"
    assert "map" in c.post("/api/protocols/proto-demo/map", json={}).json()
    assert "ir" in c.post("/api/protocols/proto-demo/ir", json={}).json()
    assert "specs" in c.post("/api/protocols/proto-demo/specs", json={}).json()
    assert "invariants" in c.post("/api/protocols/proto-demo/invariants", json={}).json()
    assert (
        "result"
        in c.post(
            "/api/protocols/proto-demo/simulate",
            json={"scenario": "price-drop", "seed": 42, "runs": 5},
        ).json()
    )
    assert (
        "scenario"
        in c.post("/api/protocols/proto-demo/economic", json={"scenario": "price-drop"}).json()
    )
    assert "assurance" in c.post("/api/protocols/proto-demo/assure", json={}).json()
    assert "ok" in c.post("/api/protocols/proto-demo/verify", json={}).json()
    assert "verdict" in c.post("/api/protocols/proto-demo/upgrade-review", json={}).json()
    assert "checks" in c.post("/api/protocols/proto-demo/deployment-guard", json={}).json()
    assert "regressions" in c.post("/api/protocols/proto-demo/regression", json={}).json()
    assert "log" in c.post("/api/protocols/proto-demo/report", json={}).json()


def test_providers_test_and_repo_context_mock() -> None:
    c = make_client()
    assert c.post("/api/providers/local/test").json()["ok"] is True
    assert c.post("/api/providers/nope/test").status_code == 404
    ctx = c.post("/api/repos/demo/context").json()
    assert ctx["status"] == "READY"
    assert c.post("/api/repos/nope/context").status_code == 404
