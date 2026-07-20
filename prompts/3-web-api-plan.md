# Full Stack RESTful API + SPA — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold and structure a full stack application consisting of a Django REST Framework (DRF) backend API and a Vue.js Single Page Application (SPA) frontend, backed by a PostgreSQL database.

**Architecture:** A 3-tier architecture — Vue.js SPA frontend communicates via REST/JSON with a DRF backend that manages all business logic and interacts with PostgreSQL through Django's native ORM. Frontend and backend are separate applications in a single monorepo, developed and served independently.

**Tech Stack:** Python 3.12 (LTS), Django 5.1, Django REST Framework 3.15, PostgreSQL, Vue.js 3.5, Vite 6, Node.js 22 (LTS)

## Global Constraints

- Python must be the latest LTS version (3.12.x at time of writing — verify at implementation time)
- All Python code runs inside a virtual environment (`venv`)
- Vue.js must be on the latest stable version (3.x — verify at implementation time)
- No additional dependencies beyond what the specifications require without explicit approval
- All business logic resides in the backend (DRF) — the frontend is a presentation layer only
- Testing uses Django's default test framework (`django.test`) — no additional test tools
- Database managed entirely through Django ORM migrations and bootstrapping

---

## Open Questions

The following items are missing or ambiguous in the specifications and should be clarified before or during implementation:

1. **Application domain**: The specs describe the technology stack but not what the application does. What models/resources does the API expose? Without this, the plan covers project scaffolding and architectural setup only.
2. **Vue Router** *(approval needed)*: An SPA requires client-side routing. Vue Router is the official routing library for Vue.js. It is not explicitly listed in the specs but is functionally required for an SPA.
3. **Build tooling** *(approval needed)*: Vue.js 3 projects require a build tool. Vite is the standard build tool shipped with `create-vue` (the official Vue scaffolding tool). It is not explicitly listed in the specs.
4. **CORS handling**: If the frontend dev server (e.g. port 5173) and backend dev server (e.g. port 8000) run on separate origins, cross-origin requests must be handled. This plan uses Vite's built-in dev proxy to avoid adding a backend dependency. If a backend solution is preferred, `django-cors-headers` would need approval.
5. **HTTP client**: The frontend needs to make API calls. This plan uses the browser-native `fetch` API to avoid adding a dependency (e.g. `axios`).
6. **Authentication/authorization**: No auth requirements are specified. Is the API public, or will auth be needed?
7. **Project name**: What should the Django project and Vue app be named? This plan uses `config` for the Django project and `frontend` for the Vue app.
8. **Deployment**: Are there any deployment requirements (Docker, reverse proxy, etc.)?

---

## 1. Dependencies

### 1.1 Backend (Python / pip)

| Package | Version | Justification |
|---------|---------|---------------|
| `Python` | 3.12.x (latest LTS) | Runtime — latest LTS version as specified |
| `Django` | 5.1.x | Web framework — required foundation for Django REST Framework |
| `djangorestframework` | 3.15.x | REST API framework — explicitly required by application specs |
| `psycopg2-binary` | 2.9.x | PostgreSQL database adapter — required for Django to connect to the Postgres database specified in the specs |

All versions should be pinned to exact patch versions in `requirements.txt` at implementation time.

### 1.2 Frontend (Node.js / npm)

| Package | Version | Justification |
|---------|---------|---------------|
| `Node.js` | 22.x (LTS) | Runtime — required to develop and build the Vue.js application |
| `vue` | 3.5.x (latest stable) | Frontend SPA framework — explicitly required by application specs |

### 1.3 Dependencies Pending Approval

These are not explicitly listed in the specs but are functionally required to build the application as specified. Each needs explicit approval before inclusion:

| Package | Version | Tier | Why It Is Needed |
|---------|---------|------|------------------|
| `vue-router` | 4.x | Frontend | Official Vue.js router — required for SPA client-side navigation; without it the app cannot function as an SPA |
| `vite` | 6.x | Frontend (dev) | Build tool and dev server — standard tooling for Vue 3 projects; ships with `create-vue`; required to compile `.vue` single-file components |
| `@vitejs/plugin-vue` | 5.x | Frontend (dev) | Vite plugin — required for Vite to process Vue single-file components |

### 1.4 Dependencies NOT Included (per spec constraint)

The following are commonly used in projects like this but are **not included** because they are not required by the specifications:

