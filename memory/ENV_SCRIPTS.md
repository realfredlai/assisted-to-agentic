# Environment & Scripts

**Procedural memory** — how things work: the commands to run tests, apply migrations, and start services. Without this an assistant guesses at commands, runs the wrong ones, or asks every time.

Companion: [WORKFLOW_STATUS.md](WORKFLOW_STATUS.md) (episodic — the stage framework and what has happened). System design: [context/ARCHITECTURE.md](../context/ARCHITECTURE.md). The executable source of truth for every command below is [`config-service/Makefile`](../config-service/Makefile) — run `make` targets by default.

## 1. Environments

| Environment | Exists? | What it is |
|-------------|---------|------------|
| **Local development** | Yes — the only one | Everything on the host except PostgreSQL, which runs in Docker. Backend in `backend/venv`, frontend via the Vite dev server. |
| **Test** | Yes, ephemeral | `make test` creates and destroys a throwaway `test_config_service_db` on the same Postgres instance. Development data is never touched. |
| **CI** | **No** | There is no `.github/workflows`, no pipeline config, nothing automated. Tests run only when someone runs them locally. Do not reference a CI run as evidence — there isn't one. |
| **Staging / production** | **No** | Out of scope for the MVP. No gunicorn/uvicorn, no reverse proxy, no container for the app tiers; only PostgreSQL is containerized. |

### Ports

| Port | Service | Notes |
|------|---------|-------|
| 5432 | PostgreSQL 16 in Docker (`config-service-db-1`) | Published to the host; volume `pgdata` persists data across restarts |
| 8000 | Django + DRF dev server | API at `/api/`, admin at `/admin/` |
| 5173 | Vite dev server (Vue SPA) | Must stay on this port — it is the only origin in `CORS_ALLOWED_ORIGINS` |

The 5173 constraint matters: start the SPA on a different port and every API call fails CORS. If 5173 is taken, free it rather than letting Vite pick 5174.

## 2. Environment variables

**There is no `.env` file, and no env-var indirection anywhere.** Configuration is hardcoded, which was a deliberate MVP decision (no `python-dotenv`/`django-environ` dependency). `.env` is nonetheless listed in `config-service/.gitignore`, so one can be introduced later without leaking.

The values that *would* be environment variables live in these two files:

**`config-service/docker-compose.yml`** — consumed by the Postgres container at first startup:

| Variable | Value | Controls |
|----------|-------|----------|
| `POSTGRES_DB` | `config_service_db` | Database created on first run |
| `POSTGRES_USER` | `postgres` | Superuser role |
| `POSTGRES_PASSWORD` | `postgres` | That role's password |

These are read **only when the `pgdata` volume is first created**. Changing them later has no effect until the volume is destroyed (`make db-destroy` — deletes all data, needs explicit permission).

**`config-service/backend/config/settings.py`** — Django settings that a deployed app would normally take from the environment:

| Setting | Value | Controls |
|---------|-------|----------|
| `SECRET_KEY` | a `django-insecure-…` literal committed to the repo | Cryptographic signing. Development-only by construction; must never be reused in a deployed environment. |
| `DEBUG` | `True` | Verbose error pages, no template caching. Never `True` outside local dev. |
| `ALLOWED_HOSTS` | `[]` | Empty is valid only because `DEBUG=True`; any deployment must populate it. |
| `DATABASES["default"]` | `config_service_db` / `postgres` / `postgres` @ `localhost:5432` | Must match the docker-compose values above — they are two copies of the same facts, so change them together. |
| `CORS_ALLOWED_ORIGINS` | `["http://localhost:5173"]` | The single browser origin allowed to call the API. |
| `TIME_ZONE` / `LANGUAGE_CODE` | `UTC` / `en-us` | Timestamp and locale handling. |

**Frontend:** no `.env` and no `VITE_*` variables. The API base URL is hardcoded in `src/services/api.js` as `http://localhost:8000/api/`; the router uses Vite's built-in `import.meta.env.BASE_URL`.

## 3. Developer scripts

Run every target from `config-service/`. `make` with no arguments lists them all.

### Bring the stack up

| Command | What it does |
|---------|--------------|
| `make up` | **The full stack in one command**: installs dependencies, starts Postgres, applies migrations, then runs the API (:8000) and SPA (:5173) concurrently. Ctrl+C stops both dev servers; the database keeps running. |
| `make backend` | Django dev server only (auto-starts the database) |
| `make frontend` | Vite dev server only |

