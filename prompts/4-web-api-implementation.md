# Config Service — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full stack application that exposes a User model via a Django REST Framework API and displays the user list in a Vue.js Single Page Application, backed by PostgreSQL running in Docker.

**Architecture:** 3-tier architecture — Vue.js SPA frontend communicates via REST/JSON (using axios) with a DRF backend that manages all business logic. The backend uses `django-cors-headers` for cross-origin requests and interacts with PostgreSQL through Django's native ORM. Both backend and frontend live inside the `./config-service/` directory.

**Tech Stack:** Python 3.12 (LTS), Django 5.1, Django REST Framework 3.15, PostgreSQL (Docker), django-cors-headers, Vue.js 3.5, Vue Router 4, Vite 6, axios, Node.js 22 (LTS)

## Global Constraints

- Python must be the latest LTS version (3.12.x — verify at implementation time)
- All Python code runs inside a virtual environment (`venv`)
- Vue.js must be on the latest stable version (3.x — verify at implementation time)
- All business logic resides in the backend (DRF) — the frontend is a presentation layer only
- Testing uses Django's default test framework (`django.test`) — no additional test tools
- Database managed entirely through Django ORM migrations and bootstrapping
- PostgreSQL runs in Docker
- API is public — no authentication required for MVP
- Project is named `config-service`; both DRF backend and Vue.js frontend reside inside `./config-service/`

---

## 1. Dependencies

### 1.1 Backend (Python / pip)

| Package | Version | Justification |
|---------|---------|---------------|
| `Python` | 3.12.x (latest LTS) | Runtime — latest LTS version as specified |
| `Django` | 5.1.x | Web framework — required foundation for Django REST Framework |
| `djangorestframework` | 3.15.x | REST API framework — explicitly required by application specs |
| `psycopg2-binary` | 2.9.x | PostgreSQL database adapter — required for Django to connect to the Postgres database |
| `django-cors-headers` | 4.x | CORS middleware — approved to handle cross-origin requests between Vue.js dev server and Django |

### 1.2 Frontend (Node.js / npm)

| Package | Version | Justification |
|---------|---------|---------------|
| `Node.js` | 22.x (LTS) | Runtime — required to develop and build the Vue.js application |
| `vue` | 3.5.x (latest stable) | Frontend SPA framework — explicitly required by application specs |
| `vue-router` | 4.x | Official Vue.js router — approved; required for SPA client-side navigation |
| `axios` | 1.x | HTTP client library — approved for making API calls to the backend |
| `vite` | 6.x | Build tool and dev server — approved; standard tooling for Vue 3 projects |
| `@vitejs/plugin-vue` | 5.x | Vite plugin — required for Vite to process Vue single-file components |

### 1.3 Infrastructure

| Tool | Version | Justification |
|------|---------|---------------|
| `Docker` / `Docker Compose` | latest | Run PostgreSQL in a container as approved |

### 1.4 Dependencies NOT Included

- `pinia` / `vuex` — state management; not needed for displaying a simple user list
- `TypeScript` — not specified in requirements
- `pytest` / `pytest-django` — Django's default test framework is sufficient
- `python-dotenv` / `django-environ` — not specified; database config hardcoded for MVP
- `gunicorn` / `uvicorn` — no production deployment requirements beyond Docker for Postgres

---

## 2. File/Folder Structure

