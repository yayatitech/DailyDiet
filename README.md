# DailyDiet v2

Weekly meal tracker with **Python FastAPI** backend, **PostgreSQL**, **React** web client, and **Expo** mobile scaffold.

| Doc | Purpose |
|-----|---------|
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | Functional & non-functional requirements |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, API, database |

## Quick start

### 1. Database

```bash
docker compose up -d
```

### 2. Backend (Python)

**Option A — local venv (recommended on WSL):**

```bash
sudo apt install python3.12-venv python3-pip   # once
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python init_db.py
uvicorn app.main:app --reload --port 3000
```

**Option B — Docker (API + Postgres):**

```bash
docker compose up -d
# API at http://localhost:3000 after build completes
```

API: http://localhost:3000/docs

### 3. Web client (React)

```bash
cd apps/web
npm install
npm run dev
```

App: http://localhost:5173 (proxies API)

### Admin seed (after Excel change)

```bash
python scripts/import_xlsm.py
cd backend && python init_db.py
# or: curl -X POST http://localhost:3000/v1/admin/seed?run_import=true -H "X-Admin-Key: dev-admin-key"
```

## Project layout

```
backend/          FastAPI + SQLAlchemy
apps/web/         React web client
apps/mobile/      Expo scaffold (Phase 3)
public/data/      Seed JSON for DB import
docs/             Requirements & architecture
scripts/          Excel import (Python stdlib)
```

## Auth

- **Dev mode:** no token → default dev user (`dev@dailydiet.local`)
- **Production:** register/login via `/v1/auth/*`, send `Authorization: Bearer <token>`

## Mobile

```bash
cd apps/mobile && npm install
EXPO_PUBLIC_API_URL=http://YOUR_IP:3000 npm start
```

See [apps/mobile/README.md](apps/mobile/README.md).
