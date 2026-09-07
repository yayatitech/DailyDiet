# DailyDiet v2 — Requirements Specification

**Version:** 2.6  
**Stack:** Python (FastAPI, SQLAlchemy, PostgreSQL) + React web + Expo mobile (Phase 3)  
**Status:** Active

---

## 1. Introduction

### 1.1 Purpose

DailyDiet helps users follow a structured **weekly meal plan** with **8 meals per day** at fixed times. Version 2 adds a **client–server architecture** with permanent database storage, multi-user support, and web/mobile clients sharing one REST API.

### 1.2 Scope

| In scope (v2) | Out of scope (v2.0) |
|---------------|---------------------|
| Weekly/day/today meal views | Calorie/macro tracking |
| Server-persisted edits & completions (logged in) | Social sharing |
| Guest read-only template browse + login/register | In-browser Excel parsing |
| Multi-user JWT auth | Automated test suite (initial) |
| Rich recipes (pages, images, hybrid links) | |
| Excel → DB admin import | |
| Web + mobile API clients | |

### 1.3 Stakeholders

- **End user** — follows daily meal plan, checks off meals
- **Admin** — imports/updates template from Excel
- **Developer** — maintains Python API and clients

### 1.4 Glossary

| Term | Definition |
|------|------------|
| **Time slot** | One of 8 daily meal times (e.g. Meal 1 @ 6:30 AM) |
| **Template week** | Canonical week block from Excel/seed (26+ weeks) |
| **User override** | User-specific meal text or notes differing from template |
| **Completion** | Checkbox state: user marked a meal as done |
| **Week key** | Stable id e.g. `week-1` matching import order |
| **Meal item** | One named food within a time slot (e.g. "Mint Chutney") |
| **Recipe catalog** | Global map of meal name → recipe (ingredients, instructions, image, optional external URL) |
| **Guest** | Anonymous visitor; sees template plan read-only until login |

---

## 2. Functional requirements

### 2.1 Core (Phase 1)

| ID | Requirement | Priority |
|----|-------------|----------|
| **FR-01** | Display weekly meal grid: 7 days × 8 time slots | Must |
| **FR-02** | Display day view for mobile/narrow screens | Must |
| **FR-03** | Edit meal text; persist to server | Must |
| **FR-04** | Edit week notes; persist to server | Must |
| **FR-05** | Mark meal complete/incomplete; cell background turns red | Must |
| **FR-06** | Highlight current day column when week has start date | Should |
| **FR-07** | Select among 26+ template weeks | Must |
| **FR-08** | Reset week meals/notes to template defaults | Must |
| **FR-09** | Reset all completion checkboxes for user | Must |
| **FR-10** | Export user plan + completions as JSON backup | Should |
| **FR-11** | Import JSON backup (v1 migration) | Should |
| **FR-12** | Seed templates from Excel via admin CLI/API | Must |

### 2.2 Multi-user (Phase 2)

| ID | Requirement | Priority |
|----|-------------|----------|
| **FR-13** | User registration with email + password | Must |
| **FR-14** | User login; JWT access + refresh tokens | Must |
| **FR-15** | Each user sees only their overrides and completions | Must |
| **FR-16** | Authenticated `/v1/me` profile endpoint | Should |

### 2.3 Mobile (Phase 3)

| ID | Requirement | Priority |
|----|-------------|----------|
| **FR-17** | Native mobile app (Expo) lists weeks and day meals | Must |
| **FR-18** | Mobile syncs completions and edits via same API | Must |

### 2.4 Meal items & recipes

| ID | Requirement | Priority |
|----|-------------|----------|
| **FR-19** | Split slot text into distinct **meal items** (newline-delimited); display each on its own row in week grid and day view | Must |
| **FR-20** | Show a **recipe link icon** when catalog matches; **hybrid link** — internal `/recipes/:id` when content exists, else external URL in new tab | Must |
| **FR-21** | Maintain a **global recipe catalog** (meal name → URL); lookup is case-insensitive, whitespace-normalized | Must |
| **FR-22** | Admin can **CRUD catalog entries** via API; seed from JSON on deploy/import | Must |
| **FR-23** | Slot **completion checkbox** remains at slot level (all items in cell share done state) | Must |
| **FR-24** | User can still **edit slot content**; edits persist as newline-joined text (backward compatible with existing overrides) | Must |