```
config-service/
├── docker-compose.yml                 # PostgreSQL container definition
│
├── backend/
│   ├── manage.py                      # Django management CLI entry point
│   ├── requirements.txt               # Pinned Python dependencies
│   │
│   ├── config/                        # Django project configuration
│   │   ├── __init__.py
│   │   ├── settings.py                # Django settings (DB, CORS, installed apps, DRF config)
│   │   ├── urls.py                    # Root URL configuration — mounts api/ namespace
│   │   ├── wsgi.py                    # WSGI application entry point
│   │   └── asgi.py                    # ASGI application entry point
│   │
│   └── api/                           # DRF application — all API code and business logic
│       ├── __init__.py
│       ├── apps.py                    # Django app configuration
│       ├── models.py                  # User model definition
│       ├── serializers.py             # UserSerializer — validation and JSON representation
│       ├── views.py                   # UserViewSet — list users endpoint
│       ├── urls.py                    # API URL routing — DRF router registration
│       ├── admin.py                   # Django admin site registration for User model
│       ├── tests.py                   # Tests using django.test / DRF APITestCase
│       └── migrations/                # Django auto-generated database migration files
│           └── __init__.py
│
└── frontend/
    ├── package.json                   # Node.js dependencies and npm scripts
    ├── vite.config.js                 # Vite configuration — plugins
    ├── index.html                     # SPA entry HTML file (Vite entry point)
    │
    └── src/
        ├── main.js                    # Vue app initialization — creates app, mounts router
        ├── App.vue                    # Root Vue component — contains <router-view>
        │
        ├── router/
        │   └── index.js               # Vue Router — route definitions
        │
        ├── views/
        │   └── HomeView.vue           # Home page — fetches and displays user list
        │
        ├── components/
        │   └── UserList.vue           # Reusable component — renders a list of users
        │
        └── services/
            └── api.js                 # axios-based API client for backend calls
```

---

## 3. Architectural Patterns

### 3.1 Backend: Model → Serializer → ViewSet → Router

1. **User Model** (`api/models.py`) — defines `first_name`, `last_name`, `email` fields mapped to a PostgreSQL table via Django ORM
2. **UserSerializer** (`api/serializers.py`) — `ModelSerializer` that serializes/deserializes User instances to/from JSON
3. **UserViewSet** (`api/views.py`) — `ModelViewSet` providing full CRUD; the frontend uses the list endpoint (`GET /api/users/`)
4. **URL Routing** (`api/urls.py`) — DRF `DefaultRouter` registers `UserViewSet` at `users/`; mounted under `/api/` in `config/urls.py`

### 3.2 Database: Django ORM + PostgreSQL (Docker)

- PostgreSQL runs in Docker via `docker-compose.yml`
- Connection configured in `config/settings.py` under `DATABASES`
- Migration workflow: modify `models.py` → `makemigrations` → `migrate`
- Bootstrapping: `migrate` applies all migrations; `createsuperuser` creates admin; seed data via fixtures or Django admin

### 3.3 CORS: django-cors-headers

- `django-cors-headers` middleware handles cross-origin requests
- In development, `CORS_ALLOWED_ORIGINS` includes the Vite dev server origin (`http://localhost:5173`)
- No Vite proxy needed — the frontend calls the backend directly at `http://localhost:8000/api/`

### 3.4 Frontend: Component-Based SPA with axios Service Layer

- **Vue Router** manages client-side navigation
- **View components** (`views/`) are route-level pages that call the API service
- **Reusable components** (`components/`) receive data via props
- **API service** (`services/api.js`) wraps axios with a pre-configured base URL pointing to the Django backend

### 3.5 Frontend ↔ Backend Communication

- Frontend (port 5173) makes HTTP requests via axios to backend (port 8000)
- `django-cors-headers` allows cross-origin requests from the frontend origin
- All endpoints prefixed with `/api/` — e.g. `GET http://localhost:8000/api/users/`
- Data flow: `HomeView.vue` → `api.js` (axios) → DRF `UserViewSet` → `UserSerializer` → `User` model/ORM → PostgreSQL

### 3.6 Testing Strategy

- Django's `django.test.TestCase` and DRF's `APITestCase`
- Tests in `backend/api/tests.py`
- Test: model creation, serializer validation, API list endpoint (status 200, correct data)
- Run: `cd config-service/backend && python manage.py test`

---

## 4. Implementation Tasks

### Task 1: PostgreSQL Docker Setup

**Files:**
- Create: `config-service/docker-compose.yml`

**Produces:**
- A running PostgreSQL instance on `localhost:5432` with database `config_service_db`, user `postgres`, password `postgres`

- [ ] **Step 1: Create `docker-compose.yml`**

Create file `config-service/docker-compose.yml`:

