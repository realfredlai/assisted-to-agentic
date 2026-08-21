# About

## description

This document is used as semantic memory for agents to understand the project at load time. The project is `config-service`: a full stack application that exposes User, Application, and Configuration models via a Django REST Framework API and a Vue.js Single Page Application, backed by PostgreSQL running in Docker.

- Application code: `config-service/` (backend + frontend)
- Workflow artifacts: `prompts/` (specs → prompt → plan → implementation → upgrade), `JOURNAL.md` (run log)
- Git repository root: `module1/` (branch `main`)
- Semantic-memory companions: [DOMAIN.md](DOMAIN.md) (business domain), [ARCHITECTURE.md](ARCHITECTURE.md) (system design), [IMPLEMENTATION.md](IMPLEMENTATION.md) (languages, versions, dependencies, preferences)
- Procedural memory: [memory/ENV_SCRIPTS.md](../memory/ENV_SCRIPTS.md) (environments, environment variables, developer scripts, and when to go off-script)
- Episodic memory: [memory/WORKFLOW_STATUS.md](../memory/WORKFLOW_STATUS.md) (the four-stage framework, work-item structure, purge discipline, and where we are; update every run), per-task work items in [changes/](../changes/), and [JOURNAL.md](../JOURNAL.md) as the append-only log

## justification

`config-service` is the hands-on exercise for Module 1 of the learn-ai-engineering curriculum: practicing an AI-assisted engineering workflow end to end. The application started deliberately minimal — a single User model displayed as a list — so the focus stayed on the workflow rather than business complexity, then grew through repeated cycles of the same workflow:

1. Write specs (`prompts/1-web-api-specs.md`)
2. Generate a planning prompt (`prompts/2-web-api-prompt.md`) and a plan (`prompts/3-web-api-plan.md`)
3. Answer the plan's open questions (`prompts/4-web-api-plan-answers.md`)
4. Produce a detailed implementation plan (`prompts/4-web-api-implementation.md`) and execute it task-by-task with AI agents
5. Repeat the cycle for maintenance work: a dependency versions upgrade (`prompts/5` → `7`)
6. Repeat the cycle again for a feature expansion: the config-storage spec (`prompts/8-web-api-config-storage-specs.md`), brainstormed → planned → executed subagent-driven on branch `feature/config-storage`

Every run is logged in `JOURNAL.md` (prompt, tool, model, mode, context, input/output files).

## personas

- **Learner / repo owner** — drives the workflow, reviews and approves plans, answers open questions, records journal entries.
- **AI coding agents** (Cline, Claude Code) — read this document at load time as semantic memory, then plan and execute implementation work task-by-task (subagent-driven execution with per-task review).
- **App end user** — anonymous visitor who opens the SPA and views the user list. No authentication (public MVP).
- **App admin** — manages User records through Django admin (`/admin/`).

## domain context

The application domain started as a minimal user directory — a single custom `User` model (not `django.contrib.auth`'s user) exposed over full CRUD REST at `/api/users/` and rendered as a list by the SPA — and has grown into an application configuration store: an `Application` registry (users↔application many-to-many) with nested `Configuration` resources holding per-environment JSON settings, both with full CRUD REST and SPA screens. The detail lives in the companion docs — single source of truth, kept out of this file to avoid drift:

- [DOMAIN.md](DOMAIN.md) — entity semantics, actors, use cases, MVP boundaries
- [ARCHITECTURE.md](ARCHITECTURE.md) — 3-tier design, request flow, stack versions, configuration, testing, dev workflow

## scope

**In scope (implemented):**

- User model, serializer, viewset, and router; full CRUD REST API under `/api/` — merged to `main`
- Vue SPA with Vue Router displaying the user list — merged to `main`
- PostgreSQL via Docker Compose; schema managed entirely by Django ORM migrations
- Django admin registration for the User, Application, and Configuration models
- Dependency versions upgrade to the Django 5.2 LTS line (see `prompts/7-web-api-versions-upgrade-plan.md`) — merged to `main`
- Application registry: `name`/`app_type` (4 types: mobile, desktop, web, cloud)/`users` M2M, full CRUD REST API under `/api/applications/` — merged to `main`
- Configuration resource nested under applications (three environments — `dev_settings`/`uat_settings`/`prod_settings`, each a JSON object): full CRUD REST API under `/api/applications/{app_id}/configurations/`, hand-rolled nesting — merged to `main`
- Full CRUD SPA for applications and configurations (list/detail/create/edit, JSON-textarea validation); users remain display-only in the SPA — merged to `main`
- Test suite (34 tests: 7 original User tests + 27 new Application/Configuration tests) using Django's default test framework

**Out of scope (explicit MVP decisions):**

- Authentication/authorization — the API is public
- Frontend state management (Pinia/Vuex), TypeScript, and frontend test tooling
- Production deployment (gunicorn/uvicorn, reverse proxy, containerizing the apps) — only Postgres runs in Docker
- `drf-nested-routers` or any other new dependency for the nested configuration routes
- Pagination/search, per-environment settings schema, user CRUD via the SPA

**Status:** initial implementation plan (`prompts/4-web-api-implementation.md`) fully executed (commit `8cd130e`); versions-upgrade plan fully executed and merged (`bf9935b..4ff19f4`); config-storage expansion (spec `prompts/8-web-api-config-storage-specs.md`) fully executed and merged (`48c4eee..47662c6`); 34/34 backend tests green as of 2026-07-28.