- `axios` — HTTP client library; the browser-native `fetch` API is used instead
- `django-cors-headers` — CORS middleware; avoided by using Vite's dev proxy
- `pinia` / `vuex` — state management; not specified in requirements
- `TypeScript` — not specified in requirements
- `pytest` / `pytest-django` — the spec says Django's default test framework is sufficient
- `python-dotenv` / `django-environ` — environment variable management; not specified
- `gunicorn` / `uvicorn` — production WSGI/ASGI servers; no deployment requirements specified

---

## 2. File/Folder Structure

```
project-root/
├── README.md                          # Project overview, setup instructions
│
├── backend/
│   ├── manage.py                      # Django management CLI entry point
│   ├── requirements.txt               # Pinned Python dependencies
│   │
│   ├── config/                        # Django project configuration
│   │   ├── __init__.py
│   │   ├── settings.py                # Django settings (DB, installed apps, middleware, DRF config)
│   │   ├── urls.py                    # Root URL configuration — mounts api/ namespace
│   │   ├── wsgi.py                    # WSGI application entry point
│   │   └── asgi.py                    # ASGI application entry point
│   │
│   └── api/                           # DRF application — all API code and business logic
│       ├── __init__.py
│       ├── apps.py                    # Django app configuration
│       ├── models.py                  # Django ORM models — database schema definitions
│       ├── serializers.py             # DRF serializers — validation and JSON representation
│       ├── views.py                   # DRF views/viewsets — request handling and business logic
│       ├── urls.py                    # API URL routing — DRF router registration
│       ├── admin.py                   # Django admin site registration
│       ├── tests.py                   # Tests using django.test.TestCase
│       └── migrations/                # Django auto-generated database migration files
│           └── __init__.py
│
└── frontend/
    ├── package.json                   # Node.js dependencies and npm scripts
    ├── vite.config.js                 # Vite configuration — dev proxy, plugins
    ├── index.html                     # SPA entry HTML file (Vite entry point)
    │
    └── src/
        ├── main.js                    # Vue app initialization — creates app, mounts router
        ├── App.vue                    # Root Vue component — contains <router-view>
        │
        ├── router/
        │   └── index.js               # Vue Router — route definitions mapping paths to views
        │
        ├── views/                     # Page-level Vue components — one per route
        │   └── HomeView.vue           # Default home page view
        │
        ├── components/                # Reusable UI components — shared across views
        │
        └── services/
            └── api.js                 # API client — centralised fetch wrapper for backend calls
```

### Structure Rationale

- **`backend/config/`** — Named `config` (not a project-name like `myproject`) to clearly separate Django configuration from application code. Generated by `django-admin startproject config .`.
- **`backend/api/`** — Single Django app housing all API code. The specs define one API tier with all business logic, so one app is sufficient. If the domain grows, additional apps can be added alongside.
- **`frontend/src/services/api.js`** — Centralised API client module. All views call this module instead of scattering `fetch` calls throughout the codebase. Makes it easy to change base URLs, headers, or error handling in one place.
- **`frontend/src/views/`** vs **`frontend/src/components/`** — Standard Vue.js convention: `views/` holds route-level page components; `components/` holds reusable UI elements shared across views.
- **Monorepo** — Backend and frontend live in the same repository under separate top-level directories. They share no code at build time but are versioned together.

---

## 3. Architectural Patterns

### 3.1 Backend: Model → Serializer → ViewSet → Router

The DRF backend follows a layered pattern where each layer has a single responsibility:

1. **Models** (`api/models.py`)
   - Define the database schema as Python classes using Django's ORM
   - Each model maps to a PostgreSQL table
   - Field constraints, relationships (ForeignKey, ManyToMany), and database-level validation are defined here
   - Models are the single source of truth for the data schema

2. **Serializers** (`api/serializers.py`)
   - Handle two-way data transformation:
     - **Deserialization** (input): validate incoming JSON request data and convert to Python objects
     - **Serialization** (output): convert model instances to JSON-compatible dictionaries for API responses
   - Use `ModelSerializer` to derive fields from model definitions, reducing duplication
   - Custom validation logic (beyond field-level) is implemented as serializer methods

3. **Views / ViewSets** (`api/views.py`)
   - Handle the HTTP request/response cycle
   - **All business logic resides here** (per spec requirement)
   - Use `ModelViewSet` for standard CRUD operations (list, create, retrieve, update, destroy)
   - Custom business logic is implemented as additional viewset actions or standalone `APIView` subclasses
   - Views call serializers for data validation and models/ORM for database operations

4. **URL Routing** (`api/urls.py` mounted in `config/urls.py`)
   - DRF's `DefaultRouter` auto-generates URL patterns from registered viewsets
   - Produces standard RESTful URL patterns (e.g. `/api/items/`, `/api/items/{id}/`)
   - The API app's URLs are included under the `/api/` prefix in the root URL configuration

