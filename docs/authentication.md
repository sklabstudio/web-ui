# Authentication

`AUTH_MODE=disabled` — localhost only, warning logged.
`AUTH_MODE=token` — set `SKLAB_AUTH_TOKEN`; login posts token, server sets
`sklab_session` HTTP-only cookie.
`AUTH_MODE=password` — set `SKLAB_AUTH_PASSWORD_HASH` (bcrypt via
`python -c "from sklab_web.auth import hash_password; print(hash_password('...'))"`).

Cookies: HttpOnly, SameSite=Lax, Secure in HTTPS deployments, 12h expiry,
logout clears. Rate-limit 10/min per IP on login.