### 2.5 View vs Edit mode

| ID | Requirement | Priority |
|----|-------------|----------|
| **FR-25** | **View mode** (default, logged in): read-only meal items, recipe links, slot checkboxes, read-only notes. Guests see template plan without checkboxes or mode toggle | Must |
| **FR-26** | **Edit mode** (logged in only): editable meals/notes via recipe combobox; no checkboxes; reset/import actions visible | Must |

### 2.6 Today dashboard & recipe admin

| ID | Requirement | Priority |
|----|-------------|----------|
| **FR-27** | On load, auto-select the template week whose date range includes today; default layout is **Today** | Must |
| **FR-28** | **Today** layout shows today's 8 slots and completion progress; checkboxes when logged in (View mode) | Must |
| **FR-29** | **Edit mode** nav link to **Recipes** admin pages (`/recipes`); list, add, edit, delete via admin API | Must |

### 2.7 Rich recipes & dedicated pages

| ID | Requirement | Priority |
|----|-------------|----------|
| **FR-30** | Store full recipe content in PostgreSQL (`name`, `display_name`, `ingredients`, `instructions`, `image`, optional `external_url`) | Must |
| **FR-31** | **Recipe view page** shows photo, ingredients, and instructions at `/recipes/:id` | Must |
| **FR-32** | **Recipe edit/create pages** at `/recipes/new` and `/recipes/:id/edit` (admin API key) | Must |
| **FR-33** | **Hybrid meal link**: internal recipe page when content exists; else external URL in new tab | Must |
| **FR-34** | Admin can **upload recipe images** to server storage (`public/recipes/`) | Must |
| **FR-34a** | Preserve uploaded recipe image filenames (`basename` + content-type extension); fall back to `{id}{ext}` only when the name is missing/invalid; prevent path traversal and filename collisions between catalog entries | Must |
| **FR-35** | **Edit mode** meal items use an editable recipe combobox; unmatched text offers **Create recipe** shortcut to `/recipes/new?name=…` | Must |

### 2.8 Authentication & guest mode

| ID | Requirement | Priority |
|----|-------------|----------|
| **FR-36** | Login/register on dedicated `/login` page; header shows Log in / Sign up or user email + Log out | Must |
| **FR-37** | **Guest** users browse template meal plan read-only (no edits, tracking, import/export); **authenticated** users get personal overrides and tracking | Must |

---

## 3. Non-functional requirements

| ID | Category | Requirement | Target |
|----|----------|-------------|--------|
| **NFR-01** | Performance | Week grid loads on 4G | < 2 s |
| **NFR-02** | Performance | Meal save feels instant | < 500 ms (optimistic UI) |
| **NFR-03** | Availability | Production API uptime | 99.5% |
| **NFR-04** | Security | Production traffic | HTTPS only |
| **NFR-05** | Security | Password storage | bcrypt hash |
| **NFR-06** | Security | API auth | JWT expiry + refresh |
| **NFR-07** | Scalability | Users without schema change | 1,000 |
| **NFR-08** | Maintainability | API documentation | OpenAPI (FastAPI auto) |
| **NFR-09** | Portability | Web browsers | Chrome, Safari, Firefox (last 2) |
| **NFR-10** | Mobile web | Responsive layout | ≥ 320 px width |
| **NFR-11** | Data integrity | Meal/completion updates | ACID (PostgreSQL) |
| **NFR-12** | Backup | Hosted DB | Daily backups |
| **NFR-13** | Observability | Health + structured logs | `/health` endpoint |
| **NFR-14** | Cost | Local dev | Docker Postgres |
| **NFR-15** | Accessibility | Grid keyboard + checkbox labels | WCAG 2.1 AA (goal) |
| **NFR-16** | i18n | UI language v2.0 | English only |
| **NFR-17** | Accessibility | Recipe links | Open with `rel="noopener noreferrer"`; icon has `aria-label="Recipe for …"` |

