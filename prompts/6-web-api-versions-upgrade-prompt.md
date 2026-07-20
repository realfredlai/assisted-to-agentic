# Prompt: Create an implementation plan for a full stack versions upgrade

## Request

You are asked to create a **comprehensive implementation plan** to upgrade the existing `config-service` full stack application to the target versions listed below. Do NOT make any code changes yet — produce a plan only.

The plan must include:

1. **Compatibility validation** — for every upgrade, cite the official release notes or documentation to confirm that the target version is compatible with the rest of the stack. If any incompatibility is found, stop and report it before proposing workarounds.
2. **Upgrade order** — the specific sequence in which dependencies should be upgraded, with justification for the ordering (e.g., "upgrade Django before DRF because DRF depends on Django").
3. **Per-dependency changes** — for each dependency being upgraded, list the exact version change (from → to), any breaking changes or deprecations that affect this project, and the specific files that need modification.
4. **Verification strategy** — after each upgrade step, how to verify that nothing is broken (run the existing 7 Django/DRF tests, manual curl checks against the API, frontend build verification).

## Current state of the application

### Backend (Python / pip)

| Package | Current Version |
|---------|----------------|
| Python | 3.14.4 |
| Django | 5.1.9 |
| djangorestframework | 3.15.2 |
| psycopg2-binary | 2.9.10 |
| django-cors-headers | 4.7.0 |

### Frontend (Node.js / npm)

| Package | Current Version |
|---------|----------------|
| Node.js | 24.x |
| Vue.js | 3.5.x |
| vue-router | 4.5.x |
| axios | 1.x |
| Vite | 6.x |
| @vitejs/plugin-vue | 5.x |

### Infrastructure

| Component | Current Version |
|-----------|----------------|
| PostgreSQL | 16 (Docker) |

### Application overview

- Django REST Framework backend exposing a `User` model via REST API at `/api/users/`
- Vue.js SPA frontend that fetches and displays the user list using axios
- `django-cors-headers` handles cross-origin requests between frontend (port 5173) and backend (port 8000)
- 7 passing tests (2 model tests + 5 API endpoint tests) using Django's default test framework
- All code lives under `./config-service/` with `backend/` and `frontend/` subdirectories

## Target versions

| Component | Target Version |
|-----------|---------------|
| Django | 5.2 |
| Django REST Framework (DRF) | 3.17 |
| Vue.js | 3.5 |
| Python | 3.14 |

## Compatibility validation requirements

The plan MUST explicitly validate, citing official release notes or documentation:

1. **Django 5.2 ↔ Python 3.14** — confirm Python 3.14 is in Django 5.2's supported Python versions matrix.
2. **Django 5.2 ↔ DRF 3.17** — confirm DRF 3.17 officially supports Django 5.2.
3. **Django 5.2 ↔ PostgreSQL 16** — confirm PostgreSQL 16 is supported by Django 5.2.
4. **Django 5.2 ↔ psycopg2-binary** — confirm the current psycopg2-binary version (or a newer one) is compatible with Django 5.2; note whether Django 5.2 requires or recommends psycopg3 instead.
5. **Django 5.2 ↔ django-cors-headers** — confirm the current django-cors-headers version (or a newer one) supports Django 5.2.
6. **Vue.js 3.5 ↔ Vite / vue-router / axios** — confirm the frontend is already on the target version (Vue.js 3.5) and that existing Vite, vue-router, and axios versions remain compatible, or specify exact version bumps needed.

## Rules — strict adherence required

- You MUST strictly adhere to ALL target versions listed above. Do not substitute alternatives.
- You MUST validate every compatibility claim with a citation to official documentation or release notes. No unsupported assertions.
- If any information you need is missing, unclear, or ambiguous, ASK for more information before proceeding.
- NO guesswork. Every decision in the plan must be traceable to the specifications above, official documentation, or an answer you have explicitly received.
- Do NOT add any additional dependencies, frameworks, libraries, or tools beyond what is required for the version upgrades without asking for approval first.