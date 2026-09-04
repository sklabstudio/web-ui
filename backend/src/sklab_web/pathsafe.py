"""Path safety: allowed-roots enforcement, traversal rejection."""
from __future__ import annotations

from pathlib import Path


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
