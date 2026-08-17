# DailyDiet — Work in Progress

**Last updated:** 2026-07-21  
**Project:** DailyDiet v2 — `/home/pingmepls/projects/DailyDiet`  
**Requirements version:** 2.6 (FR-01–37)

Living log of what has been built, what was done recently, and what is next. Update this file whenever you finish a feature, import, or significant fix.

| Related docs | Purpose |
|--------------|---------|
| [REQUIREMENTS.md](REQUIREMENTS.md) | Formal FR/NFR spec |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, API, routes |
| [../README.md](../README.md) | Quick start & dev commands |
| [../deploy/README.md](../deploy/README.md) | DigitalOcean droplet deploy (Compose + nginx + HTTPS) |

---

## Current status (snapshot)

| Area | State |
|------|-------|
| **Backend API** | FastAPI + PostgreSQL — running via Docker (`:3000`) |
| **Web app** | React + Vite + React Router — `npm run dev` (`:5173`) |
| **Auth** | JWT login/register; guest read-only template browse |
| **Recipes** | Rich pages, images, hybrid links, Edit-mode combobox, list name search |
| **Meal plan data** | 26 weeks in DB; Week 5 complete; Week 6 Mon–Thu only |
| **Mobile (Expo)** | Scaffold only — not wired for guest/auth UX |
| **Deploy (VPS)** | Prod Compose + nginx + systemd + Certbot runbook added; droplet bring-up in progress |
| **Tests** | None automated yet |

---

## Completed work (chronological)

### Phase 1 — Client–server re-architecture

- Migrated from static localStorage SPA to FastAPI + PostgreSQL + React
- Weekly / day / today views, 8 time slots, meal edits, notes, completions
- Excel → JSON import pipeline (`scripts/import_xlsm.py`)
- Admin seed from `public/data/meal-plan.json` + `recipe-catalog.json`
- Docker Compose: Postgres + API (no web container)

### Meal items & recipes

- Newline-delimited meal items per slot; recipe catalog in PostgreSQL
- View vs Edit modes (checkboxes in View; editable meals in Edit)
- Today dashboard with auto week selection
- **Rich recipes (FR-30–34):** `display_name`, ingredients, instructions, images, `external_url`
- Recipe pages: `/recipes`, `/recipes/new`, `/recipes/:id`, `/recipes/:id/edit`
- Hybrid meal links: internal `/recipes/:id` when content exists, else external URL
- **Recipe combobox (FR-35)** in Edit mode with “Create recipe” shortcut
- **Recipe list search** — filter `/recipes` by name / display name as you type

### Auth & guest mode (FR-36–37)

- `/login` page; header Log in / Sign up (top right on all pages)
- Guest: template plan read-only (no Edit, checkboxes, import/export)
- Logged in: personal overrides, completions, import/export
- `ALLOW_ANONYMOUS_DEV_USER=false` by default

### Documentation

- Rewrote `docs/ARCHITECTURE.md`, updated `README.md`, bumped `docs/REQUIREMENTS.md` to v2.6

### Deploy — DigitalOcean droplet

- SSH + repo clone on droplet already done by operator
- Added production stack files (not wired into local `docker compose` default):
  - `docker-compose.prod.yml` — Postgres + API; API bound to `127.0.0.1:3000` only; no backend source bind-mount; recipes volume persisted
  - `.env.prod.example` → copy to `.env.prod` (gitignored) for secrets / `CORS_ORIGINS`
  - `deploy/nginx/dailydiet.conf` — serves `apps/web/dist`, proxies `/v1`, `/static`, `/health` (and optional `/docs`)
  - `deploy/systemd/dailydiet.service` — start Compose on boot
  - `deploy/README.md` — full droplet runbook (secrets → Compose → seed → web build → nginx → Certbot → systemd)
- Web still built on host (`npm run build`); nginx is the public edge (80/443). Same-origin proxy so relative `/v1` fetches work.

### Bug fixes & dev ergonomics

- Recipe create: `external_url` vs legacy `recipe_url`; empty URL omitted from API body
- Docker: `./backend` volume mount; `startup.py` on boot (migrate only, not destructive seed)
- Mandatory field asterisks on recipe admin forms

---

## Latest session — Droplet deploy scaffolding (2026-07-21)

**Goal:** Durable DigitalOcean droplet run (Compose API/DB + nginx SPA + HTTPS + boot persistence).

**Done:**

1. Confirmed local stack remains: `docker compose up -d` (dev) + `apps/web` via Vite
2. Added prod artifacts listed under **Deploy — DigitalOcean droplet** above
3. Documented operator steps in `deploy/README.md` (domain A record required for Certbot)

**Still on droplet (operator):**

- [ ] `cp .env.prod.example .env.prod` and set real secrets / `CORS_ORIGINS`
- [ ] `docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build`
- [ ] First-time seed via `POST /v1/admin/seed` with prod `ADMIN_API_KEY`
- [ ] `cd apps/web && npm install && npm run build`
- [ ] Install nginx site from `deploy/nginx/dailydiet.conf` (edit `server_name` + `root`)
- [ ] Certbot HTTPS + ufw / DO firewall (22, 80, 443 only)
- [ ] Enable `deploy/systemd/dailydiet.service` (edit `User` / paths)

