# Implementation

This document is semantic memory for agents: it records the **languages, versions, dependencies, and implementation preferences** of `config-service` — the concrete toolchain an agent must respect when writing or upgrading code. For system design see [ARCHITECTURE.md](ARCHITECTURE.md); for the business domain see [DOMAIN.md](DOMAIN.md); for purpose and scope see [ABOUT.md](ABOUT.md).

## Languages & runtimes

| Language / runtime | Version | Notes |
|--------------------|---------|-------|
| Python | 3.14.4 | Virtual environment at `config-service/backend/venv/` (from Homebrew `python3`) |
| JavaScript (ES modules) | ES2020+ | `"type": "module"` in `package.json`; plain JS — **no TypeScript** (MVP exclusion) |
| Node.js | 24.x installed | README floor is 22+ |
| SQL | — | Never written by hand; schema is owned by Django ORM migrations |

## Backend dependencies

`config-service/backend/requirements.txt` — **exact pins** (`==`); upgrades happen only through a deliberate spec → prompt → plan cycle, never ad hoc:

| Package | Version | Role |
|---------|---------|------|
| `Django` | 5.2.16 | Web framework — 5.2 **LTS** line |
| `djangorestframework` | 3.17.1 | REST API framework |
| `psycopg2-binary` | 2.9.12 | PostgreSQL adapter (2.9.12+ for official Python 3.14 support) |
| `django-cors-headers` | 4.9.0 | CORS (4.9.0+ for official Python 3.14 support) |

Install: `python3 -m venv backend/venv && source backend/venv/bin/activate && pip install -r backend/requirements.txt`.

## Frontend dependencies

`config-service/frontend/package.json` — **caret ranges** (`^`), resolved by the committed `package-lock.json`:

| Package | Range | Role |
|---------|-------|------|
| `vue` | ^3.5.13 | SPA framework (Options API style) |
| `vue-router` | ^4.5.0 | Client-side routing |
| `axios` | ^1.9.0 | HTTP client (preferred over native `fetch`) |
| `vite` | ^6.2.0 | Build tool / dev server (dev dependency) |
| `@vitejs/plugin-vue` | ^5.2.0 | Vue SFC support for Vite (dev dependency) |

Install: `cd config-service/frontend && npm install`.

## Infrastructure

- **PostgreSQL 16** via `config-service/docker-compose.yml` (image `postgres:16`, service `db`, port 5432, named volume `pgdata`).
- Database `config_service_db`, user/password `postgres`/`postgres` — hardcoded in `config/settings.py` and `docker-compose.yml` (accepted MVP decision, no env-var indirection, no dotenv).
- Only the database is containerized; Django (`manage.py runserver`, :8000) and Vite (`npm run dev`, :5173) run natively on the host.

## Tooling & quality

- **Tests:** Django's default test framework only (`django.test.TestCase`, DRF `APITestCase`) — no pytest. Run with `python manage.py test` (requires the Postgres container up). 34 tests as of 2026-07-28.
- **Migrations:** `python manage.py makemigrations api` → `python manage.py migrate`; migration files are committed.
- **No linters or formatters are configured** (no ruff/flake8/black, no ESLint/Prettier) — match the existing code style by reading neighboring files.
- **Frontend scripts:** `npm run dev` (dev server), `npm run build` (production build to `dist/`), `npm run preview`.

## Dependency & style preferences

Recorded in `prompts/4-web-api-plan-answers.md` and the implementation plan — these are standing decisions, not defaults to re-litigate:

1. **Minimal-dependency policy** — only the approved list above. Explicitly rejected: Pinia/Vuex, TypeScript, pytest, dotenv, gunicorn/uvicorn, frontend test tooling.
2. **`axios` over native `fetch`** — always wrapped in `src/services/api.js`; components never touch HTTP directly.
3. **`django-cors-headers` over a Vite dev proxy** — the SPA calls the backend's real origin.
4. **Django idioms:** thin Model → Serializer → ViewSet → Router layering; `ModelViewSet` + `DefaultRouter`, no hand-rolled views or custom actions unless the domain demands it.
5. **Vue idioms:** Options API single-file components; route-level views own data fetching and state, presentational components receive props.

## Version upgrade policy

- Backend pins are upgraded as their own workflow cycle (specs → prompt → plan → execution), e.g. `prompts/5-web-api-versions-upgrade-specs.md` → `prompts/7-web-api-versions-upgrade-plan.md`, merged as `bf9935b..4ff19f4` (Django 5.1.9 → 5.2.16).
- Prefer Django **LTS** releases; prefer dependency versions with official support for the current Python runtime.
- After any upgrade: run the test suite (all green) and record the run in `JOURNAL.md`.
