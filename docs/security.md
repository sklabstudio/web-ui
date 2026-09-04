# Security

- Single-user auth: `AUTH_MODE=disabled|token|password`. Disabled only for
  localhost/trusted + emits warning. Password: bcrypt, HTTP-only SameSite
  cookie, expiry, login rate-limit, generic errors.
- Secrets: frontend never stores keys in localStorage/sessionStorage; form
  state discarded on submit; backend never returns raw secrets; masked DTOs only.
- Paths: `allowed_roots` allow-list; traversal (`..`), `/`, `/etc`,
  `C:\Windows` rejected.
- No arbitrary command/file/shell/Docker-socket endpoints.
- CORS same-origin default; CSP `default-src 'self'` etc.; XSS-safe text-only
  rendering of logs/diffs/verifier output.
- Audit log for run created/cancelled, approvals, provider changes, settings.