---

## 4. Constraints and assumptions

- PostgreSQL is the runtime source of truth; Excel is admin input only.
- Python 3.11+ for backend; Node.js for web/mobile clients only.
- Solo developer: prefer simple deployment (Docker Compose locally).

---

## 5. Traceability matrix

| FR | API endpoint(s) | UI (web) | Phase |
|----|-----------------|----------|-------|
| FR-01 | `GET /v1/weeks/:id` | WeekGrid | 1 |
| FR-02 | same | DayView | 1 |
| FR-03 | `PATCH /v1/weeks/:id/meals` | MealCell textarea | 1 |
| FR-04 | `PATCH /v1/weeks/:id/notes` | Notes textarea | 1 |
| FR-05 | `PUT /v1/weeks/:id/completions` | Checkbox | 1 |
| FR-06 | client-side date logic | `.col-today` CSS | 1 |
| FR-07 | `GET /v1/weeks` | Week select | 1 |
| FR-08 | `POST /v1/weeks/:id/reset` | Reset week button | 1 |
| FR-09 | `DELETE /v1/completions` | Reset tracking | 1 |
| FR-10 | `GET /v1/export` | Export JSON | 1 |
| FR-11 | `POST /v1/import` | Import JSON | 1 |
| FR-12 | `POST /v1/admin/seed` | — | 1 |
| FR-13–16 | `/v1/auth/*`, `/v1/me` | `/login`, token storage | 2 |
| FR-17–18 | all `/v1/*` | Expo app | 3 |
| FR-19–20 | `GET /v1/weeks/:id` (enriched items) | `MealSlotViewer` / `MealSlotEditor` | 1 |
| FR-21–22 | `GET /v1/recipes`, `/v1/admin/recipes` | admin via API/docs | 1 |
| FR-23 | existing completions API | Checkbox in View mode | 1 |
| FR-24 | `PATCH /v1/weeks/:id/meals` | per-item inputs in Edit mode | 1 |
| FR-25 | `GET /v1/weeks/:id`, completions API | View mode: read-only meals, checkboxes (logged in) | 1 |
| FR-26 | `PATCH` meals/notes, reset/import | Edit mode (logged in): editable meals/notes | 1 |
| FR-27–28 | `GET /v1/weeks`, completions | Today layout; progress when logged in | 1 |
| FR-29 | `/v1/recipes`, `/v1/admin/recipes` | Recipe list page (`/recipes`) in Edit mode nav | 1 |
| FR-30–34a | `/v1/recipes/:id`, `/v1/admin/recipes`, image upload | Recipe view/edit pages, hybrid meal links; stored names preserved | 1 |
| FR-35 | `GET /v1/recipes` | `RecipeCombobox` in Edit mode meal rows | 1 |
| FR-36–37 | `/v1/auth/*`, `/v1/me`, optional user on GET weeks | `/login`, guest read-only, header auth | 2 |

---

## 6. Revision history

| Date | Version | Change |
|------|---------|--------|
| 2026-05-30 | 2.0 | Initial v2 requirements; Python stack |
| 2026-05-30 | 2.1 | Meal items per slot + recipe catalog (FR-19–24) |
| 2026-05-30 | 2.2 | View vs Edit interaction modes (FR-25–26) |
| 2026-05-31 | 2.3 | Today dashboard + recipe catalog admin UI (FR-27–29) |
| 2026-05-31 | 2.4 | Rich recipes, dedicated pages, hybrid links, image upload (FR-30–34) |
| 2026-05-31 | 2.5 | Recipe combobox in Edit mode meal slots (FR-35) |
| 2026-05-31 | 2.6 | Auth page, guest read-only mode (FR-36–37) |
| 2026-08-30 | 2.6 | Preserve recipe image filenames on upload (FR-34a) |
