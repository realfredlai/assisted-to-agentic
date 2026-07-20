# Config Service

A full stack application consisting of a Django REST Framework (DRF) backend API and a Vue.js Single Page Application (SPA) frontend, backed by PostgreSQL.

## Tech Stack

- **Backend:** Python 3.14, Django 5.1, Django REST Framework 3.15, django-cors-headers 4.7
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
│   └── api/                    # DRF application
│       ├── models.py           # User model
│       ├── serializers.py      # UserSerializer
│       ├── views.py            # UserViewSet (CRUD)
│       ├── urls.py             # API URL routing (/api/users/)
│       ├── tests.py            # 7 tests (model + API)
│       └── migrations/         # Database migrations
└── frontend/
    ├── package.json            # Node dependencies
    ├── vite.config.js          # Vite build config
    ├── index.html              # SPA entry point
    └── src/
        ├── main.js             # Vue app bootstrap
        ├── App.vue             # Root component
        ├── router/index.js     # Vue Router config
        ├── views/HomeView.vue  # Home page — fetches and displays users
        ├── components/UserList.vue  # User list component
        └── services/api.js     # axios API client
```

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

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/users/` | List all users |
| `POST` | `/api/users/` | Create a new user |
| `GET` | `/api/users/{id}/` | Retrieve a user |
| `PUT` | `/api/users/{id}/` | Update a user |
| `DELETE` | `/api/users/{id}/` | Delete a user |

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

## Running Tests

```bash
cd config-service/backend
source venv/bin/activate
python manage.py test
```

Expected: 7 tests pass (2 model tests + 5 API tests).

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