# Deploy DailyDiet on a DigitalOcean droplet

Full runbook (architecture, Cloudflare 521, nginx, Certbot, updates): **[docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md)**.

This page is a short command cheat sheet. Production path on the droplet is `/opt/apps/DailyDiet` (replace `~/DailyDiet` below if that is where you cloned).

Stack: **Docker Compose** (Postgres + API on `127.0.0.1:3000`) → **nginx** (web + API hosts) → **Certbot** (HTTPS).

| Host | Role |
|------|------|
| `https://diet.yayati-labs.com` | React SPA (`apps/web/dist`) |
| `https://api.diet.yayati-labs.com` | FastAPI reverse proxy → `:3000` |

## Prerequisites

- Ubuntu droplet, SSH access
- Repo cloned (e.g. `~/DailyDiet`)
- DNS **A** records for both hostnames → droplet IP
- Docker Engine + Compose plugin
- Node.js (nvm is fine) for `apps/web` build
- Firewall: **22**, **80**, **443** only (not 3000/5432)

## 1. Secrets

```bash
cd ~/DailyDiet
cp .env.prod.example .env.prod
nano .env.prod   # set POSTGRES_PASSWORD, JWT_SECRET, ADMIN_API_KEY, CORS_ORIGINS
```

`CORS_ORIGINS` must be the web origin: `https://diet.yayati-labs.com`.

## 2. Start API + DB

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
curl http://127.0.0.1:3000/health
```

First-time seed:

```bash
curl -X POST http://127.0.0.1:3000/v1/admin/seed \
  -H "X-Admin-Key: $(grep ADMIN_API_KEY .env.prod | cut -d= -f2)"
```

## 3. Build web (API base URL required)

Prod split needs the API host baked in at build time:

```bash
cd ~/DailyDiet/apps/web
npm install
VITE_API_BASE_URL=https://api.diet.yayati-labs.com npm run build
# outputs apps/web/dist
```

Leave `VITE_API_BASE_URL` unset for local `npm run dev` (Vite proxy).

## 4. nginx

```bash
sudo apt install -y nginx
sudo cp ~/DailyDiet/deploy/nginx/dailydiet.conf /etc/nginx/sites-available/dailydiet
sudo nano /etc/nginx/sites-available/dailydiet
# set root to absolute path of apps/web/dist (replace YOUR_USER)
sudo ln -sf /etc/nginx/sites-available/dailydiet /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

DigitalOcean cloud firewall: allow **22**, **80**, **443**.

## 5. HTTPS (both names)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d diet.yayati-labs.com -d api.diet.yayati-labs.com
```

Certbot renews via timer automatically.

## 6. Start on boot (systemd)

```bash
sudo cp ~/DailyDiet/deploy/systemd/dailydiet.service /etc/systemd/system/dailydiet.service
sudo nano /etc/systemd/system/dailydiet.service   # edit User + WorkingDirectory
sudo systemctl daemon-reload
sudo systemctl enable --now dailydiet
```

## Cutover / update on the droplet

```bash
cd ~/DailyDiet
git pull

# CORS / secrets if changed
nano .env.prod   # CORS_ORIGINS=https://diet.yayati-labs.com

docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

cd apps/web
npm install
VITE_API_BASE_URL=https://api.diet.yayati-labs.com npm run build

sudo cp ~/DailyDiet/deploy/nginx/dailydiet.conf /etc/nginx/sites-available/dailydiet
# re-apply YOUR_USER root path if the template overwrote it
sudo nginx -t && sudo systemctl reload nginx
```

First-time certs (if not done yet):

```bash
sudo certbot --nginx -d diet.yayati-labs.com -d api.diet.yayati-labs.com
```

## Validation

```bash
curl -I https://diet.yayati-labs.com/
curl https://api.diet.yayati-labs.com/health
```

In the browser: open `https://diet.yayati-labs.com`, confirm Network tab calls go to `api.diet.yayati-labs.com`, login works, recipe images load (no CORS errors).

## Day-2 ops

| Task | Command |
|------|---------|
| Rebuild API | `docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build` |
| Rebuild web | `cd apps/web && VITE_API_BASE_URL=https://api.diet.yayati-labs.com npm run build` |
| Logs | `docker compose -f docker-compose.prod.yml logs -f api` |
| Status | `docker compose -f docker-compose.prod.yml ps` |

## Notes

- Postgres is **not** published on the public interface.
- API is only on `127.0.0.1:3000`; browsers hit nginx on 80/443.
- Web calls absolute API URLs via `VITE_API_BASE_URL` (rebuild required after changing the API host).
- Do not commit `.env.prod`.
