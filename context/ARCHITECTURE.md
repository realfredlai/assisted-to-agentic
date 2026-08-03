# Architecture

This document is semantic memory for agents: it describes **how** `config-service` is built and runs. For the business domain see [DOMAIN.md](DOMAIN.md); for project purpose and scope see [ABOUT.md](ABOUT.md).

## System overview

Three-tier architecture; all business logic lives in the backend, the frontend is a presentation layer only.

```
┌─────────────────────┐   REST/JSON    ┌──────────────────────┐   Django ORM   ┌─────────────────────┐
│  Vue 3 SPA (Vite)   │ ──── axios ──► │  Django + DRF API    │ ─────────────► │  PostgreSQL 16      │
│  localhost:5173     │ ◄── CORS ───── │  localhost:8000      │                │  Docker, port 5432  │
└─────────────────────┘                └──────────────────────┘                └─────────────────────┘
```

## Tech stack (current, post-upgrade)

| Layer | Technology | Version |
|-------|-----------|---------|
| Runtime (backend) | Python (in `venv`) | 3.14 |
| Web framework | Django | 5.2.16 (LTS) |
| API framework | Django REST Framework | 3.17.1 |
| DB adapter | psycopg2-binary | 2.9.12 |
| CORS | django-cors-headers | 4.9.0 |
| Database | PostgreSQL (Docker) | 16 |
| Runtime (frontend) | Node.js | 22+ |
| SPA framework | Vue.js | 3.5 |
| Routing | Vue Router | 4 |
| HTTP client | axios | 1.x |
| Build tool | Vite (+ `@vitejs/plugin-vue`) | 6 |

Versions were upgraded from the original plan's pins (Django 5.1.9 → 5.2.16 etc.) by `prompts/7-web-api-versions-upgrade-plan.md`, merged as `bf9935b..4ff19f4`.

## Backend (`config-service/backend/`)

**Pattern: Model → Serializer → ViewSet → Router** — each layer in its own module under the `api` app:

- `api/models.py` — `User`, `Application`, `Configuration` models (see DOMAIN.md for field semantics); tables managed by ORM migrations in `api/migrations/` (`0001_initial` for `User`, `0002_application_configuration` adds the other two).
- `api/serializers.py` — `UserSerializer(ModelSerializer)`; `ApplicationSerializer(ModelSerializer)` (`users` as a writable `PrimaryKeyRelatedField(many=True)`); `ConfigurationSerializer(ModelSerializer)` (`application` read-only, per-field `validate_*_settings` reject non-dict values, `validate()` enforces per-application name uniqueness using `self.context["view"].kwargs["application_pk"]`).
- `api/views.py` — `UserViewSet(ModelViewSet)` and `ApplicationViewSet(ModelViewSet)`: full CRUD in ~4 lines each, no custom actions. `ConfigurationViewSet(ModelViewSet)` overrides `get_queryset()` (404s via `get_object_or_404(Application, pk=self.kwargs["application_pk"])`, then filters `Configuration.objects.filter(application_id=...)`) and `perform_create()` (re-resolves the application and passes it explicitly to `serializer.save(application=application)`).
- `api/urls.py` — DRF `DefaultRouter` registers `users/` and `applications/` as top-level viewsets. `ConfigurationViewSet` is **not** router-registered; it is hand-wired with `ConfigurationViewSet.as_view({...})` action maps (`configuration_list` for GET/POST, `configuration_detail` for GET/PUT/PATCH/DELETE) bound to explicit `path()` entries under `applications/<int:application_pk>/configurations/`. This avoids adding `drf-nested-routers` as a dependency — the project's minimal-dependency policy stands; the nesting is implemented by hand with plain DRF primitives instead.
- `config/urls.py` — mounts the api app under `/api/` and Django admin under `/admin/`.
- `api/admin.py` — `admin.site.register(User)`, `admin.site.register(Application)`, `admin.site.register(Configuration)`.

**API surface:**

