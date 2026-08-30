# DailyDiet — DigitalOcean droplet deployment

Production runbook for hosting DailyDiet on an Ubuntu droplet, with nginx as the public edge and optional Cloudflare DNS/proxy.

Canonical app path on the droplet: **`/opt/apps/DailyDiet`**. Repo templates in `deploy/` still use `YOUR_USER` placeholders — replace them with this path (and a non-root user if you are not running as `root`).

| Public host | Role |
|-------------|------|
| `https://diet.yayati-labs.com` | React SPA (`apps/web/dist`) |
| `https://api.diet.yayati-labs.com` | FastAPI via nginx → `127.0.0.1:3000` |

Related files:

- [`docker-compose.prod.yml`](../docker-compose.prod.yml) — Postgres + API
- [`.env.prod.example`](../.env.prod.example) — secrets template (copy to `.env.prod`, never commit)
- [`deploy/nginx/dailydiet.conf`](../deploy/nginx/dailydiet.conf) — HTTP vhosts
- [`deploy/systemd/dailydiet.service`](../deploy/systemd/dailydiet.service) — start Compose on boot
- [`deploy/README.md`](../deploy/README.md) — short command cheat sheet

---

## 1. High-level architecture

The web client is **not** in Docker. Compose runs Postgres and the API only. nginx serves the built SPA and reverse-proxies the API. Browsers never talk to port `3000`.

```
                    Internet
                        |
                        v
              +-------------------+
              | Cloudflare (opt.) |
              | DNS + orange cloud|
              | SSL/TLS Full strict|
              +-------------------+
                        |
                   80 / 443
                        |
                        v
              +-------------------+
              | Ubuntu droplet    |
              | nginx             |
              |  diet.*  → static |
              |  api.*   → :3000  |
              +---------+---------+
                        |
              127.0.0.1:3000
                        |
              +---------v---------+
              | Docker Compose    |
              |                   |
              |  dailydiet-api    |---- TCP ----+
              |  (FastAPI :3000)  |             |
              |                   |             v
              |  dailydiet-db     |      postgres:5432
              |  (Postgres 16)    |      (docker network only)
              +-------------------+
```

```mermaid
flowchart LR
  browser["Browser"]
  cf["Cloudflare proxy"]
  nginx["nginx :80/:443"]
  spa["apps/web/dist"]
  api["dailydiet-api :3000"]
  pg[("dailydiet-db")]

  browser -->|"HTTPS diet.yayati-labs.com"| cf
  browser -->|"HTTPS api.diet.yayati-labs.com"| cf
  cf --> nginx
  nginx -->|"try_files SPA"| spa
  nginx -->|"proxy_pass"| api
  api --> pg
```

### Trust boundaries

| Surface | Binding | Public? |
|---------|---------|---------|
| nginx HTTP/HTTPS | `0.0.0.0:80` and `:443` | Yes (Cloudflare and/or internet) |
| FastAPI | `127.0.0.1:3000` only | No |
| Postgres | Docker network `dailydiet_default`, no host port | No |

### Request flow

1. Browser loads `https://diet.yayati-labs.com` → nginx serves `apps/web/dist` (`try_files` → `index.html` for client routes).
2. SPA calls `https://api.diet.yayati-labs.com/...` because `VITE_API_BASE_URL` was set at **build** time.
3. nginx proxies that host to `http://127.0.0.1:3000`.
4. API uses `DATABASE_URL` host **`postgres`** (Compose service name) on the Docker network, not localhost and not a Unix socket.
5. Recipe images live in `public/recipes` (bind-mounted into the API container) and are served as `/static/...` on the API host.

### What does *not* run in production

- `npm run dev` / Vite `:5173` — local only.
- `docker compose up` (dev compose) — publishes `3000` and `5432` on all interfaces; use **`docker-compose.prod.yml`**.
- `ALLOW_ANONYMOUS_DEV_USER=true`.

---

## 2. Prerequisites

