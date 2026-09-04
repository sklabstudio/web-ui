"""Protocol Intelligence integration — PRIVATE module behind a public-safe adapter.

Same boundary rules as AppSec Lab: backend-side dynamic discovery only,
generic DTOs, no proprietary logic copied into this repo.
"""
from __future__ import annotations

import importlib.util
import os
from typing import Any


def _mock_enabled() -> bool:
    v = os.environ.get("SKLAB_MOCK_PROTOCOLS", os.environ.get("SKLAB_MOCK_MODE", "")).lower()
    return v in ("1", "true", "yes")


def _private_available() -> tuple[bool, str | None]:
    try:
        spec = importlib.util.find_spec("sklab_protocol_intelligence")
        if spec is None:
            return False, None
        mod = importlib.import_module("sklab_protocol_intelligence")
        return True, str(getattr(mod, "__version__", "unknown"))
    except Exception:
        return False, None


def status(mock_mode: bool = False) -> dict[str, Any]:
    if mock_mode or _mock_enabled():
        return {"state": "READY", "version": "mock-0.2.0",
                "detail": "mock Protocol Intelligence (deterministic fixture)", "mock": True}
    ok, ver = _private_available()
    if ok:
        return {"state": "READY", "version": ver,
                "detail": "detected sklab_protocol_intelligence", "mock": False}
    return {"state": "NOT_INSTALLED", "version": None,
            "detail": "Protocol Intelligence not installed (optional private module)", "mock": False}


def capability() -> str:
    return "protocols.intelligence"


def live_available(mock_mode: bool = False) -> bool:
    """True when the real private module is installed and mocks are off."""
    if mock_mode or _mock_enabled():
        return False
    ok, _ = _private_available()
    return ok


def resolve_protocol_root(pid: str) -> str | None:
    """Map a protocol id to a real workspace under SKLAB_PROTOCOLS_ROOT.

    Only explicit operator configuration; never developer-machine defaults.
    Returns None when unresolvable (caller falls back to fixtures).
    """
    import re
    from pathlib import Path

    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-_]{0,63}", pid or ""):
        return None
    root_env = os.environ.get("SKLAB_PROTOCOLS_ROOT", "").strip()
    if not root_env:
        return None
    candidate = (Path(root_env).expanduser() / pid).resolve()
    try:
        base = Path(root_env).expanduser().resolve()
    except Exception:
        return None
    if base not in candidate.parents:
        return None
    return str(candidate) if candidate.is_dir() else None


def _load(pid: str, root: str):  # type: ignore[no-untyped-def]
    from sklab_protocol_intelligence.core.config import load_manifest
    from sklab_protocol_intelligence.graphs.protocol_map import build_protocol_map
    from sklab_protocol_intelligence.ir.builder import build_ir

    manifest = load_manifest(root)
    protocol_id = getattr(manifest, "id", pid) or pid
    chain = getattr(manifest, "chain", "ethereum") or "ethereum"
    ir = build_ir(root, protocol_id=protocol_id, chain=chain)
    pmap = build_protocol_map(root, protocol_id=protocol_id)
    return ir, pmap, protocol_id, chain


