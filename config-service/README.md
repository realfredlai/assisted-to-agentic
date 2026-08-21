# Config Service

A full stack application consisting of a Django REST Framework (DRF) backend API and a Vue.js Single Page Application (SPA) frontend, backed by PostgreSQL.

## Tech Stack

- **Backend:** Python 3.14, Django 5.2, Django REST Framework 3.17, django-cors-headers 4.9, PyYAML 6.0
- **Frontend:** Vue.js 3.5, Vue Router 4, axios, Vite 6
- **Database:** PostgreSQL 16 (Docker)

## Prerequisites

- Python 3.12+ (available at `/opt/homebrew/bin/python3` or via `brew install python`)
- Node.js 22+ (available at `/opt/homebrew/bin/node` or via `brew install node`)
- Docker and Docker Compose (Docker Desktop for macOS)

## Project Structure

```
config-service/
├── docker-compose.yml          # PostgreSQL container
├── backend/
│   ├── manage.py               # Django management CLI
│   ├── requirements.txt        # Python dependencies
│   ├── venv/                   # Python virtual environment
│   ├── config/                 # Django project settings
│   │   ├── settings.py         # DB, CORS, installed apps config
│   │   └── urls.py             # Root URL routing
│   ├── api/                    # DRF application
│       ├── models.py           # User, Application, Configuration models
│       ├── serializers.py      # UserSerializer, ApplicationSerializer, ConfigurationSerializer
│       ├── views.py            # UserViewSet, ApplicationViewSet, ConfigurationViewSet (CRUD)
│       ├── urls.py             # API routing (/api/users/, /api/applications/, nested configurations)
│       ├── tests.py            # 34 tests (model + API)
│       └── migrations/         # Database migrations
│   └── knowledge_graph/        # Knowledge graph app (storage, importer, manage.py knowledge CLI, 10 tests)
├── knowledge/                  # Domain knowledge YAML (nodes/ + edges/; source of truth: context/DOMAIN.md)
└── frontend/
    ├── package.json            # Node dependencies
    ├── vite.config.js          # Vite build config
    ├── index.html              # SPA entry point
    └── src/
        ├── main.js             # Vue app bootstrap
        ├── App.vue             # Root component; nav (Users | Applications)
        ├── router/index.js     # Vue Router config (users + applications + configurations routes)
        ├── views/HomeView.vue             # Home page — fetches and displays users
        ├── views/ApplicationListView.vue  # Application list page
        ├── views/ApplicationDetailView.vue # Application detail + its configurations
        ├── views/ApplicationFormView.vue   # Application create/edit form
        ├── views/ConfigurationFormView.vue # Configuration create/edit form
        ├── components/UserList.vue         # User list component
        ├── components/ApplicationList.vue  # Application list component
        ├── components/ConfigurationList.vue # Configuration list component
        └── services/api.js     # axios API client
```

## Quick Start (Make)

All regular tasks are wrapped in the [Makefile](Makefile). From `config-service/`:

```bash
make up
```

installs all dependencies (venv + pip, npm), starts PostgreSQL, applies migrations, and runs the API on :8000 and the SPA on :5173 (Ctrl+C stops both servers; `make db-down` stops the database). Other frequent targets: `make test`, `make migrate`, `make superuser`, `make build` — run `make` alone to list them all.

The sections below document the equivalent manual commands.

## Getting Started

### 1. Start PostgreSQL

```bash
cd config-service
docker compose up -d
```

This starts a PostgreSQL 16 container on port 5432 with:
- Database: `config_service_db`
- User: `postgres`
- Password: `postgres`

Verify it's running:

```bash
docker compose ps
```

### 2. Set Up the Backend

**First time only** — create the virtual environment and install dependencies:

```bash
cd config-service
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
```

**Apply database migrations:**

```bash
cd config-service/backend
source venv/bin/activate
python manage.py migrate
```

**Start the Django development server:**

```bash
cd config-service/backend
source venv/bin/activate
python manage.py runserver
```

The API is now available at `http://localhost:8000/api/`.

### 3. Set Up the Frontend

**First time only** — install Node dependencies:

```bash
cd config-service/frontend
npm install
```

**Start the Vite development server:**

```bash
cd config-service/frontend
npm run dev
```

The app is now available at `http://localhost:5173/`.

## Running All Three Services

Open three separate terminals:

```bash
# Terminal 1 — PostgreSQL
cd config-service && docker compose up -d

# Terminal 2 — Backend (port 8000)
cd config-service/backend && source venv/bin/activate && python manage.py runserver

# Terminal 3 — Frontend (port 5173)
cd config-service/frontend && npm run dev
```

