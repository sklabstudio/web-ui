"""Path safety: allowed-roots enforcement, traversal rejection."""
from __future__ import annotations

import ipaddress
import re
from pathlib import Path
from urllib.parse import urlparse


def is_path_allowed(candidate: str, allowed_roots: list[str]) -> bool:
    try:
        cand = Path(candidate).resolve()
    except Exception:
        return False
    for root in allowed_roots:
        try:
            r = Path(root).resolve()
        except Exception:
            continue
        try:
            if cand == r or r in cand.parents:
                return True
        except Exception:
            continue
    return False


def reject_traversal(candidate: str) -> bool:
    """Return True if the raw string looks like traversal/absolute-escape attempt."""
    c = candidate.replace("\\", "/")
    if ".." in c.split("/"):
        return True
    return False


def validate_repo_path(candidate: str, allowed_roots: list[str]) -> tuple[bool, str]:
    if not candidate:
        return False, "empty path"
    if reject_traversal(candidate):
        return False, "path traversal rejected"
    # Block filesystem roots
    norm = candidate.replace("\\", "/").rstrip("/")
    if norm in ("", "/", "C:", "C:/", "C:/Windows", "/etc"):
        return False, "path not allowed"
    if norm in ("/etc", "/etc/passwd", "C:/Windows", "C:\\Windows"):
        return False, "path not allowed"
    if not is_path_allowed(candidate, allowed_roots):
        return False, "path outside allowed roots"
    return True, "ok"


def validate_public_repo_url(value: str) -> tuple[bool, str]:
    """Accept public HTTP(S) Git URLs without credentials or local targets."""
    try:
        parsed = urlparse(value.strip())
    except Exception:
        return False, "invalid repository URL"
    if parsed.scheme not in ("http", "https"):
        return False, "repository URL must use http or https"
    if not parsed.hostname or parsed.username or parsed.password:
        return False, "repository URL must not contain credentials"
    if parsed.query or parsed.fragment:
        return False, "repository URL must not contain query or fragment data"
    host = parsed.hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain", "metadata.google.internal"} or host.endswith(
        ".local"
    ):
        return False, "local repository hosts are not allowed"
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and (address.is_private or address.is_loopback or address.is_link_local):
        return False, "private repository hosts are not allowed"
    if not parsed.path.strip("/"):
        return False, "repository URL must include a repository path"
    return True, "ok"


def safe_repo_name(url: str, requested: str | None = None) -> str:
    """Return a single safe child name for a cloned repository."""
    raw = (requested or Path(urlparse(url).path.rstrip("/")).name or "repo").strip()
    if raw.lower().endswith(".git"):
        raw = raw[:-4]
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip(".-_")[:80]
    if not name or name in {".", ".."}:
        raise ValueError("repository destination is invalid")
    return name