### Install and migrate

| Command | What it does |
|---------|--------------|
| `make install` | Both stacks: creates `backend/venv` if missing, `pip install -r backend/requirements.txt`, and `npm install`. Idempotent. |
| `make install-backend` / `make install-frontend` | One stack only. Override the interpreter with `make PYTHON3=/path/to/python install-backend`. |
| `make migrate` | Apply Django migrations (auto-starts the database) |
| `make makemigrations` | Generate migrations after editing `backend/api/models.py`, then run `make migrate` |

### Test, build, operate

| Command | What it does |
|---------|--------------|
| `make test` | Backend suite via Django's test framework — 44 tests as of 2026-08-19 (34 api + 10 knowledge_graph). Auto-starts the database; uses a throwaway test database. |
| `make build` | Production frontend bundle into `frontend/dist/` |
| `make superuser` | Interactive `createsuperuser` for Django admin |
| `make shell` | Django shell inside the venv |
| `make clean` | Removes `frontend/dist/`, `__pycache__`, and `knowledge.db` — keeps venv, node_modules, and database data |

### Knowledge graph (no Docker needed)

| Command | What it does |
|---------|--------------|
| `make knowledge-import` | Rebuild `knowledge.db` from `knowledge/{nodes,edges}/*.yaml` — run after editing the YAML |
| `make knowledge-validate` | Fail if any edge references a missing node |
| `make knowledge-lookup TERM=…` | Look up a term by id, name, or alias; JSON output. Direct CLI adds `related`, `list-areas`, `--format table` |

### Database lifecycle

| Command | What it does |
|---------|--------------|
| `make db-up` | Start PostgreSQL detached; no-op if already running |
| `make db-down` | Stop it; data survives in the `pgdata` volume |
| `make db-status` | Container status |
| `make db-destroy` | **Destructive** — stops Postgres and deletes the volume and all data. Requires explicit permission every time. |

### Linting and type checking — planned, not yet configured

There is no ruff, flake8, black, or mypy in `requirements.txt`, and no eslint or prettier in `package.json` (both were declined when the Vue project was scaffolded). There is no `make lint` and no `make typecheck`.

**Never report a lint or type-check pass — there is nothing to run.** Do not silently add the tooling either; it means new dependencies, which needs approval.

This is expected to change: the tooling is planned. **When it is added, replace this section with the real commands** and follow the update checklist in [WORKFLOW_STATUS.md](WORKFLOW_STATUS.md#open-decisions) so the Makefile, this doc, and the BUILD & ASSESS gate all move together.

### Smoke checks

With the stack up:

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8000/api/users/    # expect 200
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:5173/              # expect 200
```

## 4. When to go off-script

The Makefile is the default path. Deviate deliberately when:

- **The operation has no target.** Other `manage.py` commands (`dbshell`, `showmigrations`, `loaddata`, `dumpdata`, `collectstatic`) are fine to run by hand — always via `backend/venv/bin/python`, always with `backend/` as the working directory.
- **The Docker daemon itself is down** (`Cannot connect to the Docker daemon` from any `docker` or `make db-*`/`make test` command). Start Docker Desktop with `open -a Docker`, then poll until `docker info` succeeds (typically 5-10s). Only the Postgres-dependent targets need this; the `knowledge-*` targets work without Docker entirely.
- **A port is already taken.** Don't start a second server or let Vite fall back to 5174 (CORS will reject it). Find the holder with `lsof -i :8000 -i :5173 -sTCP:LISTEN`, stop strays with `pkill -f "manage.py runserver"` or `pkill -f vite`, then re-run the target.
- **Dependencies changed.** After editing `requirements.txt` or `package.json`, run `make install` — the Makefile does not track those files, so nothing reinstalls on its own.
- **The database is in a bad state** (failed migration, schema drift). Diagnose first with `make shell`, `dbshell`, or `showmigrations`. `make db-destroy` is the last resort and needs the user's explicit go-ahead.
- **A manual sequence becomes routine.** Promote it to a Makefile target and document it here rather than repeating it.

Invariants that hold even off-script:

- Never use the system Python, and never `pip install` outside the venv.
- Never destroy data — `db-destroy`, `docker volume rm`, dropping tables — without explicit permission.
- Never add a dependency without approval.
- Never commit or push unless asked.
