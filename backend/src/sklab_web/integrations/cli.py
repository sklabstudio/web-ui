"""Shared helpers for delegating to SKLab CLIs with machine-readable output.

Rules (never violated):
- Only ``--json`` machine-readable output is parsed. Rich/human output is
  never parsed; it may only be returned as bounded, labeled log text.
- No shell. Fixed argv only. Timeouts always. Cwd is allow-listed.
- IDs are validated ([A-Za-z0-9][A-Za-z0-9-_]{0,63}) to block traversal.
- Failures map to typed CliError (caller maps to normalized API codes).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

DEFAULT_TIMEOUT = 120.0
MAX_TEXT_CHARS = 12000

_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9-_]{0,63}")

_EXTRA_BIN_DIRS = (
    Path.home() / ".local" / "bin",
    Path.home() / ".foundry" / "bin",
)


def valid_id(value: str) -> bool:
    return bool(_ID_RE.fullmatch(value or ""))


def require_id(value: str, what: str = "id") -> str:
    if not valid_id(value):
        raise CliError(
            "BAD_REQUEST", f"Invalid {what}: must match [A-Za-z0-9][A-Za-z0-9-_]* (<=64)"
        )
    return value


def _augmented_env() -> dict[str, str]:
    env = dict(os.environ)
    extra = [str(p) for p in _EXTRA_BIN_DIRS if p.is_dir()]
    if extra:
        env["PATH"] = os.pathsep.join(extra + [env.get("PATH", "")])
    return env


def cli_available(name: str) -> bool:
    if shutil.which(name):
        return True
    return any((p / name).exists() for p in _EXTRA_BIN_DIRS if p.is_dir())


class CliError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def run_cli_json(
    cli: str,
    args: list[str],
    timeout: float = DEFAULT_TIMEOUT,
    cwd: str | None = None,
) -> Any:
    """Run ``cli args`` (must include --json) and parse stdout as JSON."""
    if not cli_available(cli):
        raise CliError("MODULE_NOT_INSTALLED", f"CLI not available: {cli}")
    try:
        proc = subprocess.run(
            [cli, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=_augmented_env(),
        )
    except subprocess.TimeoutExpired:
        raise CliError("MODULE_UNAVAILABLE", f"{cli} timed out after {timeout:.0f}s")
    except Exception as exc:
        raise CliError("MODULE_UNAVAILABLE", f"{cli} failed to start: {exc}")
    out = (proc.stdout or "").strip()
    if proc.returncode != 0:
        detail = ((proc.stderr or "") + "\n" + out).strip()[:2000]
        raise CliError("MODULE_UNAVAILABLE", f"{cli} exited {proc.returncode}: {detail}")
    if not out:
        raise CliError("MODULE_UNAVAILABLE", f"{cli} returned empty output")
    try:
        return json.loads(out)
    except Exception:
        raise CliError("MODULE_UNAVAILABLE", f"{cli} returned non-JSON output")


def run_cli_text(
    cli: str,
    args: list[str],
    timeout: float = DEFAULT_TIMEOUT,
    cwd: str | None = None,
    max_chars: int = MAX_TEXT_CHARS,
) -> dict[str, Any]:
    """Run a CLI without --json; return bounded raw log text (labeled, real)."""
    if not cli_available(cli):
        raise CliError("MODULE_NOT_INSTALLED", f"CLI not available: {cli}")
    try:
        proc = subprocess.run(
            [cli, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=_augmented_env(),
        )
    except subprocess.TimeoutExpired:
        raise CliError("MODULE_UNAVAILABLE", f"{cli} timed out after {timeout:.0f}s")
    except Exception as exc:
        raise CliError("MODULE_UNAVAILABLE", f"{cli} failed to start: {exc}")
    log = ((proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")).strip()
    if len(log) > max_chars:
        log = log[:max_chars] + f"\n…[truncated to {max_chars} chars]"
    return {"ok": proc.returncode == 0, "exit_code": proc.returncode, "log": log}


def resolve_under_root(env_var: str, pid: str, *, must_exist: bool = True) -> str | None:
    """Map an id to a real directory under an operator-configured root.

    Returns None when unresolvable (caller falls back honestly).
    """
    require_id(pid)
    root_env = os.environ.get(env_var, "").strip()
    if not root_env:
        return None
    try:
        base = Path(root_env).expanduser().resolve()
    except Exception:
        return None
    candidate = (base / pid).resolve()
    if base not in candidate.parents:
        return None
    if must_exist and not candidate.is_dir():
        return None
    return str(candidate)
