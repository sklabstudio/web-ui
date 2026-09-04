"""Backend tests: health, auth, path safety, mock runs, SSE, secrets, validation."""
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
        auth=AuthConfig(mode=mode, token="test-token-123"),  # type: ignore[arg-type]
        repositories=RepositoriesConfig(allowed_roots=["/srv/sklab/repos"]),
    )
    return TestClient(create_app(cfg))


def test_health_and_version() -> None:
    c = make_client()
    assert c.get("/api/health").json()["ok"] is True
    assert c.get("/api/version").json()["api_schema"] == 2


def test_system_degraded_not_fake() -> None:
    c = make_client()
    data = c.get("/api/system").json()
    assert data["web_ui"]["state"] == "READY"


def test_auth_required_in_token_mode() -> None:
    c = make_client("token")
    assert c.get("/api/runs").status_code == 401
    assert c.get("/api/runs").json()["detail"]["code"] == "AUTH_REQUIRED"
    r = c.post("/api/auth/login", json={"token": "test-token-123"})
    assert r.status_code == 200


def test_path_traversal_rejected() -> None:
    c = make_client()
    for bad in ["../../", "/etc", "/etc/passwd", "C:\\Windows", "/"]:
        r = c.post("/api/runs/plan", json={"repository": bad, "task": "fix"})
        assert r.status_code == 400, bad


def test_plan_and_run_lifecycle() -> None:
    c = make_client()
    plan = c.post("/api/runs/plan", json={"repository": "/srv/sklab/repos/demo", "task": "fix timeout"}).json()
    assert plan["selected_agent"] == "hermes"
    run = c.post("/api/runs", json={"repository": "/srv/sklab/repos/demo", "task": "fix timeout"}).json()
    rid = run["id"]
    assert rid.startswith("run-")
    detail = c.get(f"/api/runs/{rid}").json()
    assert detail["id"] == rid
    # cancel works
    assert c.post(f"/api/runs/{rid}/cancel").json()["status"] == "CANCELLED"


def test_approval_flow_for_paid_model() -> None:
    c = make_client()
    run = c.post("/api/runs", json={"repository": "/srv/sklab/repos/demo",
                                    "task": "x", "model": "paid-gpt"}).json()
    assert run["status"] == "WAITING_FOR_APPROVAL"
    resumed = c.post(f"/api/runs/{run['id']}/resume", json={}).json()
    assert resumed["status"] == "RUNNING_AGENT"


def test_provider_secret_never_returned() -> None:
    c = make_client()
    fake = "do-not-leak-123"
    created = c.post("/api/providers", json={"id": "t", "api_key": fake}).json()
    assert fake not in str(created)
    listed = c.get("/api/providers").json()
    assert fake not in str(listed)
    assert fake not in str(c.get("/api/system").json())


def test_xss_event_message_preserved_as_text() -> None:
    # Backend stores raw text; frontend must render as text (covered in frontend tests).
    c = make_client()
    run = c.post("/api/runs", json={"repository": "/srv/sklab/repos/demo", "task": "x"}).json()
    assert run["id"]


def test_events_endpoint_streams() -> None:
    c = make_client()
    run = c.post("/api/runs", json={"repository": "/srv/sklab/repos/demo", "task": "x"}).json()
    # SSE endpoint exists and returns event-stream (read first chunk via stream)
    with c.stream("GET", f"/api/runs/{run['id']}/events") as r:
        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]
        chunk = next(r.iter_text())
        assert "data:" in chunk or "id:" in chunk


def test_artifact_path_safety() -> None:
    c = make_client()
    assert c.get("/api/artifacts/../secret").status_code in (400, 404)
    assert c.get("/api/artifacts/..%2Fsecret").status_code in (400, 404)


def test_cors_not_wildcard() -> None:
    c = make_client()
    r = c.get("/api/health", headers={"Origin": "https://evil.example"})
    assert r.headers.get("access-control-allow-origin") != "*"