```yaml
version: "3.9"

services:
  db:
    image: postgres:16
    restart: unless-stopped
    environment:
      POSTGRES_DB: config_service_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

- [ ] **Step 2: Start PostgreSQL**

Run: `cd config-service && docker compose up -d`

Expected: PostgreSQL container starts and is accessible on `localhost:5432`.

- [ ] **Step 3: Verify PostgreSQL is running**

Run: `docker compose ps`

Expected: `db` service shows status `Up`.

- [ ] **Step 4: Commit**

```bash
cd config-service && git add docker-compose.yml
git commit -m "feat: add Docker Compose for PostgreSQL"
```

---

### Task 2: Backend Project Scaffolding

**Files:**
- Create: `config-service/backend/requirements.txt`
- Create: `config-service/backend/config/` (generated)
- Create: `config-service/backend/api/` (generated)

**Consumes:** PostgreSQL from Task 1 (running on `localhost:5432`)

**Produces:**
- A Django project (`config`) with DRF and `django-cors-headers` installed
- An empty `api` app registered in `INSTALLED_APPS`
- PostgreSQL connection configured and initial migrations applied

- [ ] **Step 1: Create virtual environment**

Run:
```bash
cd config-service && python3 -m venv backend/venv
```

- [ ] **Step 2: Create `requirements.txt`**

Create file `config-service/backend/requirements.txt`:

```
Django==5.1.9
djangorestframework==3.15.2
psycopg2-binary==2.9.10
django-cors-headers==4.7.0
```

*(Verify latest patch versions at implementation time and update accordingly)*

- [ ] **Step 3: Install dependencies**

Run:
```bash
cd config-service && source backend/venv/bin/activate && pip install -r backend/requirements.txt
```

Expected: All packages install without errors.

- [ ] **Step 4: Scaffold the Django project**

Run:
```bash
cd config-service/backend && source venv/bin/activate && django-admin startproject config .
```

Expected: `manage.py` and `config/` directory are created in `config-service/backend/`.

- [ ] **Step 5: Create the API app**

Run:
```bash
cd config-service/backend && source venv/bin/activate && python manage.py startapp api
```

Expected: `api/` directory is created with standard Django app files.

- [ ] **Step 6: Configure `settings.py`**

Edit `config-service/backend/config/settings.py`:

Add to `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    # Local
    "api",
]
```

Add `corsheaders` middleware — it must be placed **before** `CommonMiddleware`:
```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",          # <-- add here
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

Add CORS configuration at the bottom:
```python
# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]
```

Replace the `DATABASES` section:
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "config_service_db",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
```

- [ ] **Step 7: Apply initial migrations**

Run:
```bash
cd config-service/backend && source venv/bin/activate && python manage.py migrate
```

Expected: All Django built-in migrations apply successfully.

- [ ] **Step 8: Verify the server starts**

Run:
```bash
cd config-service/backend && source venv/bin/activate && python manage.py runserver
```

Expected: Server starts at `http://127.0.0.1:8000/` without errors.

- [ ] **Step 9: Commit**

```bash
cd config-service && git add backend/
git commit -m "feat: scaffold Django backend with DRF, django-cors-headers, and PostgreSQL"
```

---

### Task 3: User Model and API Endpoints

**Files:**
- Modify: `config-service/backend/api/models.py`
- Create: `config-service/backend/api/serializers.py` (file exists but is empty)
- Modify: `config-service/backend/api/views.py`
- Create: `config-service/backend/api/urls.py`
- Modify: `config-service/backend/config/urls.py`
- Modify: `config-service/backend/api/admin.py`
- Modify: `config-service/backend/api/tests.py`

**Consumes:** Scaffolded Django project from Task 2

**Produces:**
- `User` model with `first_name`, `last_name`, `email` fields
- `GET /api/users/` returns a JSON list of all users
- Full CRUD via `ModelViewSet` at `/api/users/` and `/api/users/{id}/`
- Tests verifying list, create, retrieve, update, delete

- [ ] **Step 1: Write the failing tests**

Edit `config-service/backend/api/tests.py`:

