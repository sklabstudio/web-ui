"""Protocol Intelligence write-ops via the private ``sklab-protocol`` CLI.

Safety: simulation-only. No live transactions, no signing, no broadcast.
``monitor``/``incident`` read explicit event JSON only. Roots resolve
strictly under SKLAB_PROTOCOLS_ROOT. DTOs are generic (no proprietary
internals cross the boundary).
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from sklab_web.integrations.cli import (
    CliError,
    cli_available,
    require_id,
    resolve_under_root,
    run_cli_json,
    run_cli_text,
)

CLI = "sklab-protocol"
ROOT_ENV = "SKLAB_PROTOCOLS_ROOT"
MAX_SOURCE_CHARS = 256_000
_SOL_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\.sol")


def _root(pid: str) -> str:
    root = resolve_under_root(ROOT_ENV, pid)
    if root is None:
        raise CliError("NOT_FOUND", "Protocol project not found")
    return root


def _run(pid: str, args: list[str], timeout: float = 180.0) -> Any:
    root = _root(pid)
    if not cli_available(CLI):
        raise CliError("MODULE_NOT_INSTALLED", "sklab-protocol CLI not available")
    try:
        return run_cli_json(CLI, [*args, "--json"], timeout=timeout, cwd=root)
    except CliError as exc:
        msg = exc.message.lower()
        if "not found" in msg or "no such" in msg or "unknown" in msg:
            raise CliError("NOT_FOUND", exc.message[:500])
        raise


def project_create(pid: str) -> dict[str, Any]:
    require_id(pid, "protocol")
    base_env = os.environ.get(ROOT_ENV, "").strip()
    if not base_env:
        raise CliError("MODULE_UNAVAILABLE", "SKLAB_PROTOCOLS_ROOT is not configured")
    try:
        base = Path(base_env).expanduser().resolve()
    except Exception:
        raise CliError("MODULE_UNAVAILABLE", "protocol root is invalid")
    dest = (base / pid).resolve()
    if base not in dest.parents:
        raise CliError("BAD_REQUEST", "invalid protocol id")
    if dest.exists():
        raise CliError("BAD_REQUEST", "protocol project already exists")
    if not cli_available(CLI):
        raise CliError("MODULE_NOT_INSTALLED", "sklab-protocol CLI not available")
    dest.mkdir(parents=True, exist_ok=False)
    try:
        data = run_cli_json(
            CLI, ["init", str(dest), "--protocol-id", pid, "--json"], timeout=60.0, cwd=str(base)
        )
    except CliError as exc:
        raise CliError(exc.code, exc.message)
    return (
        {"id": pid, "ok": True, "init": data} if isinstance(data, dict) else {"id": pid, "ok": True}
    )


def project_import(pid: str, files: dict[str, str]) -> dict[str, Any]:
    """Initialize a local protocol workspace and import bounded Solidity files."""
    require_id(pid, "protocol")
    if not files:
        raise CliError("BAD_REQUEST", "no Solidity source files provided")
    base_env = os.environ.get(ROOT_ENV, "").strip()
    if not base_env:
        raise CliError("MODULE_UNAVAILABLE", "SKLAB_PROTOCOLS_ROOT is not configured")
    base = Path(base_env).expanduser().resolve()
    dest = (base / pid).resolve()
    if base not in dest.parents:
        raise CliError("BAD_REQUEST", "invalid protocol id")
    if dest.exists():
        raise CliError("BAD_REQUEST", "protocol project already exists")
    if not cli_available(CLI):
        raise CliError("MODULE_NOT_INSTALLED", "sklab-protocol CLI not available")
    dest.mkdir(parents=True, exist_ok=False)
    try:
        run_cli_json(
            CLI,
            ["init", str(dest), "--protocol-id", pid, "--json"],
            timeout=60.0,
            cwd=str(base),
        )
        src_dir = dest / "src"
        src_dir.mkdir()
        written: list[str] = []
        for name, content in files.items():
            if not _SOL_RE.fullmatch(name or ""):
                raise CliError("BAD_REQUEST", f"invalid Solidity filename: {name}")
            if len(content or "") > MAX_SOURCE_CHARS:
                raise CliError("BAD_REQUEST", f"source too large: {name}")
            target = (src_dir / name).resolve()
            if src_dir not in target.parents:
                raise CliError("BAD_REQUEST", f"invalid filename: {name}")
            target.write_text(content, encoding="utf-8")
            written.append(f"src/{name}")
    except CliError:
        import shutil

        shutil.rmtree(dest, ignore_errors=True)
        raise
    except Exception as exc:
        import shutil

        shutil.rmtree(dest, ignore_errors=True)
        raise CliError("MODULE_UNAVAILABLE", f"protocol import failed: {exc}")
    return {"id": pid, "ok": True, "files": written}


def build_ir(pid: str) -> Any:
    return _run(pid, ["ir"])


def build_map(pid: str) -> Any:
    return _run(pid, ["map"])


def assets(pid: str) -> Any:
    return _run(pid, ["assets"])


def assets_dto(pid: str) -> list[dict[str, Any]] | None:
    """Normalized asset-flow rows (stable keys for the UI)."""
    data = assets(pid)
    rows: Any = []
    if isinstance(data, dict):
        rows = data.get("flows", data.get("assets", []))
    elif isinstance(data, list):
        rows = data
    if not isinstance(rows, list):
        return None
    out: list[dict[str, Any]] = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        out.append(
            {
                "asset": str(r.get("asset", "")),
                "source": str(r.get("source", "")),
                "destination": str(r.get("destination", "")),
                "trigger": str(r.get("trigger", "")),
                "authority": str(r.get("authority", "")),
                "constraint": str(r.get("constraint", r.get("expected_invariant", "")))[:300],
                "live": True,
            }
        )
    return out or None


def authorities(pid: str) -> Any:
    return _run(pid, ["authorities"])


def authorities_dto(pid: str) -> list[dict[str, Any]] | None:
    """Normalized capability DTOs (stable keys for the UI)."""
    data = authorities(pid)
    caps: Any = []
    if isinstance(data, dict):
        caps = data.get("capabilities", data.get("authorities", []))
    elif isinstance(data, list):
        caps = data
    if not isinstance(caps, list):
        return None
    blast: dict[str, Any] = {}
    if isinstance(data, dict):
        for b in data.get("blast_radius", []) or []:
            if isinstance(b, dict) and b.get("authority"):
                blast[str(b["authority"])] = b
    out: list[dict[str, Any]] = []
    for c in caps:
        if not isinstance(c, dict):
            continue
        auth = str(c.get("authority", ""))
        b = blast.get(auth, {})
        reach = b.get("reachable", []) if isinstance(b, dict) else []
        out.append(
            {
                "authority": auth,
                "capability": str(c.get("capability", c.get("normalized", ""))),
                "target": str(c.get("target", "")),
                "evidence": str(c.get("evidence", ""))[:500],
                "confidence": str(c.get("confidence", "UNKNOWN")),
                "transitive": bool(c.get("transitive", False)),
                "blast_radius": (
                    f"{len(reach)} reachable" if isinstance(reach, list) else str(reach)
                ),
                "live": True,
            }
        )
    return out or None


def dependencies(pid: str) -> Any:
    # dependency view derives from inspect + map; expose both honestly
    insp = _run(pid, ["inspect"])
    return insp


def specs(pid: str) -> Any:
    return _run(pid, ["specs"])


def invariants(pid: str) -> Any:
    return _run(pid, ["invariants"])


def threat_model(pid: str) -> Any:
    return _run(pid, ["threat-model"])


def audit(pid: str) -> Any:
    return _run(pid, ["audit"], timeout=600.0)


def simulate(pid: str, seed: int = 42, runs: int = 20) -> Any:
    seed = max(0, min(int(seed or 42), 2**31 - 1))
    runs = max(1, min(int(runs or 20), 10000))
    return _run(pid, ["simulate", "--seed", str(seed), "--runs", str(runs)], timeout=600.0)


def economic(pid: str, scenario: str = "price-drop") -> Any:
    scenario = (scenario or "price-drop").strip()[:64]
    return _run(pid, ["economic", scenario], timeout=300.0)


def historical_regression(pid: str) -> Any:
    return _run(pid, ["historical-regression"], timeout=600.0)


def upgrade_review(pid: str, old: str = "", new: str = "") -> Any:
    old, new = (old or "").strip()[:128], (new or "").strip()[:128]
    if not old or not new:
        raise CliError(
            "BAD_REQUEST",
            "upgrade-review compares two versions: provide old and new (paths or refs).",
        )
    return _run(pid, ["upgrade-review", old, new], timeout=300.0)


def change_impact(pid: str) -> Any:
    return _run(pid, ["change-impact"], timeout=300.0)


def deployment_guard(pid: str) -> Any:
    return _run(pid, ["deployment-guard"], timeout=300.0)


def verify(pid: str) -> Any:
    return _run(pid, ["verify"], timeout=600.0)


def findings(pid: str) -> Any:
    return _run(pid, ["findings"], timeout=180.0)


def evidence(pid: str) -> Any:
    return _run(pid, ["evidence"], timeout=180.0)


def assure(pid: str) -> Any:
    return _run(pid, ["assure"], timeout=600.0)


def monitor(pid: str) -> Any:
    return _run(pid, ["monitor"], timeout=120.0)


def incident(pid: str) -> Any:
    return _run(pid, ["incident"], timeout=120.0)


def report(pid: str) -> dict[str, Any]:
    """Report has no --json; run bounded and return labeled log text."""
    root = _root(pid)
    if not cli_available(CLI):
        raise CliError("MODULE_NOT_INSTALLED", "sklab-protocol CLI not available")
    return run_cli_text(CLI, ["report"], timeout=300.0, cwd=root)


def doctor() -> dict[str, Any] | None:
    if not cli_available(CLI):
        return None
    try:
        data = run_cli_json(CLI, ["doctor", "--json"], timeout=60.0)
    except CliError:
        return None
    return data if isinstance(data, dict) else None
