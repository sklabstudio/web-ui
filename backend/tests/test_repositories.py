from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient

from sklab_web.auth import clear_state
from sklab_web.config import AppConfig, AuthConfig, RepositoriesConfig
from sklab_web.main import create_app


def client(root: str) -> TestClient:
    clear_state()
    return TestClient(
        create_app(
            AppConfig(
                mock_mode=False,
                auth=AuthConfig(mode="disabled"),  # type: ignore[arg-type]
                repositories=RepositoriesConfig(allowed_roots=[root]),
            )
        )
    )


def test_repo_url_and_path_boundaries(tmp_path) -> None:  # type: ignore[no-untyped-def]
    c = client(str(tmp_path))
    assert c.post("/api/repos/clone", json={"url": "file:///etc/passwd"}).status_code == 400
    assert c.post("/api/repos/open", json={"path": "/etc/passwd"}).status_code == 400


def test_open_workspace_and_clone(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    c = client(str(tmp_path))
    existing = tmp_path / "existing"
    existing.mkdir()
    (existing / ".git").mkdir()
    opened = c.post("/api/repos/open", json={"path": str(existing)})
    assert opened.status_code == 200
    assert opened.json()["context_status"] == "READY"

    def fake_run(args, **_: object):  # type: ignore[no-untyped-def]
        if args[1] == "clone":
            destination = tmp_path / "fixture"
            destination.mkdir()
            (destination / ".git").mkdir()
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("sklab_web.main.subprocess.run", fake_run)
    cloned = c.post(
        "/api/repos/clone",
        json={"url": "https://github.com/example/fixture.git"},
    )
    assert cloned.status_code == 200
    assert cloned.json()["name"] == "fixture"