```python
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from api.models import User


class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create(
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
        )
        self.assertEqual(user.first_name, "Alice")
        self.assertEqual(user.last_name, "Smith")
        self.assertEqual(user.email, "alice@example.com")

    def test_str_representation(self):
        user = User.objects.create(
            first_name="Bob",
            last_name="Jones",
            email="bob@example.com",
        )
        self.assertEqual(str(user), "Bob Jones")


class UserAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        self.user = User.objects.create(**self.user_data)

    def test_list_users(self):
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["first_name"], "Alice")
        self.assertEqual(response.data[0]["last_name"], "Smith")
        self.assertEqual(response.data[0]["email"], "alice@example.com")

    def test_create_user(self):
        new_user = {
            "first_name": "Charlie",
            "last_name": "Brown",
            "email": "charlie@example.com",
        }
        response = self.client.post("/api/users/", new_user, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(response.data["first_name"], "Charlie")

    def test_retrieve_user(self):
        response = self.client.get(f"/api/users/{self.user.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "alice@example.com")

    def test_update_user(self):
        updated = {"first_name": "Alicia", "last_name": "Smith", "email": "alice@example.com"}
        response = self.client.put(
            f"/api/users/{self.user.id}/", updated, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Alicia")

    def test_delete_user(self):
        response = self.client.delete(f"/api/users/{self.user.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), 0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd config-service/backend && source venv/bin/activate && python manage.py test
```

Expected: FAIL — `ImportError: cannot import name 'User' from 'api.models'`

- [ ] **Step 3: Define the User model**

Edit `config-service/backend/api/models.py`:

```python
from django.db import models


class User(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
```

- [ ] **Step 4: Generate and apply migrations**

Run:
```bash
cd config-service/backend && source venv/bin/activate && python manage.py makemigrations api
python manage.py migrate
```

Expected: Migration `0001_initial.py` is created and applied.

- [ ] **Step 5: Create the serializer**

Edit `config-service/backend/api/serializers.py`:

```python
from rest_framework import serializers

from api.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
```

- [ ] **Step 6: Create the viewset**

Edit `config-service/backend/api/views.py`:

```python
from rest_framework import viewsets

from api.models import User
from api.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
```

- [ ] **Step 7: Create API URL routing**

Create `config-service/backend/api/urls.py`:

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
```

- [ ] **Step 8: Mount API URLs in root config**

Edit `config-service/backend/config/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
]
```

- [ ] **Step 9: Register model in admin**

Edit `config-service/backend/api/admin.py`:

```python
from django.contrib import admin

from api.models import User

admin.site.register(User)
```

- [ ] **Step 10: Run tests to verify they pass**

Run:
```bash
cd config-service/backend && source venv/bin/activate && python manage.py test
```

Expected: All 7 tests pass (2 model tests + 5 API tests).

- [ ] **Step 11: Verify endpoints manually**

Run:
```bash
cd config-service/backend && source venv/bin/activate && python manage.py runserver
```

Then in another terminal:
```bash
curl http://localhost:8000/api/users/
```

Expected: `[]` (empty list, 200 OK)

```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Alice","last_name":"Smith","email":"alice@example.com"}'
```

Expected: 201 Created with user JSON.

```bash
curl http://localhost:8000/api/users/
```

Expected: JSON array with one user.

- [ ] **Step 12: Commit**

```bash
cd config-service && git add backend/
git commit -m "feat: add User model, serializer, viewset, and API tests"
```

---

### Task 4: Frontend Project Scaffolding

**Files:**
- Create: `config-service/frontend/` (generated by `npm create vue@latest`)

**Produces:**
- A Vue.js 3 project with Vue Router and Vite at `config-service/frontend/`
- Dev server running at `http://localhost:5173`

- [ ] **Step 1: Scaffold the Vue.js project**

Run:
```bash
cd config-service && npm create vue@latest frontend
```

When prompted, select:
- Add TypeScript? — **No**
- Add JSX Support? — **No**
- Add Vue Router? — **Yes**
- Add Pinia? — **No**
- Add Vitest? — **No**
- Add an End-to-End Testing Solution? — **No**
- Add ESLint? — **No**
- Add Prettier? — **No**

- [ ] **Step 2: Install dependencies**

Run:
```bash
cd config-service/frontend && npm install
```

Expected: Dependencies install without errors.

- [ ] **Step 3: Install axios**

Run:
```bash
cd config-service/frontend && npm install axios
```

Expected: axios is added to `package.json` dependencies.

- [ ] **Step 4: Verify the dev server starts**

Run:
```bash
cd config-service/frontend && npm run dev
```

Expected: Vite dev server starts at `http://localhost:5173/`.

- [ ] **Step 5: Commit**