---

## Prior session — Excel import (Week 5–6)

**Goal:** Load updated meal plan from downloaded `simple_weekly_meal_plan_extendable.xlsm`.

**Done:**

1. Backed up repo xlsm → `simple_weekly_meal_plan_extendable.xlsm.bak`
2. Copied from `C:\Users\write\Downloads\simple_weekly_meal_plan_extendable.xlsm` to repo root
3. Ran `python3 scripts/import_xlsm.py` → `public/data/meal-plan.json` (26 weeks)
4. Reseeded PostgreSQL:
   - `POST /v1/admin/seed` alone used **stale JSON inside Docker image**
   - Fix used: `docker cp public/data/meal-plan.json dailydiet-api:/app/public/data/meal-plan.json` then `docker exec dailydiet-api python init_db.py`
5. Verified in browser — Week 5 and Week 6 show new meals

**Data result:**

| Week | Status |
|------|--------|
| **Week 5** (`week-5`, June 1 2026) | Fully populated Mon–Sun |
| **Week 6** (`week-6`, June 8 2026) | Mon–Thu populated; **Fri–Sun empty in source Excel** |

**Note:** Re-seed wipes all user overrides, notes, and completions. Export first (`GET /v1/export` while logged in) if you need to keep personal data.

---

## Known gotchas

- **Docker seed:** API container may have old `meal-plan.json` baked in at build time. After Excel import, copy JSON into container or re-seed from host before relying on API data.
- **`docker compose up --build`:** May fail if `docker-buildx` missing; use volume-mounted backend or install buildx.
- **`init_db.py` vs `startup.py`:** `init_db.py` = full destructive seed; `startup.py` = schema + migrate only.
- **Web not in Docker:** Run `cd apps/web && npm run dev` separately (local); on droplet, build static and serve via nginx.
- **Admin key (local):** `dev-admin-key` for `/v1/admin/*` and recipe admin UI.
- **Prod vs local Compose:** Use `docker-compose.prod.yml` + `.env.prod` on the droplet; do not reuse local `JWT_SECRET` / `ADMIN_API_KEY` / DB password.
- **Prod CORS:** Must match public origin (e.g. `https://your.domain.com`). Same-origin nginx makes relative `/v1` work; wrong `CORS_ORIGINS` still breaks if the browser origin differs.
- **Do not publish 3000/5432** on the droplet firewall — only 22, 80, 443.

---

## Next up (suggested)

- [ ] Finish droplet checklist under **Latest session** (secrets → Compose → seed → web → nginx → Certbot → systemd)
- [ ] Fill **Week 6 Fri–Sun** in Excel, then re-import + reseed
- [ ] Add recipe catalog entries for new meal names (via `/recipes` or `recipe-catalog.json`)
- [ ] Re-login and re-track meals if re-seed cleared personal data
- [ ] Mobile: JWT auth + week/day screens (Phase 3)
- [ ] Optional: `--input` flag on `import_xlsm.py` to import without copying xlsm to repo root
- [ ] Optional: mount `./public/data` in Docker so admin seed always sees latest JSON

---

## Repeatable commands

### After Excel changes

```bash
cd /home/pingmepls/projects/DailyDiet
python3 scripts/import_xlsm.py

# If API runs in Docker:
docker cp public/data/meal-plan.json dailydiet-api:/app/public/data/meal-plan.json
docker exec dailydiet-api python init_db.py

# Or local venv:
cd backend && python3 init_db.py
```

### Dev servers

```bash
docker compose up -d          # Postgres + API :3000
cd apps/web && npm run dev    # Web :5173
```

### Droplet (prod)

```bash
# Full runbook: deploy/README.md
cd ~/DailyDiet
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
cd apps/web && npm install && npm run build
# then nginx + certbot + systemd per deploy/README.md
```

---

## How to keep this file in sync

Update **this file** when you:

- Ship a feature or fix worth remembering
- Import new Excel data or change seed files
- Hit a new gotcha or change dev workflow
- Complete or add items under **Next up**

Also update formal docs when behavior changes:

| Change | Also update |
|--------|-------------|
| New requirement / behavior | `docs/REQUIREMENTS.md` |
| API, auth, routes, schema | `docs/ARCHITECTURE.md` |
| Setup / quick start | `README.md` |
| Droplet / production deploy | `deploy/README.md` (+ prod Compose / nginx / systemd) |
| Session progress / “where I left off” | **this file** |

---

## Revision log

| Date | Change |
|------|--------|
| 2026-07-21 | Droplet deploy scaffolding: `docker-compose.prod.yml`, `.env.prod.example`, `deploy/` (nginx, systemd, README); WIP checklist for bring-up |
| 2026-07-19 | Recipe list page: client-side name search bar (`/recipes`) |
| 2026-07-11 | Created work log; captured v2.6 feature set + Week 5–6 Excel import session |
