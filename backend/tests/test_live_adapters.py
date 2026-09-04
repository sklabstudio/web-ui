"""L1 regression: real adapters win when modules are READY; mocks only on demand."""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sklab_web.auth import clear_state
from sklab_web.config import AppConfig, AuthConfig, RepositoriesConfig
from sklab_web.integrations import appsec_lab, contract_toolkit, protocol_intelligence
from sklab_web.main import create_app

FIXTURES = Path.home() / "sklab-integration" / "fixtures"


def _clear_mock_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for k in ("SKLAB_MOCK_SECURITY", "SKLAB_MOCK_CONTRACTS",
              "SKLAB_MOCK_PROTOCOLS", "SKLAB_MOCK_MODE"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("SKLAB_CONTRACTS_ROOT", str(FIXTURES / "contracts"))
    monkeypatch.setenv("SKLAB_PROTOCOLS_ROOT", str(FIXTURES / "protocols"))


def make_live_client() -> TestClient:
    clear_state()
    cfg = AppConfig(
        mock_mode=False, mock_security=False, mock_contracts=False, mock_protocols=False,
        auth=AuthConfig(mode="disabled"),  # type: ignore[arg-type]
        repositories=RepositoriesConfig(allowed_roots=["/srv/sklab/repos"]),
    )
    return TestClient(create_app(cfg))


def make_mock_client() -> TestClient:
    clear_state()
    cfg = AppConfig(
        mock_mode=True, mock_security=True, mock_contracts=True, mock_protocols=True,
        auth=AuthConfig(mode="disabled"),  # type: ignore[arg-type]
        repositories=RepositoriesConfig(allowed_roots=["/srv/sklab/repos"]),
    )
    return TestClient(create_app(cfg))


def test_real_adapter_wins_contracts(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_mock_env(monkeypatch)
    assert contract_toolkit.live_available() is True
    c = make_live_client()
    r = c.get("/api/contracts/tools")
    assert r.status_code == 200
    assert any(t.get("live") or t.get("tool") == "solc" for t in r.json())
    r = c.get("/api/contracts/projects")
    assert r.status_code == 200
    projects = r.json()
    assert any(p.get("id") == "proj-demo" and p.get("live") for p in projects), projects
    r = c.post("/api/contracts/projects/proj-demo/compile")
    assert r.status_code == 200, r.text
    assert r.json().get("live") is True
    assert r.json().get("ok") is True


def test_real_adapter_wins_protocols(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_mock_env(monkeypatch)
    assert protocol_intelligence.live_available() is True
    c = make_live_client()
    r = c.get("/api/protocols")
    assert r.status_code == 200
    assert any(p.get("id") == "proto-demo" and p.get("live") for p in r.json()), r.json()
    r = c.get("/api/protocols/proto-demo/map")
    assert r.status_code == 200
    assert r.json().get("live") is True
    r = c.get("/api/protocols/proto-demo/specs")
    assert r.status_code == 200


def test_real_adapter_wins_security(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_mock_env(monkeypatch)
    assert appsec_lab.live_available() is True
    c = make_live_client()
    r = c.get("/api/security/findings")
    assert r.status_code == 200
    findings = r.json()
    assert findings, "real analyzers must produce findings"
    assert all("live" in f for f in findings), findings
    r = c.get("/api/security/engagements/live-demo/traffic")
    assert r.status_code == 200
    assert all("live" in t for t in r.json())
    r = c.get("/api/security/simulations")
    assert r.status_code == 200
    assert r.json(), "real simulations must be non-empty"


def test_mock_fallback_explicit_only() -> None:
    c = make_mock_client()
    r = c.get("/api/contracts/projects")
    assert r.status_code == 200
    assert any(p.get("id") == "proj-demo" and not p.get("live") for p in r.json())
    r = c.get("/api/security/engagements")
    assert r.status_code == 200
    assert any(e.get("id") == "eng-demo" for e in r.json())
    r = c.get("/api/protocols")
    assert r.status_code == 200
    assert any(p.get("id") == "proto-demo" and not p.get("live") for p in r.json())


def test_unavailable_module_status_and_503(monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib.util

    real_find_spec = importlib.util.find_spec
    monkeypatch.setattr(
        importlib.util, "find_spec",
        lambda name, *a, **k: None
        if name in ("sklab_appsec_lab", "sklab_contract_toolkit", "sklab_protocol_intelligence")
        else real_find_spec(name, *a, **k),
    )
    _clear_mock_env(monkeypatch)
    assert appsec_lab.status()["state"] == "NOT_INSTALLED"
    assert contract_toolkit.status()["state"] == "NOT_INSTALLED"
    assert protocol_intelligence.status()["state"] == "NOT_INSTALLED"
    c = make_live_client()
    assert c.get("/api/security/engagements").status_code == 503
    assert c.get("/api/contracts/projects").status_code == 503
    assert c.get("/api/protocols").status_code == 503


def test_frontend_bundles_no_private_implementation() -> None:
    root = Path(__file__).resolve().parents[2] / "frontend" / "src"
    hits: list[str] = []
    if root.is_dir():
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in (".ts", ".tsx", ".js"):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                continue
            for marker in ("sklab_appsec_lab", "sklab_protocol_intelligence"):
                if marker in text:
                    hits.append(f"{path.name}:{marker}")
    assert hits == [], hits


def test_public_build_without_private_roots(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_mock_env(monkeypatch)
    monkeypatch.delenv("SKLAB_CONTRACTS_ROOT", raising=False)
    monkeypatch.delenv("SKLAB_PROTOCOLS_ROOT", raising=False)
    c = make_live_client()
    # Status stays honest; data falls back to fixtures (dev fixture mode).
    assert c.get("/api/contracts/status").status_code == 200
    r = c.get("/api/contracts/projects")
    assert r.status_code == 200
    assert any(p.get("id") == "proj-demo" for p in r.json())