```bash
cd config-service && git add frontend/
git commit -m "feat: scaffold Vue.js frontend with Vue Router and axios"
```

---

### Task 5: Frontend API Service and User List

**Files:**
- Create: `config-service/frontend/src/services/api.js`
- Create: `config-service/frontend/src/components/UserList.vue`
- Modify: `config-service/frontend/src/views/HomeView.vue`
- Modify: `config-service/frontend/src/router/index.js`
- Modify: `config-service/frontend/src/App.vue`

**Consumes:** Vue.js project from Task 4, API endpoints from Task 3

**Produces:**
- axios-based API client configured to call `http://localhost:8000/api/`
- `UserList.vue` component that renders a list of users
- `HomeView.vue` that fetches users on mount and passes them to `UserList`
- Working SPA with route at `/` displaying the user list

- [ ] **Step 1: Create the API service**

Create `config-service/frontend/src/services/api.js`:

```javascript
import axios from 'axios'

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/',
  headers: {
    'Content-Type': 'application/json',
  },
})

export default {
  getUsers() {
    return apiClient.get('users/')
  },
}
```

- [ ] **Step 2: Create the UserList component**

Create `config-service/frontend/src/components/UserList.vue`:

```vue
<template>
  <div>
    <h2>Users</h2>
    <p v-if="users.length === 0">No users found.</p>
    <ul v-else>
      <li v-for="user in users" :key="user.id">
        {{ user.first_name }} {{ user.last_name }} — {{ user.email }}
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  name: 'UserList',
  props: {
    users: {
      type: Array,
      required: true,
    },
  },
}
</script>
```

- [ ] **Step 3: Update HomeView to fetch and display users**

Replace the content of `config-service/frontend/src/views/HomeView.vue`:

```vue
<template>
  <div>
    <h1>Config Service</h1>
    <p v-if="loading">Loading users...</p>
    <p v-else-if="error">Error loading users: {{ error }}</p>
    <UserList v-else :users="users" />
  </div>
</template>

<script>
import api from '../services/api.js'
import UserList from '../components/UserList.vue'

export default {
  name: 'HomeView',
  components: {
    UserList,
  },
  data() {
    return {
      users: [],
      loading: true,
      error: null,
    }
  },
  async mounted() {
    try {
      const response = await api.getUsers()
      this.users = response.data
    } catch (err) {
      this.error = err.message
    } finally {
      this.loading = false
    }
  },
}
</script>
```

- [ ] **Step 4: Update the router**

Replace the content of `config-service/frontend/src/router/index.js`:

```javascript
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
  ],
})

export default router
```

- [ ] **Step 5: Simplify App.vue**

Replace the content of `config-service/frontend/src/App.vue`:

```vue
<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App',
}
</script>
```

- [ ] **Step 6: Verify the full data flow**

Start all services in separate terminals:

Terminal 1 — PostgreSQL (if not already running):
```bash
cd config-service && docker compose up -d
```

Terminal 2 — Backend:
```bash
cd config-service/backend && source venv/bin/activate && python manage.py runserver
```

Terminal 3 — Frontend:
```bash
cd config-service/frontend && npm run dev
```

Open `http://localhost:5173/` in the browser.

Expected: The page loads and shows "No users found." (empty database).

Add a user via curl:
```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Alice","last_name":"Smith","email":"alice@example.com"}'
```

Refresh the browser page.

Expected: The page shows "Alice Smith — alice@example.com" in the list.

- [ ] **Step 7: Run backend tests**

Run:
```bash
cd config-service/backend && source venv/bin/activate && python manage.py test
```

Expected: All 7 tests pass.

- [ ] **Step 8: Commit**

```bash
cd config-service && git add frontend/
git commit -m "feat: add API service, UserList component, and HomeView integration"
```

---

## 5. Development Workflow Summary

1. **Start PostgreSQL** — `cd config-service && docker compose up -d`
2. **Start the backend** — `cd config-service/backend && source venv/bin/activate && python manage.py runserver`
3. **Start the frontend** — `cd config-service/frontend && npm run dev`
4. **Access the app** — open `http://localhost:5173` in the browser
5. **Run tests** — `cd config-service/backend && source venv/bin/activate && python manage.py test`
6. **Stop PostgreSQL** — `cd config-service && docker compose down`