Then open `http://localhost:5173` in the browser.

## SPA Pages

The nav bar (Users | Applications) links the two areas of the app:

| Route | Page | Description |
|-------|------|-------------|
| `/` | Home | Lists users (display-only; no create/edit/delete UI) |
| `/applications` | Application list | Lists all applications with type and linked-user count |
| `/applications/new` | Application form | Create an application (name, type, linked users via checkboxes) |
| `/applications/:id` | Application detail | Shows the application plus its configurations |
| `/applications/:id/edit` | Application form | Edit an application |
| `/applications/:id/configurations/new` | Configuration form | Create a configuration for the application (three JSON textareas: dev/uat/prod) |
| `/applications/:id/configurations/:configId/edit` | Configuration form | Edit a configuration |

Users remain display-only in the SPA — creating, editing, and deleting users is only possible via the API or Django admin. Application and configuration forms validate JSON textareas client-side before submit and render field-level errors returned by DRF.

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/users/` | List all users |
| `POST` | `/api/users/` | Create a new user |
| `GET` | `/api/users/{id}/` | Retrieve a user |
| `PUT` | `/api/users/{id}/` | Update a user |
| `DELETE` | `/api/users/{id}/` | Delete a user |
| `GET` | `/api/applications/` | List all applications |
| `POST` | `/api/applications/` | Create a new application |
| `GET` | `/api/applications/{id}/` | Retrieve an application |
| `PUT` | `/api/applications/{id}/` | Update an application |
| `DELETE` | `/api/applications/{id}/` | Delete an application (cascades its configurations) |
| `GET` | `/api/applications/{app_id}/configurations/` | List configurations for an application |
| `POST` | `/api/applications/{app_id}/configurations/` | Create a configuration for an application |
| `GET` | `/api/applications/{app_id}/configurations/{id}/` | Retrieve a configuration |
| `PUT` | `/api/applications/{app_id}/configurations/{id}/` | Update a configuration |
| `DELETE` | `/api/applications/{app_id}/configurations/{id}/` | Delete a configuration |

Nested `configurations` routes are hand-rolled (no `drf-nested-routers` dependency): `application` on a configuration is always derived from the URL's `{app_id}`, never accepted in the request body. Unknown `{app_id}` or a configuration id that belongs to a different application both return `404`.

### Example: Create a User

```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Alice","last_name":"Smith","email":"alice@example.com"}'
```

### Example: List Users

```bash
curl http://localhost:8000/api/users/
```

### Example: Create an Application (with linked users)

```bash
curl -X POST http://localhost:8000/api/applications/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Payments","app_type":"web","users":[1,2]}'
```

`app_type` must be one of `mobile`, `desktop`, `web`, `cloud`. `name` must be unique across all applications.

### Example: Create a Configuration for an Application

```bash
curl -X POST http://localhost:8000/api/applications/1/configurations/ \
  -H "Content-Type: application/json" \
  -d '{"name":"default","dev_settings":{"debug":true},"uat_settings":{},"prod_settings":{}}'
```

`name` must be unique within the application (but may repeat across applications). Each of `dev_settings`, `uat_settings`, `prod_settings` defaults to `{}` and must be a JSON object — arrays or scalars are rejected with `400`.

## Knowledge Graph

The domain language of this service (User, Application, Configuration, …) is queryable as a small knowledge graph: hand-authored YAML in `knowledge/{nodes,edges}/`, imported into a local SQLite file (`knowledge.db`, gitignored), queried via `manage.py knowledge`. Works without Docker — the graph never touches Postgres.

```bash
make knowledge-import              # rebuild knowledge.db from the YAML (run after editing it)
make knowledge-validate            # check for edges pointing at missing nodes
make knowledge-lookup TERM=app     # look up a term by id, name, or alias (JSON)
```

Direct CLI use (from `backend/`, venv active) adds `related <term>`, `list-areas`, and `--format table` for human-readable output:

```bash
python manage.py knowledge lookup "config entry" --format table
python manage.py knowledge related application
```

The YAML is a projection of `context/DOMAIN.md` — if they disagree, DOMAIN.md wins and the YAML gets corrected.

## Running Tests

```bash
cd config-service/backend
source venv/bin/activate
python manage.py test
```

Expected: 44 tests pass (34 api tests: User/Application/Configuration models and API; 10 knowledge_graph tests: import, lookup, related, validate, list-areas).

## Stopping Services

```bash
# Stop the frontend — Ctrl+C in Terminal 3
# Stop the backend — Ctrl+C in Terminal 2

# Stop PostgreSQL
cd config-service && docker compose down
```

To remove the database volume (deletes all data):

```bash
cd config-service && docker compose down -v