- DigitalOcean Ubuntu 24.04 droplet (2 GB RAM recommended).
- SSH access (this runbook uses `root`; a sudo user in group `docker` is better).
- Domain on Cloudflare (or any DNS) with nameservers delegated.
- Docker Engine + Compose plugin.
- Node.js for the web build (nvm is fine: `export PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH"`).
- Firewall: **22, 80, 443** only. Do not publish **3000** or **5432**.

Install Docker (once), then clone:

```bash
# Docker: follow https://docs.docker.com/engine/install/ubuntu/
sudo usermod -aG docker "$USER"   # if not root; then re-login

sudo mkdir -p /opt/apps
sudo git clone <YOUR_REPO_URL> /opt/apps/DailyDiet
# or: git pull inside /opt/apps/DailyDiet if already cloned
cd /opt/apps/DailyDiet
```

---

## 3. DNS (Cloudflare)

Create **A** records to the droplet IPv4:

| Name | Type | Content | Proxy |
|------|------|---------|--------|
| `diet` | A | droplet IPv4 | Proxied (orange) after TLS works |
| `api.diet` | A | droplet IPv4 | Proxied (orange) after TLS works |

**SSL/TLS → Overview:** **Full (strict)** once origin has a valid certificate. Do not use Flexible long-term (HTTPS to Cloudflare, HTTP to origin).

Grey-cloud (DNS only) both names **while issuing Let's Encrypt certificates**. HTTP-01 fails if the records are orange-clouded.

---

## 4. Secrets

```bash
cd /opt/apps/DailyDiet
cp .env.prod.example .env.prod
nano .env.prod
```

Set:

| Variable | Notes |
|----------|--------|
| `POSTGRES_PASSWORD` | Letters, numbers, `-`, `_` only. Avoid `@ # : / %` — they break `DATABASE_URL` interpolation. |
| `JWT_SECRET` | Long random string; not the local/dev secret. |
| `ADMIN_API_KEY` | Header `X-Admin-Key` for seed and recipe admin. |
| `CORS_ORIGINS` | Exactly `https://diet.yayati-labs.com` (no trailing slash). |
| `ALLOW_ANONYMOUS_DEV_USER` | `false` |

`--env-file .env.prod` on the Compose **CLI** is required so `${POSTGRES_PASSWORD}` interpolates in `docker-compose.prod.yml`. The `env_file:` on the `api` service does not do that interpolation by itself.

Do not commit `.env.prod`.

---

## 5. Start API + database

```bash
cd /opt/apps/DailyDiet
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
docker compose -f docker-compose.prod.yml --env-file .env.prod ps
curl -sS http://127.0.0.1:3000/health
# expect: {"status":"ok"}
```

`curl http://127.0.0.1:3000/health` only works **on the droplet**. Prod binds `127.0.0.1:3000`, not the public interface.

### First-time seed

