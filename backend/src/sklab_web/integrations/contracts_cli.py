"""Contract Toolkit write-ops: typed SDK first, ``--json`` CLI second,
bounded CLI log text only where no machine flag exists.

Safety: read/build/test/analyze only. Never deploys, never signs,
never broadcasts. Project roots resolve strictly under
SKLAB_CONTRACTS_ROOT. Uploaded sources are .sol only, size-capped.
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

CLI = "sklab-contract"
ROOT_ENV = "SKLAB_CONTRACTS_ROOT"
MAX_SOURCE_CHARS = 256_000
_SOL_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\.sol")


def _root(pid: str) -> str:
    root = resolve_under_root(ROOT_ENV, pid)
    if root is None:
        raise CliError("NOT_FOUND", "Contract project not found")
    return root


def _toolkit(root: str):  # type: ignore[no-untyped-def]
    from sklab_contract_toolkit.sdk import ContractToolkit

    return ContractToolkit(root=root)


def _sdk_call(pid: str, method: str, *args: Any, **kwargs: Any) -> Any:
    root = _root(pid)
    try:
        return getattr(_toolkit(root), method)(*args, **kwargs)
    except CliError:
        raise
    except FileNotFoundError:
        raise CliError("NOT_FOUND", "Contract project not found")
    except Exception as exc:
        raise CliError("MODULE_UNAVAILABLE", f"toolkit {method} failed: {exc}")


# ---------------- project lifecycle ----------------


def project_create(pid: str, kind: str = "custom") -> dict[str, Any]:
    """Scaffold from SKLab templates (token|nft|vault|staking|custom)."""
    require_id(pid, "project")
    kind = (kind or "custom").strip().lower()
    if kind not in ("token", "nft", "vault", "staking", "custom"):
        raise CliError("BAD_REQUEST", "kind must be token|nft|vault|staking|custom")
    base_env = os.environ.get(ROOT_ENV, "").strip()
    if not base_env:
        raise CliError("MODULE_UNAVAILABLE", "SKLAB_CONTRACTS_ROOT is not configured")
    try:
        base = Path(base_env).expanduser().resolve()
    except Exception:
        raise CliError("MODULE_UNAVAILABLE", "contract root is invalid")
    dest = (base / pid).resolve()
    if base not in dest.parents:
        raise CliError("BAD_REQUEST", "invalid project id")
    if dest.exists():
        raise CliError("BAD_REQUEST", "project already exists")
    if not cli_available(CLI):
        raise CliError("MODULE_NOT_INSTALLED", "sklab-contract CLI not available")
    res = run_cli_text(CLI, ["new", kind, str(dest)], timeout=120.0)
    if not res["ok"]:
        raise CliError("MODULE_UNAVAILABLE", f"scaffold failed: {res['log'][:500]}")
    return {"id": pid, "kind": kind, "path": str(dest), "ok": True, "log": res["log"][:2000]}


def project_import(pid: str, files: dict[str, str]) -> dict[str, Any]:
    """Create a project from uploaded .sol sources (custom kind)."""
    require_id(pid, "project")
    if not files:
        raise CliError("BAD_REQUEST", "no source files provided")
    base_env = os.environ.get(ROOT_ENV, "").strip()
    if not base_env:
        raise CliError("MODULE_UNAVAILABLE", "SKLAB_CONTRACTS_ROOT is not configured")
    try:
        base = Path(base_env).expanduser().resolve()
    except Exception:
        raise CliError("MODULE_UNAVAILABLE", "contract root is invalid")
    dest = (base / pid).resolve()
    if base not in dest.parents:
        raise CliError("BAD_REQUEST", "invalid project id")
    if dest.exists():
        raise CliError("BAD_REQUEST", "project already exists")
    src_dir = dest / "src"
    src_dir.mkdir(parents=True, exist_ok=False)
    written = []
    for name, content in files.items():
        if not _SOL_RE.fullmatch(name or ""):
            raise CliError("BAD_REQUEST", f"invalid solidity filename: {name}")
        if len(content or "") > MAX_SOURCE_CHARS:
            raise CliError("BAD_REQUEST", f"source too large: {name}")
        target = (src_dir / name).resolve()
        if src_dir not in target.parents:
            raise CliError("BAD_REQUEST", f"invalid filename: {name}")
        target.write_text(content, encoding="utf-8")
        written.append(f"src/{name}")
    (dest / "foundry.toml").write_text(
        '[profile.default]\nsrc = "src"\ntest = "test"\nlibs = ["lib"]\n', encoding="utf-8"
    )
    (dest / "test").mkdir(exist_ok=True)
    return {"id": pid, "ok": True, "files": written, "live": True}


# ---------------- typed SDK ops ----------------


def upgrade_review(pid: str) -> dict[str, Any]:
    try:
        res = _sdk_call(pid, "review_upgrade")
        return res if isinstance(res, dict) else {"result": res}
    except CliError:
        return cli_log(pid, ["upgrade-review"])


def storage_layout(pid: str) -> dict[str, Any]:
    return cli_log(pid, ["storage"])


def storage_diff(pid: str) -> dict[str, Any]:
    return cli_log(pid, ["storage-diff"])


def abi_diff(pid: str) -> dict[str, Any]:
    return cli_log(pid, ["abi-diff"])


def diff_storage(pid: str) -> dict[str, Any]:
    try:
        res = _sdk_call(pid, "diff_storage")
        return res if isinstance(res, dict) else {"result": res}
    except CliError:
        return cli_log(pid, ["storage-diff"])


def diff_abi(pid: str) -> dict[str, Any]:
    try:
        res = _sdk_call(pid, "diff_abi")
        return res if isinstance(res, dict) else {"result": res}
    except CliError:
        return cli_log(pid, ["abi-diff"])


def prepare_fix(pid: str, ref: str) -> dict[str, Any]:
    ref = (ref or "").strip()[:128]
    if not ref:
        raise CliError("BAD_REQUEST", "finding ref is required")
    res = _sdk_call(pid, "prepare_fix", ref)
    return res if isinstance(res, dict) else {"patch": str(res)}


def verify_fix(pid: str, ref: str) -> dict[str, Any]:
    ref = (ref or "").strip()[:128]
    if not ref:
        raise CliError("BAD_REQUEST", "finding ref is required")
    res = _sdk_call(pid, "verify_fix", ref)
    return res if isinstance(res, dict) else {"result": res}


def generate_report(pid: str) -> dict[str, Any]:
    res = _sdk_call(pid, "generate_report")
    if isinstance(res, dict):
        return res
    return {"result": str(res)}


def graph_for_root(pid: str, kind: str = "authority") -> dict[str, Any]:
    root = _root(pid)
    if not cli_available(CLI):
        raise CliError("MODULE_NOT_INSTALLED", "sklab-contract CLI not available")
    for argv in (["graph", kind, "--json"], ["graph", "--json"]):
        try:
            data = run_cli_json(CLI, argv, timeout=120.0, cwd=root)
            if isinstance(data, dict):
                return data
        except CliError:
            continue
    raise CliError("MODULE_UNAVAILABLE", "graph export failed")


def cli_log(pid: str, cmd: list[str], timeout: float = 300.0) -> dict[str, Any]:
    """Bounded real CLI log for commands without --json (gas/coverage/...)."""
    root = _root(pid)
    if not cli_available(CLI):
        raise CliError("MODULE_NOT_INSTALLED", "sklab-contract CLI not available")
    return run_cli_text(CLI, cmd, timeout=timeout, cwd=root)


def threat_model(pid: str) -> dict[str, Any]:
    return cli_log(pid, ["threat-model"])


def gas(pid: str) -> dict[str, Any]:
    return cli_log(pid, ["gas"])


def coverage(pid: str) -> dict[str, Any]:
    return cli_log(pid, ["coverage"])