def _dump(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _dump(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_dump(v) for v in obj]
    if hasattr(obj, "model_dump"):
        try:
            return _dump(obj.model_dump(mode="python"))
        except Exception:
            pass
    if hasattr(obj, "to_json"):
        try:
            return _dump(obj.to_json())
        except Exception:
            pass
    return str(obj)


def live_list() -> list[dict[str, Any]] | None:
    """Real protocol workspaces discovered under SKLAB_PROTOCOLS_ROOT."""
    import os as _os
    from pathlib import Path as _Path

    root_env = _os.environ.get("SKLAB_PROTOCOLS_ROOT", "").strip()
    if not root_env:
        return None
    try:
        base = _Path(root_env).expanduser().resolve()
        if not base.is_dir():
            return None
        out: list[dict[str, Any]] = []
        for child in sorted(base.iterdir()):
            if not child.is_dir() or child.name.startswith("."):
                continue
            try:
                from sklab_protocol_intelligence.core.config import load_manifest

                manifest = load_manifest(str(child))
                pid = getattr(manifest, "id", child.name) or child.name
            except Exception:
                continue
            out.append({
                "id": pid, "chain": "ethereum",
                "source_summary": "live workspace",
                "assurance_freshness": "UNKNOWN", "open_findings": 0,
                "critical_authorities": 0, "monitored": False,
                "latest_upgrade": "", "active_alerts": 0, "live": True,
            })
        return out or None
    except Exception:
        return None


def live_map(pid: str) -> dict[str, Any] | None:
    root = resolve_protocol_root(pid)
    if root is None:
        return None
    try:
        _, pmap, protocol_id, _ = _load(pid, root)
        graph = pmap.get("graph", {}) if isinstance(pmap, dict) else {}
        nodes = graph.get("nodes", []) if isinstance(graph, dict) else []
        edges = graph.get("edges", []) if isinstance(graph, dict) else []
        return {"id": protocol_id, "nodes": _dump(nodes), "edges": _dump(edges), "live": True}
    except Exception:
        return None


def live_assets(pid: str) -> list[dict[str, Any]] | None:
    root = resolve_protocol_root(pid)
    if root is None:
        return None
    try:
        from sklab_protocol_intelligence.graphs.asset_flow import build_asset_flow_from_root

        rows = build_asset_flow_from_root(root, pid)
        return [{**r, "live": True} if isinstance(r, dict) else {"flow": str(r), "live": True}
                for r in (rows if isinstance(rows, list) else [])] or None
    except Exception:
        try:
            from sklab_protocol_intelligence.graphs.asset_flow import build_asset_flow

            ir, _, _, _ = _load(pid, root)
            return _dump({"flows": build_asset_flow(ir), "live": True}) or None
        except Exception:
            return None


def live_authorities(pid: str) -> list[dict[str, Any]] | None:
    root = resolve_protocol_root(pid)
    if root is None:
        return None
    try:
        from sklab_protocol_intelligence.graphs.authority import build_authority_graph
        from sklab_protocol_intelligence.graphs.blast_radius import compute_blast_radius

        ir, _, _, _ = _load(pid, root)
        graph = build_authority_graph(ir)
        blast = compute_blast_radius(graph) if isinstance(graph, dict) else []
        g = _dump(graph)
        nodes = g.get("nodes", []) if isinstance(g, dict) else []
        out = nodes if isinstance(nodes, list) else [g]
        if blast:
            out = out + [{"blast_radius": _dump(blast), "live": True}]
        return [{**r, "live": True} if isinstance(r, dict) else {"authority": str(r), "live": True}
                for r in out] or None
    except Exception:
        return None


def live_specs(pid: str) -> list[dict[str, Any]] | None:
    root = resolve_protocol_root(pid)
    if root is None:
        return None
    try:
        from sklab_protocol_intelligence.specs.miner import mine_specs

        ir, pmap, _, _ = _load(pid, root)
        specs = mine_specs(ir, pmap)
        return [_dump({**s, "live": True}) if isinstance(s, dict) else _dump(s)
                for s in (specs if isinstance(specs, list) else [])] or None
    except Exception:
        return None


def live_invariants(pid: str) -> list[dict[str, Any]] | None:
    root = resolve_protocol_root(pid)
    if root is None:
        return None
    try:
        from sklab_protocol_intelligence.invariants.miner import mine_invariants
        from sklab_protocol_intelligence.specs.miner import mine_specs

        ir, pmap, _, _ = _load(pid, root)
        invs = mine_invariants(mine_specs(ir, pmap))
        return [_dump(i) for i in (invs if isinstance(invs, list) else [])] or None
    except Exception:
        return None


def live_evidence(pid: str) -> list[dict[str, Any]] | None:
    root = resolve_protocol_root(pid)
    if root is None:
        return None
    try:
        from sklab_protocol_intelligence.evidence.graph import build_evidence
        from sklab_protocol_intelligence.invariants.miner import mine_invariants
        from sklab_protocol_intelligence.specs.miner import mine_specs

        ir, pmap, _, _ = _load(pid, root)
        specs = mine_specs(ir, pmap)
        graph = build_evidence(specs, mine_invariants(specs), [], [])
        g = _dump(graph)
        edges = g.get("edges", [g]) if isinstance(g, dict) else g
        return edges if isinstance(edges, list) else [edges]
    except Exception:
        return None


def live_assurance(pid: str) -> list[dict[str, Any]] | None:
    root = resolve_protocol_root(pid)
    if root is None:
        return None
    try:
        from sklab_protocol_intelligence.assurance.profile import build_profile

        profile = build_profile()
        p = _dump(profile)
        checks = p.get("checks", [p]) if isinstance(p, dict) else p
        return checks if isinstance(checks, list) else [checks]
    except Exception:
        return None