Use a **single line** (broken `\` pastes cause `Invalid HTTP request received`):

```bash
cd /opt/apps/DailyDiet
KEY=$(grep '^ADMIN_API_KEY=' .env.prod | cut -d= -f2 | tr -d '\r')
curl -sS -X POST http://127.0.0.1:3000/v1/admin/seed -H "X-Admin-Key: $KEY"
```

Expect `{"ok": true, "message": "Database seeded from meal-plan.json and recipe-catalog.json"}`.

`startup.py` (container boot) creates/migrates tables only. Seed loads meal plan + recipe catalog.

### If the API is `Restarting`

```bash
docker logs dailydiet-api --tail 120
```

Common failures:

| Log | Cause | Fix |
|-----|--------|-----|
| `socket "@postgres/.s.PGSQL.5432"` | Malformed `DATABASE_URL` (Unix socket, not TCP) | Recreate API with `--env-file .env.prod`; simple password; URL must be `...@postgres:5432/dailydiet` |
| `password authentication failed for user "dailydiet"` | Volume was initialized with a different password | Empty DB only: `down`, `docker volume rm` the `dailydiet_pg` volume, `up` again. **Destroys data.** |
| `required variable POSTGRES_PASSWORD is missing` | Compose started without `--env-file .env.prod` | Always pass `--env-file .env.prod` |
| API `IPAddress` empty in `docker inspect` | Crash loop; not a separate network bug | Fix the crash; DB should already be on `dailydiet_default` as `172.18.0.x` |

Postgres image **ignores `POSTGRES_PASSWORD` after the first volume init**. Changing `.env.prod` and recreating only `api` does not change the DB password.

---

## 6. Build the web app

There is no Node daemon in production. Build static files; nginx serves `dist`.

```bash
export PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH"   # if using nvm
cd /opt/apps/DailyDiet/apps/web
npm install
VITE_API_BASE_URL=https://api.diet.yayati-labs.com npm run build
ls dist/index.html
```

`VITE_*` is compiled into the JS bundle. Changing the API host requires a rebuild. Leave `VITE_API_BASE_URL` unset for local `npm run dev` (Vite proxy).

---

## 7. nginx

```bash
sudo apt install -y nginx
sudo cp /opt/apps/DailyDiet/deploy/nginx/dailydiet.conf /etc/nginx/sites-available/dailydiet
sudo nano /etc/nginx/sites-available/dailydiet
```

Set **`root /opt/apps/DailyDiet/apps/web/dist;`** in the web server block. Do not leave `/home/YOUR_USER/...`.

Target HTTP config (Certbot later adds `listen 443 ssl` and redirects):

```nginx
# --- Web SPA ---
server {
    listen 80;
    listen [::]:80;
    server_name diet.yayati-labs.com;

    root /opt/apps/DailyDiet/apps/web/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}

# --- API ---
server {
    listen 80;
    listen [::]:80;
    server_name api.diet.yayati-labs.com;

    client_max_body_size 6m;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site, disable the Ubuntu default:

```bash
sudo ln -sf /etc/nginx/sites-available/dailydiet /etc/nginx/sites-enabled/dailydiet
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

`unknown directive "wq!"` means a vim `:wq!` was typed into the file. Delete that line. In **nano**: Ctrl+O, Enter, Ctrl+X.

### Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'    # 80 + 443
sudo ufw enable
sudo ufw status
```

Also open **22, 80, 443** on the DigitalOcean **cloud** firewall (separate from `ufw`). Do not leave Vite `5173` open.

### nginx smoke test (on the droplet)

```bash
ss -tlnp | grep -E ':80|:443|:3000'
curl -sS -H "Host: api.diet.yayati-labs.com" http://127.0.0.1/health
curl -sS -H "Host: diet.yayati-labs.com" http://127.0.0.1/ | head
```

Expect `{"status":"ok"}` and HTML containing `id="root"` (not `Welcome to nginx`).

| Result | Meaning |
|--------|---------|
| `/health` → nginx **404** | API `server_name` block missing or `default` still enabled; request never reached `:3000` |
| `/` → 615-byte welcome page | Wrong `root` or default site |
| `/` → **301** and no `:443` | HTTP→HTTPS redirect before Certbot; origin TLS not up yet |

---

## 8. HTTPS (Certbot + Cloudflare)

Cloudflare **521 Web server is down** means CF reached the droplet IP and the origin **refused the connection**. Typical cause: SSL mode Full/strict while nginx listens on **:80 only** (`ss` shows no `:443`).

1. Grey-cloud `diet` and `api.diet` in Cloudflare.
2. Issue certificates:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d diet.yayati-labs.com -d api.diet.yayati-labs.com
sudo nginx -t && sudo systemctl reload nginx
ss -tlnp | grep 443
```

3. Cloudflare SSL/TLS → **Full (strict)**. Orange-cloud both records.
4. Optional: Always Use HTTPS on.

Certbot installs a systemd timer for renewal. Test: `sudo certbot renew --dry-run`.

**Temporary only:** Flexible mode (CF → origin HTTP :80) can clear 521 before certificates exist. Switch to Full (strict) after Certbot.

**Alternative:** Cloudflare Origin CA certificate installed on nginx, keep Full (strict), skip Let's Encrypt. Not required if Certbot works.

---

## 9. Start Compose on boot (systemd)

```bash
sudo cp /opt/apps/DailyDiet/deploy/systemd/dailydiet.service /etc/systemd/system/dailydiet.service
sudo nano /etc/systemd/system/dailydiet.service
```

Set `WorkingDirectory=/opt/apps/DailyDiet`. Set `User=` to the user that can run Docker (or `root` if that is how you deploy). `Group=docker` if the user is in that group.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now dailydiet
sudo systemctl status dailydiet
```

nginx and Docker have their own enablement; this unit only brings the Compose stack up.

---

## 10. Validate: droplet vs DNS

Work inward → outward. Stop at the first failure.

### A. Process on the droplet

```bash
cd /opt/apps/DailyDiet
docker compose -f docker-compose.prod.yml --env-file .env.prod ps
curl -sS http://127.0.0.1:3000/health
```

Both containers `Up` (API not `Restarting`); `{"status":"ok"}`.

### B. nginx

```bash
sudo nginx -t
sudo systemctl is-active nginx
curl -sS -H "Host: api.diet.yayati-labs.com" http://127.0.0.1/health
curl -sSI -H "Host: diet.yayati-labs.com" http://127.0.0.1/
```

### C. DNS

```bash
curl -sS ifconfig.me; echo
dig +short diet.yayati-labs.com A
dig +short api.diet.yayati-labs.com A
```

Grey-cloud: A records = droplet IPv4. Orange-cloud: Cloudflare anycast IPs; the record **target** in the CF UI must still be the droplet.

### D. From the internet

```bash
curl -sSI https://diet.yayati-labs.com/
curl -sS https://api.diet.yayati-labs.com/health
```

`cf-ray` in headers means the request went through Cloudflare.

### E. Browser

Open `https://diet.yayati-labs.com`. Network tab: XHR/fetch must go to `https://api.diet.yayati-labs.com` (not `:3000` or the web host). Login works; no CORS errors; recipe images load.

| Symptom | Likely cause |
|---------|----------------|
| Local `:3000/health` fails | API container down |
| Host-header nginx `/health` 404 | API vhost not enabled |
| `dig` wrong / empty | DNS not pointed at droplet |
| HTTPS timeout / **522** | CF cannot complete TCP to origin |
| **521** | Origin refused (usually nothing on 443) |
| SSL error, Full strict | No valid origin cert |
| UI loads, API calls wrong host | Rebuild with `VITE_API_BASE_URL` |

---

## 11. Update the stack after code or config changes

SSH to the droplet, `cd /opt/apps/DailyDiet`. Pick the row that matches what changed.

### 11.1 Application code (backend and/or web)

```bash
cd /opt/apps/DailyDiet
git pull

docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

cd apps/web
npm install
VITE_API_BASE_URL=https://api.diet.yayati-labs.com npm run build

sudo nginx -t && sudo systemctl reload nginx
curl -sS http://127.0.0.1:3000/health
```

API image rebuilds from `backend/Dockerfile`. Web is only updated when `dist/` is rebuilt. nginx reload is enough after a web rebuild (no Docker restart required for SPA-only changes).

### 11.2 Web only (UI, `VITE_API_BASE_URL`)

```bash
cd /opt/apps/DailyDiet
git pull
cd apps/web
npm install
VITE_API_BASE_URL=https://api.diet.yayati-labs.com npm run build
# nginx already points at dist; no reload required unless nginx conf also changed
```

### 11.3 API / Docker only (Python, Dockerfile, `public/` seed JSON used at runtime)

```bash
cd /opt/apps/DailyDiet
git pull
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
docker compose -f docker-compose.prod.yml --env-file .env.prod ps
curl -sS http://127.0.0.1:3000/health
```

Schema: container boot runs `startup.py` (create + migrate). It does **not** re-seed. To reload meal plan / catalog from JSON (destructive to seeded content — know what `run_full_seed` does):

```bash
KEY=$(grep '^ADMIN_API_KEY=' .env.prod | cut -d= -f2 | tr -d '\r')
curl -sS -X POST http://127.0.0.1:3000/v1/admin/seed -H "X-Admin-Key: $KEY"
```

### 11.4 `.env.prod` (JWT, CORS, admin key, DB password)

```bash
nano /opt/apps/DailyDiet/.env.prod
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --force-recreate api
```

- **`CORS_ORIGINS`:** recreate API; no web rebuild unless origins in the SPA changed (they do not — CORS is server-side).
- **`JWT_SECRET`:** existing browser tokens invalidate; users log in again.
- **`ADMIN_API_KEY`:** update any clients that send `X-Admin-Key`.
- **`POSTGRES_PASSWORD`:** recreating `api` is not enough if the volume already exists. Either `ALTER USER` inside Postgres or wipe the volume (data loss). See §5.

### 11.5 nginx template (`deploy/nginx/dailydiet.conf`)

```bash
cd /opt/apps/DailyDiet
git pull
sudo cp deploy/nginx/dailydiet.conf /etc/nginx/sites-available/dailydiet
sudo nano /etc/nginx/sites-available/dailydiet
# restore: root /opt/apps/DailyDiet/apps/web/dist;
# restore any ssl_certificate lines Certbot added if the template overwrote them
sudo nginx -t && sudo systemctl reload nginx
```

Copying the template **after** Certbot can wipe SSL server blocks. Prefer editing the live file in `/etc/nginx/sites-available/dailydiet`, or re-run Certbot if TLS stanzas disappeared.

### 11.6 systemd unit

```bash
sudo cp /opt/apps/DailyDiet/deploy/systemd/dailydiet.service /etc/systemd/system/dailydiet.service
sudo nano /etc/systemd/system/dailydiet.service   # WorkingDirectory + User
sudo systemctl daemon-reload
sudo systemctl restart dailydiet
```

### 11.7 Hostnames or TLS names

1. Add/change DNS A records; grey-cloud for HTTP-01.
2. `sudo certbot --nginx -d diet.yayati-labs.com -d api.diet.yayati-labs.com` (include every name).
3. Update `CORS_ORIGINS` and recreate API.
4. Rebuild web with the new `VITE_API_BASE_URL`.
5. Orange-cloud again.

---

## 12. Day-2 operations

| Task | Command |
|------|---------|
| Status | `docker compose -f docker-compose.prod.yml --env-file .env.prod ps` |
| API logs | `docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f api` |
| DB logs | `docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f postgres` |
| Rebuild API | `docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build` |
| Rebuild web | `cd /opt/apps/DailyDiet/apps/web && VITE_API_BASE_URL=https://api.diet.yayati-labs.com npm run build` |
| Stop stack | `docker compose -f docker-compose.prod.yml --env-file .env.prod down` (**no** `-v` unless you intend to delete the DB) |
| nginx logs | `sudo tail -f /var/log/nginx/access.log /var/log/nginx/error.log` |

`down -v` or `docker volume rm` of `dailydiet_*_dailydiet_pg` **deletes all Postgres data**.

---

## 13. Security checklist

- [ ] `.env.prod` not in git
- [ ] API bound to `127.0.0.1:3000` only
- [ ] Postgres not published on the host
- [ ] ufw + DigitalOcean firewall: 22, 80, 443 only
- [ ] Cloudflare Full (strict) after origin certs exist
- [ ] `ALLOW_ANONYMOUS_DEV_USER=false`
- [ ] Distinct `JWT_SECRET` / `ADMIN_API_KEY` from development
