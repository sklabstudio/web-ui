"""Auth: disabled | token | password modes. Single-user, no multi-tenancy."""
from __future__ import annotations

import hmac
import secrets
import time
from typing import Any

from fastapi import Request
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

_sessions: dict[str, float] = {}
_login_attempts: dict[str, list[float]] = {}


def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_ctx.verify(plain, hashed)
    except Exception:
        return False


def create_session(expiry_seconds: int = 43200) -> str:
    sid = secrets.token_urlsafe(32)
    _sessions[sid] = time.time() + expiry_seconds
    return sid


def validate_session(sid: str | None) -> bool:
    if not sid:
        return False
    exp = _sessions.get(sid)
    if not exp:
        return False
    if exp < time.time():
        _sessions.pop(sid, None)
        return False
    return True


def destroy_session(sid: str | None) -> None:
    if sid:
        _sessions.pop(sid, None)


def rate_limit_ok(key: str, limit: int = 10, window: int = 60) -> bool:
    now = time.time()
    arr = _login_attempts.setdefault(key, [])
    arr[:] = [t for t in arr if now - t < window]
    if len(arr) >= limit:
        return False
    arr.append(now)
    return True


def is_authenticated(request: Request, cfg: Any) -> bool:
    mode = getattr(getattr(cfg, "auth", None), "mode", "disabled")
    if mode == "disabled":
        return True
    if mode == "token":
        auth = request.headers.get("authorization", "")
        expected = getattr(cfg.auth, "token", "")
        if not expected:
            return False
        if auth.startswith("Bearer "):
            got = auth[len("Bearer "):].strip()
            return hmac.compare_digest(got, expected)
        # also allow cookie session created via login
        sid = request.cookies.get("sklab_session")
        return validate_session(sid)
    if mode == "password":
        sid = request.cookies.get("sklab_session")
        return validate_session(sid)
    return False


def clear_state() -> None:
    _sessions.clear()
    _login_attempts.clear()
