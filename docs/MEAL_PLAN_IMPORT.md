# Meal plan import — Excel → JSON → local → droplet

How to load a **new weekly meal plan** into DailyDiet.

```text
Excel (.xlsm / .xlsx)
  → scripts/import_xlsm.py
  → public/data/meal-plan.json
  → POST /v1/admin/seed  (or init_db.py)
  → PostgreSQL
  → App UI
```

**Important:** Creating or editing `meal-plan.json` alone does **not** update the app. The API reads from **Postgres**. Seed (or `init_db.py`) is the step that loads JSON into the database.

---

## Prerequisites

- Docker Compose API + Postgres running locally (`docker compose up -d`), or a local venv API
- Workbook uses the usual Fitelo layout: week headers like `Week N starting: …`, then 8 meal rows × Mon–Sun (cols B–H)
- Local admin key default: `dev-admin-key` (from `ADMIN_API_KEY`)

---

## Part 1 — Local: Excel → JSON → database

### 1. Put the workbook in the repo

Copy your file to the repo root as:

```text
simple_weekly_meal_plan_extendable.xlsm
```

(The import script currently looks for that path. `.xlsx` is the same OOXML format — save/copy as `.xlsm` or rename if needed.)

### 2. Convert Excel → `meal-plan.json`

```bash
cd ~/projects/DailyDiet   # or your clone path
python3 scripts/import_xlsm.py
```

Expected: `Wrote N weeks to …/public/data/meal-plan.json`

### 3. Copy JSON into the API container (Docker)

The API container may have an older baked-in copy of `public/data/`. After updating the host file:

```bash
docker cp public/data/meal-plan.json dailydiet-api:/app/public/data/meal-plan.json
```

Skip this if you run the API from a local venv that reads the host `public/data/` path.

### 4. Seed Postgres from JSON

**If JSON is already updated** (recommended after step 2):

```bash
curl -X POST "http://localhost:3000/v1/admin/seed" \
  -H "X-Admin-Key: dev-admin-key"
```

Expected:

```json
{"ok":true,"message":"Database seeded from meal-plan.json and recipe-catalog.json"}
```

**Do not use `?run_import=true`** unless you want the server to re-run `import_xlsm.py` itself. You already have `meal-plan.json`.

| Situation | Endpoint |
|-----------|----------|
| JSON already updated | `POST /v1/admin/seed` |
| Excel → JSON + seed in one call | `POST /v1/admin/seed?run_import=true` |

**CLI alternative** (same full seed):

```bash
docker exec dailydiet-api python init_db.py
# or, with local venv:
cd backend && python init_db.py
```

### 5. Verify locally

```bash
curl -s http://localhost:3000/health
curl -s http://localhost:3000/v1/weeks | head
```

Open http://localhost:5173 and check the week dropdown / meal grid.

---

## What seed does (destructive)

`POST /v1/admin/seed` / `run_full_seed` / `init_db.py`:

- Reloads **meal plan** from `public/data/meal-plan.json`
- Reloads **recipe catalog** from `public/data/recipe-catalog.json`
- **Deletes** template weeks/meals, time slots, user meal overrides, week notes, and completions

User accounts remain. Export personal data first if you need it (`GET /v1/export` while logged in).

Code: [`backend/seed.py`](../backend/seed.py), trigger: [`backend/app/routers/admin.py`](../backend/app/routers/admin.py).

---

## Part 2 — Move the new plan to the droplet

Canonical app path: `/opt/apps/DailyDiet`. See also [DEPLOYMENT.md §12](DEPLOYMENT.md) for table dumps and SSH details.

### Preferred: copy JSON + seed on droplet

**On your laptop** (after local import produced the JSON you want):

```bash
export DROPLET=root@YOUR_DROPLET_IP
export SSH_KEY=~/.ssh/id_digital_ocean   # key registered on the droplet

scp -i "$SSH_KEY" public/data/meal-plan.json \
  "$DROPLET:/opt/apps/DailyDiet/public/data/meal-plan.json"
```

**On the droplet** (SSH in, or remote one-liners):

```bash
# Ensure container sees the new file
docker cp /opt/apps/DailyDiet/public/data/meal-plan.json \
  dailydiet-api:/app/public/data/meal-plan.json

# Use the real ADMIN_API_KEY from .env.prod — not dev-admin-key
curl -X POST "http://127.0.0.1:3000/v1/admin/seed" \
  -H "X-Admin-Key: YOUR_PROD_ADMIN_API_KEY"
```

**Warning:** This wipes **cloud** personal overrides / notes / completions the same way as local seed. User accounts stay.

### Alternate: dump template tables from local DB

If local Postgres is already correct and you prefer SQL over JSON seed, use [DEPLOYMENT.md §12.2–12.4](DEPLOYMENT.md) (`pg_dump` of `time_slots`, `plan_templates`, `template_weeks`, `template_meals`, optional `recipe_catalog`).

Do **not** run `/v1/admin/seed` after a SQL restore if that would overwrite what you just imported.

---

## Quick reference

### Local (JSON already built)

```bash
python3 scripts/import_xlsm.py
docker cp public/data/meal-plan.json dailydiet-api:/app/public/data/meal-plan.json
curl -X POST "http://localhost:3000/v1/admin/seed" \
  -H "X-Admin-Key: dev-admin-key"
```

### Local (Excel + seed in one API call)

```bash
curl -X POST "http://localhost:3000/v1/admin/seed?run_import=true" \
  -H "X-Admin-Key: dev-admin-key"
```

(Requires the xlsm file and import script available where the API process runs.)

### Droplet

```bash
scp -i "$SSH_KEY" public/data/meal-plan.json \
  "$DROPLET:/opt/apps/DailyDiet/public/data/meal-plan.json"
ssh -i "$SSH_KEY" "$DROPLET" \
  'docker cp /opt/apps/DailyDiet/public/data/meal-plan.json dailydiet-api:/app/public/data/meal-plan.json'
ssh -i "$SSH_KEY" "$DROPLET" \
  'curl -sS -X POST http://127.0.0.1:3000/v1/admin/seed -H "X-Admin-Key: YOUR_PROD_ADMIN_API_KEY"'
```

---

## Related docs

| Doc | Content |
|-----|---------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, seed in the pipeline diagram |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Droplet deploy + §12 data migration |
| [work_in_progress.md](work_in_progress.md) | Session log |
| [README.md](../README.md) | Quick start |
