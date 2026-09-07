# DailyDiet — Work in Progress

**Last updated:** 2026-09-06  
**Project:** DailyDiet v2 — `/home/pingmepls/projects/DailyDiet`  
**Requirements version:** 2.6 (FR-01–37)

Living log of what has been built, what was done recently, and what is next. Update this file whenever you finish a feature, import, or significant fix.

| Related docs | Purpose |
|--------------|---------|
| [REQUIREMENTS.md](REQUIREMENTS.md) | Formal FR/NFR spec |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, API, routes |
| [DEPLOYMENT.md](DEPLOYMENT.md) | DigitalOcean droplet deploy (architecture, nginx, HTTPS, updates) |
| [MEAL_PLAN_IMPORT.md](MEAL_PLAN_IMPORT.md) | Excel → meal-plan.json → local seed → droplet |
| [../README.md](../README.md) | Quick start & dev commands |
| [../deploy/README.md](../deploy/README.md) | Short droplet command cheat sheet |

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
| **Deploy (VPS)** | Dual-domain nginx: `diet.yayati-labs.com` (SPA) + `api.diet.yayati-labs.com` (API); `VITE_API_BASE_URL` at build |
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
- Production stack:
  - `docker-compose.prod.yml` — Postgres + API; API bound to `127.0.0.1:3000` only; recipes volume persisted
  - `.env.prod.example` → `.env.prod` with `CORS_ORIGINS=https://diet.yayati-labs.com`
  - `deploy/nginx/dailydiet.conf` — **two** server blocks: web SPA + API reverse proxy
  - `deploy/systemd/dailydiet.service` — start Compose on boot
  - `deploy/README.md` — dual-domain runbook + cutover commands
- Domains: `diet.yayati-labs.com` (web), `api.diet.yayati-labs.com` (API)
- Web build uses `VITE_API_BASE_URL=https://api.diet.yayati-labs.com` (relative `/v1` no longer enough for split hosts)
- `mediaUrl()` prefixes `/static/...` recipe images for the API host

### Bug fixes & dev ergonomics

- Recipe create: `external_url` vs legacy `recipe_url`; empty URL omitted from API body
- Docker: `./backend` volume mount; `startup.py` on boot (migrate only, not destructive seed)
- Mandatory field asterisks on recipe admin forms

---

## Latest session — Dual-domain nginx (2026-08-16)

**Goal:** Wire `diet.yayati-labs.com` (web) + `api.diet.yayati-labs.com` (API) for droplet deploy.

**Done (repo):**

1. `VITE_API_BASE_URL` + `mediaUrl()` in `apps/web/src/api.ts`; recipe image pages updated
2. `deploy/nginx/dailydiet.conf` — dual `server` blocks (no `/v1` proxy on web host)
3. `.env.prod.example` CORS → `https://diet.yayati-labs.com`
4. `deploy/README.md` — DNS, build with API base, Certbot both names, cutover + validation

**Still on droplet (operator):**

- [ ] DNS A records for both hosts → droplet IP
- [ ] `.env.prod` with `CORS_ORIGINS=https://diet.yayati-labs.com`; recreate API if CORS changed
- [ ] `VITE_API_BASE_URL=https://api.diet.yayati-labs.com npm run build`
- [ ] Install/update nginx from `deploy/nginx/dailydiet.conf` (set `root` path)
- [ ] `certbot --nginx -d diet.yayati-labs.com -d api.diet.yayati-labs.com`
- [ ] Validate: `curl` web + `/health` on api; browser Network → api host

---

## Prior session — Droplet deploy scaffolding (2026-07-21)

**Goal:** Durable DigitalOcean droplet run (Compose API/DB + nginx SPA + HTTPS + boot persistence).

**Done:**

1. Confirmed local stack remains: `docker compose up -d` (dev) + `apps/web` via Vite
2. Added prod artifacts listed under **Deploy — DigitalOcean droplet** above
3. Documented operator steps in `deploy/README.md` (domain A record required for Certbot)

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
- **Prod CORS:** `https://diet.yayati-labs.com` (web origin). API is on a different host — CORS must allow the web origin.
- **Prod web build:** Must set `VITE_API_BASE_URL=https://api.diet.yayati-labs.com` or the SPA calls the wrong host.
- **Do not publish 3000/5432** on the droplet firewall — only 22, 80, 443.

---

## Next up (suggested)

- [ ] Finish dual-domain droplet checklist under **Latest session**
- [ ] Fill **Week 6 Fri–Sun** in Excel, then re-import + reseed
- [ ] Add recipe catalog entries for new meal names (via `/recipes` or `recipe-catalog.json`)
- [ ] Re-login and re-track meals if re-seed cleared personal data
- [ ] Mobile: JWT auth + week/day screens (Phase 3)
- [ ] Optional: `--input` flag on `import_xlsm.py` to import without copying xlsm to repo root
- [ ] Optional: mount `./public/data` in Docker so admin seed always sees latest JSON

---

## Repeatable commands

### After Excel changes

Full runbook: [MEAL_PLAN_IMPORT.md](MEAL_PLAN_IMPORT.md).

```bash
cd /home/pingmepls/projects/DailyDiet
python3 scripts/import_xlsm.py
docker cp public/data/meal-plan.json dailydiet-api:/app/public/data/meal-plan.json
curl -X POST "http://localhost:3000/v1/admin/seed" \
  -H "X-Admin-Key: dev-admin-key"
```

Omit `?run_import=true` when JSON is already built. Seed is destructive.
### Dev servers

```bash
docker compose up -d          # Postgres + API :3000
cd apps/web && npm run dev    # Web :5173
```

### Droplet (prod, dual-domain)

```bash
# Full runbook: deploy/README.md
cd ~/DailyDiet
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
cd apps/web && VITE_API_BASE_URL=https://api.diet.yayati-labs.com npm run build
# nginx + certbot both names per deploy/README.md
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
| Excel / meal-plan load | `docs/MEAL_PLAN_IMPORT.md` |
| Droplet / production deploy | `docs/DEPLOYMENT.md`, `deploy/README.md` |
| Session progress / “where I left off” | **this file** |

---

## Revision log

| Date | Change |
|------|--------|
| 2026-09-06 | Added `docs/MEAL_PLAN_IMPORT.md` — Excel → JSON → local/droplet seed curl runbook |
| 2026-08-16 | Dual-domain deploy: `diet.` + `api.diet.` nginx, `VITE_API_BASE_URL` / `mediaUrl`, CORS + deploy docs |
| 2026-07-21 | Droplet deploy scaffolding: `docker-compose.prod.yml`, `.env.prod.example`, `deploy/` (nginx, systemd, README); WIP checklist for bring-up |
| 2026-07-19 | Recipe list page: client-side name search bar (`/recipes`) |
| 2026-07-11 | Created work log; captured v2.6 feature set + Week 5–6 Excel import session |