| Method | URL | Action |
|--------|-----|--------|
| GET | `/api/users/` | List (ordered by last, first name) |
| POST | `/api/users/` | Create (400 on duplicate email) |
| GET | `/api/users/{id}/` | Retrieve |
| PUT / PATCH | `/api/users/{id}/` | Update |
| DELETE | `/api/users/{id}/` | Delete (204) |
| GET | `/api/applications/` | List (ordered by name) |
| POST | `/api/applications/` | Create (400 on duplicate name, invalid `app_type`, or unknown user id in `users`) |
| GET | `/api/applications/{id}/` | Retrieve |
| PUT / PATCH | `/api/applications/{id}/` | Update, incl. replacing the `users` M2M set |
| DELETE | `/api/applications/{id}/` | Delete (204); cascades and deletes its configurations |
| GET | `/api/applications/{app_id}/configurations/` | List configurations for that application (ordered by name); 404 if `app_id` doesn't exist |
| POST | `/api/applications/{app_id}/configurations/` | Create under that application (`application` forced from the URL, never from the body); 404 if `app_id` doesn't exist; 400 on duplicate name within the application or non-object settings |
| GET | `/api/applications/{app_id}/configurations/{id}/` | Retrieve; 404 if `id` doesn't exist under `app_id` (incl. when it exists under a *different* application) |
| PUT / PATCH | `/api/applications/{app_id}/configurations/{id}/` | Update |
| DELETE | `/api/applications/{app_id}/configurations/{id}/` | Delete (204) |

No pagination, filtering, throttling, or auth is configured (`REST_FRAMEWORK` settings block is absent — DRF defaults apply). Responses are plain JSON arrays/objects.

**Configuration** (`config/settings.py`):

- `INSTALLED_APPS` adds `rest_framework`, `corsheaders`, `api`.
- `corsheaders.middleware.CorsMiddleware` sits **above** `CommonMiddleware`; `CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]`.
- `DATABASES`: hardcoded PostgreSQL connection (`config_service_db` / `postgres` / `postgres` @ `localhost:5432`) — an accepted MVP decision, no env-var indirection.

## Frontend (`config-service/frontend/`)

**Pattern: component-based SPA with an axios service layer:**

- `src/services/api.js` — the only place HTTP happens: a single axios instance (`baseURL: "http://localhost:8000/api/"`) with one exported function per operation — `getUsers()`, plus `getApplications`/`getApplication`/`createApplication`/`updateApplication`/`deleteApplication`, and `getConfigurations`/`getConfiguration`/`createConfiguration`/`updateConfiguration`/`deleteConfiguration` (the last five take `appId` as their first argument to build the nested URL). The frontend calls the backend directly (no Vite proxy) — CORS on the backend permits it.
- `src/views/HomeView.vue` — route-level page; fetches users on `mounted()`, tracks `loading` / `error` state, passes `users` down as a prop.
- `src/views/ApplicationListView.vue` — fetches and lists applications; handles delete (with `window.confirm`) and re-fetches.
- `src/views/ApplicationDetailView.vue` — fetches one application, its configurations, and the full user list in parallel (`Promise.all`); derives `linkedUsers` as a computed property; hosts the nested configuration list and its delete handling.
- `src/views/ApplicationFormView.vue` — single component for both create and new (`isEdit` computed from `$route.params.id`); renders name/app_type/users-checkboxes fields; on submit, catches DRF's `err.response.data` and renders it as per-field errors (`fieldErrors`) plus a general/`non_field_errors` message.
- `src/views/ConfigurationFormView.vue` — single component for both create and edit (`isEdit` computed from `$route.params.configId`); renders name plus three JSON `<textarea>`s (dev/uat/prod); client-side `parseSettings()` validates each textarea is parseable JSON and a plain object *before* the request is sent (`jsonErrors`), independent of the DRF field-error rendering used for server-side validation failures.
- `src/components/UserList.vue` — presentational; receives `users` via prop, renders "`first_name` `last_name` — `email`" list items or "No users found."
- `src/components/ApplicationList.vue` — presentational table; receives `applications` via prop, links to detail/edit, emits `delete`.
- `src/components/ConfigurationList.vue` — presentational; receives `configurations` via prop, renders each with its three settings blocks as `<pre>{{ JSON.stringify(...) }}</pre>`, links to edit, emits `delete`.
- `src/router/index.js` — Vue Router (HTML5 history mode) with routes: `/` (Home), `/applications`, `/applications/new`, `/applications/:id`, `/applications/:id/edit`, `/applications/:id/configurations/new`, `/applications/:id/configurations/:configId/edit`.
- `src/App.vue` — root component; nav bar with `Users` (`/`) and `Applications` (`/applications`) links, then `<router-view/>`.
- No state management library (Pinia/Vuex), no TypeScript — explicit MVP exclusions.

## Data flow (list users)

