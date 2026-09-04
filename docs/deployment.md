# Deployment (private VPS)

Options: localhost/SSH tunnel (`ssh -L 3000:localhost:3000 vps`), Tailscale
(recommended, no public port), Cloudflare Access, or Caddy/Nginx HTTPS.

Caddy example:

```
sklab.example.com {
  reverse_proxy localhost:3000
}
```

Nginx example: proxy `/` → `:3000`, `/api` → `:8787` with TLS.

Compose: `docker compose up --build`. Mount `/srv/sklab/repos:ro` and config
volume. Never bake secrets into images; use env/Docker secrets.

ReproBox note: backend does NOT mount `/var/run/docker.sock` by default.
Prefer native backend on host + frontend container, or explicitly opt into
Docker access with full understanding of the tradeoff.
