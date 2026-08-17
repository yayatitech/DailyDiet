# Deploy DailyDiet on a DigitalOcean droplet

Stack: **Docker Compose** (Postgres + API on `127.0.0.1:3000`) → **nginx** (SPA + reverse proxy) → **Certbot** (HTTPS).

## Prerequisites

- Ubuntu droplet, SSH access
- Repo cloned (e.g. `~/DailyDiet`)
- Domain DNS **A** record → droplet IP (needed for HTTPS)
- Docker Engine + Compose plugin installed
- Node.js available (nvm is fine) for `apps/web` build

## 1. Secrets

```bash
cd ~/DailyDiet
cp .env.prod.example .env.prod
nano .env.prod   # set POSTGRES_PASSWORD, JWT_SECRET, ADMIN_API_KEY, CORS_ORIGINS
```

`CORS_ORIGINS` must match the public URL, e.g. `https://your.domain.com`.

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

## 3. Build web

```bash
cd ~/DailyDiet/apps/web
npm install
npm run build
# outputs apps/web/dist
```

## 4. nginx

```bash
sudo apt install -y nginx
# edit server_name + root path in the file, then:
sudo cp ~/DailyDiet/deploy/nginx/dailydiet.conf /etc/nginx/sites-available/dailydiet
sudo nano /etc/nginx/sites-available/dailydiet
sudo ln -sf /etc/nginx/sites-available/dailydiet /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

Open firewall ports if using ufw:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

DigitalOcean cloud firewall: allow **22**, **80**, **443** (not 3000/5432).

## 5. HTTPS

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your.domain.com
```

Certbot renews via timer automatically.

## 6. Start on boot (systemd)

```bash
# edit User + WorkingDirectory paths first
sudo cp ~/DailyDiet/deploy/systemd/dailydiet.service /etc/systemd/system/dailydiet.service
sudo nano /etc/systemd/system/dailydiet.service
sudo systemctl daemon-reload
sudo systemctl enable --now dailydiet
```

## Day-2 ops

| Task | Command |
|------|---------|
| Update code | `git pull` → rebuild API → rebuild web → reload nginx |
| Rebuild API | `docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build` |
| Rebuild web | `cd apps/web && npm install && npm run build` |
| Logs | `docker compose -f docker-compose.prod.yml logs -f api` |
| Status | `docker compose -f docker-compose.prod.yml ps` |

Update flow:

```bash
cd ~/DailyDiet
git pull
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
cd apps/web && npm install && npm run build
sudo systemctl reload nginx
```

## Notes

- Postgres is **not** published on the public interface.
- API is only on `127.0.0.1:3000`; browsers hit nginx on 80/443.
- Web uses relative `/v1` paths, so same-origin nginx routing is required.
- Do not commit `.env.prod`.