`HomeView.mounted()` → `api.getUsers()` → axios `GET http://localhost:8000/api/users/` → CORS middleware → DRF router → `UserViewSet.list()` → `UserSerializer` → `User.objects.all()` (ordered) → PostgreSQL → JSON array → `HomeView.users` → `UserList` props → rendered `<li>` items.

## Data flow (create a configuration)

`ConfigurationFormView.handleSubmit()` parses/validates the three JSON textareas client-side → `api.createConfiguration(appId, payload)` → axios `POST /api/applications/{appId}/configurations/` → hand-rolled `configuration_list` view → `ConfigurationViewSet.perform_create()` resolves the `Application` (404 if missing) → `ConfigurationSerializer` validates `name` uniqueness within that application and that each settings field is an object → `Configuration.objects.create(application=..., ...)` → PostgreSQL → JSON response → SPA navigates back to `application-detail`.

## Database & migrations

- PostgreSQL 16 runs via `config-service/docker-compose.yml` (service `db`, named volume `pgdata` for persistence).
- Schema is owned entirely by Django ORM: change `models.py` → `python manage.py makemigrations api` → `python manage.py migrate`.
- Bootstrapping: `migrate` + optional `createsuperuser` for admin access; seed data via the API, admin, or fixtures.

## Testing

- Django's default framework only: `django.test.TestCase` + DRF `APITestCase`/`APIClient` in `backend/api/tests.py`.
- 34 tests across six classes:
  - `UserModelTest` (2): creation, `__str__`.
  - `UserAPITest` (5): list, create, retrieve, update, delete.
  - `ApplicationModelTest` (4): creation, `__str__`, cascade-delete of configurations, deleting a linked user leaves the application in place.
  - `ConfigurationModelTest` (4): settings default to `{}`, `__str__`, duplicate name within an application raises `IntegrityError`, same name allowed under a different application.
  - `ApplicationAPITest` (9): list ordering, create (valid / duplicate name / invalid `app_type` / with users / unknown user id), retrieve, patch `users`, delete cascades its configurations.
  - `ConfigurationAPITest` (10): nested list scoped to its application, create (settings default / non-object settings rejected / duplicate name / same name under another application), retrieve, update via PUT and PATCH, delete, unknown application id 404s list and create, configuration id under the wrong application 404s.
- Run: `cd config-service/backend && source venv/bin/activate && python manage.py test` — requires the Postgres container up (tests create/destroy a `test_config_service_db`).

## Development workflow

Everyday tasks are driven by `config-service/Makefile` (run from `config-service/`; `make` alone lists all targets):

```
make up          # full stack: installs deps, starts db, migrates, runs API :8000 + SPA :5173 (Ctrl+C stops)
make test        # backend test suite (starts db if needed)
make install     # venv + pip install, npm install
make migrate     # apply migrations        make makemigrations  # generate after model changes
make backend     # API only :8000          make frontend        # SPA only :5173
make db-up       # start Postgres          make db-down         # stop (data kept)
make superuser   # Django admin account    make shell           # Django shell
make build       # production frontend build (frontend/dist/)
make db-destroy  # stop Postgres AND delete all data
```

The equivalent manual commands (docker compose / manage.py / npm directly) are documented in `config-service/README.md`.

## Key architectural decisions

Recorded in `prompts/4-web-api-plan-answers.md` and the implementation plan:

1. **django-cors-headers over a Vite dev proxy** — the SPA talks to the backend's real origin in dev.
2. **axios over native fetch** — explicit preference; wrapped in a service module so components never touch HTTP directly.
3. **Vite + Vue Router** — standard Vue 3 tooling; approved additions to the spec.
4. **No extra dependencies** — no Pinia, TypeScript, pytest, dotenv, or production servers (gunicorn/uvicorn); Django's built-ins and the approved list only.
5. **Hardcoded MVP config** — DB credentials and CORS origins live directly in `settings.py`; acceptable for a local-only learning project.
6. **Hand-rolled nested routing over `drf-nested-routers`** — `prompts/8-web-api-config-storage-specs.md` required nested `/api/applications/{app_id}/configurations/` routes without adding a new dependency. Rather than a router package, `ConfigurationViewSet` is bound with explicit `.as_view({...})` action maps and plain `path()` entries in `api/urls.py`, and it resolves/validates the parent `Application` itself in `get_queryset()`/`perform_create()`. Same minimal-dependency policy as decision 4, applied to the new resource.
