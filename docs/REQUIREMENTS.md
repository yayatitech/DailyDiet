# DailyDiet v2 — Requirements Specification

**Version:** 2.0  
**Stack:** Python (FastAPI, SQLAlchemy, PostgreSQL) + React web + Expo mobile (Phase 3)  
**Status:** Active

---

## 1. Introduction

### 1.1 Purpose

DailyDiet helps users follow a structured **weekly meal plan** with **8 meals per day** at fixed times. Version 2 adds a **client–server architecture** with permanent database storage, multi-user support, and web/mobile clients sharing one REST API.

### 1.2 Scope

| In scope (v2) | Out of scope (v2.0) |
|---------------|---------------------|
| Weekly/day meal views | Calorie/macro tracking |
| Server-persisted edits & completions | Social sharing |
| Multi-user auth (Phase 2) | In-browser Excel parsing |
| Excel → DB admin import | Automated test suite (initial) |
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
| **Recipe catalog** | Global map of meal name → recipe URL, shared across all weeks/users |

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
| **FR-20** | Show a **recipe link icon** next to a meal item when the catalog has a URL for that name; icon opens URL in new tab | Must |
| **FR-21** | Maintain a **global recipe catalog** (meal name → URL); lookup is case-insensitive, whitespace-normalized | Must |
| **FR-22** | Admin can **CRUD catalog entries** via API; seed from JSON on deploy/import | Must |
| **FR-23** | Slot **completion checkbox** remains at slot level (all items in cell share done state) | Must |
| **FR-24** | User can still **edit slot content**; edits persist as newline-joined text (backward compatible with existing overrides) | Must |

### 2.5 View vs Edit mode

| ID | Requirement | Priority |
|----|-------------|----------|
| **FR-25** | **View mode** (default): read-only meal items, recipe links, slot checkboxes, read-only notes | Must |
| **FR-26** | **Edit mode**: editable meals/notes; no checkboxes; reset/import actions visible | Must |

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
| FR-13–16 | `/v1/auth/*`, `/v1/me` | Login/register | 2 |
| FR-17–18 | all `/v1/*` | Expo app | 3 |
| FR-19–20 | `GET /v1/weeks/:id` (enriched items) | `MealSlotViewer` / `MealSlotEditor` | 1 |
| FR-21–22 | `GET /v1/recipes`, `/v1/admin/recipes` | admin via API/docs | 1 |
| FR-23 | existing completions API | Checkbox in View mode | 1 |
| FR-24 | `PATCH /v1/weeks/:id/meals` | per-item inputs in Edit mode | 1 |
| FR-25 | `GET /v1/weeks/:id`, completions API | View mode: read-only meals, checkboxes | 1 |
| FR-26 | `PATCH` meals/notes, reset/import | Edit mode: editable meals/notes | 1 |

---

## 6. Revision history

| Date | Version | Change |
|------|---------|--------|
| 2026-05-30 | 2.0 | Initial v2 requirements; Python stack |
| 2026-05-30 | 2.1 | Meal items per slot + recipe catalog (FR-19–24) |
| 2026-05-30 | 2.2 | View vs Edit interaction modes (FR-25–26) |