**Request lifecycle:**
```
HTTP Request → config/urls.py → api/urls.py (Router) → ViewSet → Serializer → Model/ORM → PostgreSQL
                                                                                              ↓
HTTP Response ← ViewSet ← Serializer (JSON) ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←← Query Result ←┘
```

### 3.2 Database: Django ORM + PostgreSQL

**Connection Configuration:**
- PostgreSQL connection is configured in `config/settings.py` under `DATABASES`
- Uses `django.db.backends.postgresql` engine with `psycopg2-binary` as the adapter
- Connection parameters: database name, user, password, host, port

**Migration Strategy:**
- All schema changes are managed through Django's built-in migration framework
- Workflow: modify `models.py` → run `makemigrations` to generate migration files → run `migrate` to apply to the database
- Migration files are version-controlled in `api/migrations/` — they form a complete, reproducible history of schema evolution
- Migrations are applied in order and are idempotent (safe to re-run)

**Bootstrapping:**
- Initial database setup: `python manage.py migrate` applies all migrations (including Django's built-in auth, sessions, etc.)
- Seed data can be loaded via Django fixtures (`python manage.py loaddata`) or custom management commands
- Superuser creation: `python manage.py createsuperuser`

### 3.3 Frontend: Component-Based SPA with Service Layer

1. **Single-File Components** (`.vue` files)
   - Each component encapsulates template (HTML), logic (JavaScript), and scoped styles (CSS) in one file
   - This is Vue.js's standard authoring format, compiled by Vite + `@vitejs/plugin-vue`

2. **View Components** (`src/views/`)
   - One component per route/page (e.g. `HomeView.vue`, `DetailView.vue`)
   - These are "smart" components — they call the API service, manage page-level state, and pass data to child components via props

3. **Reusable Components** (`src/components/`)
   - "Dumb" / presentational components that receive data via props and emit events
   - No direct API calls — they only render what they're given
   - Reusable across multiple views

4. **Vue Router** (`src/router/index.js`)
   - Manages client-side navigation — the browser never performs a full page reload
   - Routes map URL paths to view components
   - `<router-view>` in `App.vue` renders the matched view component
   - `<router-link>` provides navigation without page reloads

5. **API Service Layer** (`src/services/api.js`)
   - Wraps the browser-native `fetch` API — no additional HTTP library needed
   - All API calls go through this module, which handles:
     - Base URL construction (e.g. `/api/`)
     - Request headers (`Content-Type: application/json`)
     - JSON parsing of responses
     - Error handling
   - Views import and call functions from this module (e.g. `api.getItems()`, `api.createItem(data)`)

### 3.4 Frontend ↔ Backend Communication

- **Protocol:** RESTful HTTP with JSON request/response bodies
- **URL convention:** All backend endpoints are prefixed with `/api/` (e.g. `/api/items/`, `/api/items/1/`)
- **Development setup:** Two separate dev servers run simultaneously:
  - Vite dev server: `http://localhost:5173` (frontend)
  - Django dev server: `http://localhost:8000` (backend)
  - Vite's proxy configuration forwards requests matching `/api/*` to the Django server, so the frontend makes same-origin requests and no CORS handling is needed during development
- **Data flow:** View component → `api.js` (fetch) → DRF ViewSet → Serializer → Model/ORM → PostgreSQL → response flows back through the same layers in reverse

**Vite proxy configuration** (`vite.config.js`):
```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

### 3.5 Testing Strategy

- **Framework:** Django's default `django.test.TestCase` and DRF's `APITestCase` (which extends Django's `TestCase`)
- **Test location:** `backend/api/tests.py` — can be expanded to a `tests/` package with multiple test modules as the test suite grows
- **What to test:**
  - Model logic — field validation, custom methods, relationships
  - Serializer validation — input validation rules, custom validators
  - API endpoints — request/response cycle using DRF's `APIClient` (status codes, response data, error cases)
- **Running tests:** `cd backend && python manage.py test`
- **Frontend testing:** Not specified in the requirements. No frontend testing tools are included per the dependency constraint.

---

## 4. Implementation Tasks

### Task 1: Backend Project Scaffolding

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/config/` (generated by `django-admin startproject`)
- Create: `backend/api/` (generated by `python manage.py startapp`)

- [ ] Create the project root directory and `backend/` subdirectory
- [ ] Create a Python virtual environment: `python3 -m venv backend/venv`
- [ ] Activate the virtual environment: `source backend/venv/bin/activate`
- [ ] Create `backend/requirements.txt` with pinned dependencies:
  ```
  Django==5.1.*
  djangorestframework==3.15.*
  psycopg2-binary==2.9.*
  ```
  *(Pin exact patch versions at implementation time)*
- [ ] Install dependencies: `cd backend && pip install -r requirements.txt`
- [ ] Scaffold the Django project: `cd backend && django-admin startproject config .`
- [ ] Create the API app: `cd backend && python manage.py startapp api`
- [ ] Edit `config/settings.py`:
  - Add `'rest_framework'` and `'api'` to `INSTALLED_APPS`
  - Configure `DATABASES` to use PostgreSQL (`django.db.backends.postgresql`)
- [ ] Ensure PostgreSQL is running and the target database exists
- [ ] Apply initial migrations: `python manage.py migrate`
- [ ] Verify the server starts: `python manage.py runserver`
- [ ] Commit: `feat: scaffold Django backend with DRF and PostgreSQL`

### Task 2: Backend API Structure

**Files:**
- Modify: `backend/api/models.py`
- Modify: `backend/api/serializers.py`
- Modify: `backend/api/views.py`
- Create/Modify: `backend/api/urls.py`
- Modify: `backend/config/urls.py`
- Modify: `backend/api/tests.py`

*Note: Specific models, serializers, and viewsets depend on the application domain (see Open Questions #1). The steps below establish the structural pattern — replace the placeholder resource with actual domain models once clarified.*

- [ ] Define an initial model in `api/models.py`
- [ ] Generate and apply migrations: `python manage.py makemigrations api && python manage.py migrate`
- [ ] Create a `ModelSerializer` in `api/serializers.py` for the model
- [ ] Create a `ModelViewSet` in `api/views.py` for the model
- [ ] Create `api/urls.py` with a `DefaultRouter` and register the viewset
- [ ] Mount `api.urls` in `config/urls.py` under the `api/` prefix using `include()`
- [ ] Write tests in `api/tests.py` using `APITestCase`:
  - Test list endpoint returns 200
  - Test create endpoint creates a record
  - Test retrieve endpoint returns correct data
  - Test update and delete operations
- [ ] Run tests: `python manage.py test`
- [ ] Verify endpoints manually: `python manage.py runserver` and use `curl` or browser
- [ ] Commit: `feat: add API models, serializers, viewsets, and URL routing`

### Task 3: Frontend Project Scaffolding

**Files:**
- Create: `frontend/` (generated by `npm create vue@latest`)
- Create: `frontend/src/services/api.js`

- [ ] Scaffold the Vue.js project: `npm create vue@latest frontend`
  - Select: Add Vue Router for SPA — **Yes** *(pending approval — see Open Questions #2)*
  - Select: Add Pinia — **No**
  - Select: Add TypeScript — **No**
  - Select: Add JSX — **No**
  - Select: Add Vitest / Cypress / Playwright — **No**
  - Select: Add ESLint — **No** (not in specs; add only if approved)
- [ ] Install dependencies: `cd frontend && npm install`
- [ ] Verify the dev server starts: `npm run dev`
- [ ] Create `frontend/src/services/api.js` — implement a `fetch`-based API client module with functions for GET, POST, PUT, DELETE requests against `/api/` endpoints
- [ ] Configure Vite dev proxy in `frontend/vite.config.js` — proxy `/api` requests to `http://localhost:8000`
- [ ] Verify the proxy works: start both servers and confirm a frontend `fetch('/api/...')` call reaches the Django backend
- [ ] Commit: `feat: scaffold Vue.js frontend with API service layer and dev proxy`

### Task 4: Frontend–Backend Integration

**Files:**
- Modify: `frontend/src/views/HomeView.vue`
- Modify: `frontend/src/services/api.js`

- [ ] Import and call the API service from `HomeView.vue` to fetch data from the backend
- [ ] Display the fetched data in the view template
- [ ] Verify the full data flow: Vue.js → fetch → Vite proxy → DRF → ORM → PostgreSQL → response → Vue.js rendered output
- [ ] Run backend tests: `cd backend && python manage.py test`
- [ ] Commit: `feat: integrate frontend views with backend API`

---

## 5. Development Workflow Summary

1. **Start PostgreSQL** — ensure the database server is running
2. **Start the backend** — `cd backend && source venv/bin/activate && python manage.py runserver`
3. **Start the frontend** — `cd frontend && npm run dev`
4. **Access the app** — open `http://localhost:5173` in the browser
5. **Run tests** — `cd backend && python manage.py test`