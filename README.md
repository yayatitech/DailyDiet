# DailyDiet v2

Weekly meal tracker with **Python FastAPI** backend, **PostgreSQL**, **React** web client, and **Expo** mobile scaffold.

| Doc | Purpose |
|-----|---------|
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | Functional & non-functional requirements (FR-01–37) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, API, auth, recipes, web routes |

## Quick start

### 1. Database + API

```bash
docker compose up -d
# API: http://localhost:3000  (runs startup.py migrate on boot)
```

Docker startup creates/migrates tables only. For a fresh database, seed the default meal plan and recipe catalog:

```bash
curl -X POST http://localhost:3000/v1/admin/seed \
  -H "X-Admin-Key: dev-admin-key"
```

**Option A — local venv (WSL):**

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python init_db.py          # first time: full seed
uvicorn app.main:app --reload --port 3000
```

**First-time or reset seed:** `python init_db.py`  
**Schema migrate only:** `python startup.py` or `python migrate_recipe_catalog.py`

### 2. Web client (React — not in Docker)

```bash
cd apps/web
npm install
npm run dev
```

App: http://localhost:5173 (proxies `/v1` and `/static` to API)

## Build and test

Backend tests:

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

Web build and tests:

```bash
cd apps/web
npm run build
npm test
```

Mobile has Expo start scripts but no test/build script in `package.json`:

```bash
cd apps/mobile
npm start
```

### 3. Using the app

| Role | What you get |
|------|----------------|
| **Guest** (no login) | Browse template meal plan (Today / Week / Day), recipe view links |
| **Logged in** | Personal meal edits, checkboxes, notes, import/export, Edit mode |
| **Recipe admin** | `/recipes` pages + `X-Admin-Key` (`dev-admin-key` locally) |

**Sign in:** top-right **Log in** / **Sign up**, or `/login`

## Web pages

| URL | Purpose |
|-----|---------|
| `/` | Meal planner |
| `/login` | Login & register |
| `/recipes` | Recipe list (admin) |
| `/recipes/new` | Create recipe |
| `/recipes/:id` | View recipe (ingredients, steps, photo) |
| `/recipes/:id/edit` | Edit recipe + upload image |

## Features (v2.6)

- **Today dashboard** — auto-select week containing today; progress when logged in
- **View / Edit modes** — View = checkboxes + read-only; Edit = editable meals + Recipes link
- **Rich recipes** — PostgreSQL storage; hybrid meal links (internal page or external URL)
- **Recipe combobox** — pick catalog recipe in Edit mode; shortcut to create new recipe
- **Guest mode** — anonymous users see template plan only; login unlocks personal data
- **Auth header** — Log in / Sign up top-right on all pages

See [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) for FR-01–37.

## Auth

**Default:** no JWT → guest (read-only template). Mutations return **401** until logged in.

```bash
# Register / login via UI at /login, or:
curl -X POST http://localhost:3000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpassword"}'
```

Send `Authorization: Bearer <access_token>` on authenticated requests (web stores tokens in `localStorage`).

**Optional dev flag** (legacy shared dev-user when no JWT):

```bash
# backend/.env or docker-compose api environment
ALLOW_ANONYMOUS_DEV_USER=true
```

## Recipe catalog

Recipes live in PostgreSQL (`recipe_catalog` table). Seed input: [`public/data/recipe-catalog.json`](public/data/recipe-catalog.json).

Meal items link by **normalized name** (case/spacing insensitive). Edit mode uses a **combobox** to pick recipes or create new ones.

```bash
# List
curl http://localhost:3000/v1/recipes

# Create (admin)
curl -X POST http://localhost:3000/v1/admin/recipes \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: dev-admin-key" \
  -d '{"name":"Mint Chutney","ingredients":[{"amount":"1 cup","item":"mint"}],"instructions":"Blend."}'
```

Images: upload on `/recipes/:id/edit` or `POST /v1/admin/recipes/{id}/image` → stored in `public/recipes/`.

### Recipe screenshot loader (external)

Bulk-import recipes from mobile app screenshots via the admin API. Separate ops tool — not required to run the app.

**Repo:** [dailydiet-recipe-loader](https://github.com/pingmepls/dailydiet-recipe-loader)

```bash
git clone https://github.com/pingmepls/dailydiet-recipe-loader.git
cd dailydiet-recipe-loader && pip install -e .
export ADMIN_KEY=dev-admin-key OPENAI_API_KEY=sk-...
recipe-loader-watch --extractor llm --poll
```

## Admin seed (after Excel change)

```bash
python scripts/import_xlsm.py
cd backend && python init_db.py
# or: curl -X POST http://localhost:3000/v1/admin/seed?run_import=true -H "X-Admin-Key: dev-admin-key"
```

## Project layout

```
backend/          FastAPI + SQLAlchemy (startup.py, init_db.py, migrate_recipe_catalog.py)
apps/web/         React + Vite + React Router (npm run dev)
apps/mobile/      Expo scaffold (Phase 3)
public/data/      Seed JSON (meal plan + recipe catalog)
public/recipes/   Uploaded recipe images
docs/             REQUIREMENTS.md, ARCHITECTURE.md
scripts/          Excel import
docker-compose.yml  postgres + api only
```

## Mobile

```bash
cd apps/mobile && npm install
EXPO_PUBLIC_API_URL=http://YOUR_IP:3000 npm start
```

See [apps/mobile/README.md](apps/mobile/README.md).
