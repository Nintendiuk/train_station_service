# 🚂 TrainStation Service API

A production-grade, high-load REST API for managing train stations, routes,
journeys, crew, and ticket bookings — built with Django REST Framework.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Framework | Django 4.2 + Django REST Framework 3.15 |
| Authentication | SimpleJWT (Bearer tokens) |
| Documentation | drf-spectacular (OpenAPI 3 / Swagger) |
| Database | PostgreSQL 15 |
| Filtering | django-filter |
| Containerization | Docker + Docker Compose |
| Testing | pytest + pytest-django |
| Linting | flake8 (max-line-length = 79) |

---

## Architecture Overview

```
train_station_service/   ← Django project config
train_station/           ← Main application (models, views, serializers)
tests/                   ← All pytest test suites
```

### Domain Model (class diagram)

```
Station ──< Route >── Station
             │
             ▼
           Journey ──< Ticket >── Order
             │
          TrainType
             │
            Train
             │
            Crew
```

---

## Quick Start (Docker)

### 1. Clone & configure environment

```bash
git clone https://github.com/your-org/train-station-service.git
cd train-station-service
cp .env.example .env
# Edit .env with your secrets
```

### 2. Build and run

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.

### 3. Create a superuser (optional)

```bash
docker compose exec web python manage.py createsuperuser
```

---

## Running Tests

```bash
# Inside the container
docker compose exec web python -m pytest tests/ -v

# Locally (requires SQLite test settings)
python -m pytest tests/ -v
```

---

## Linting

```bash
flake8 .
```

Config lives in `.flake8` (max-line-length = 79).

---

## API Documentation

Once the server is running, visit:

| URL | Description |
|---|---|
| `GET /api/docs/swagger/` | Swagger UI (interactive) |
| `GET /api/docs/redoc/` | ReDoc UI |
| `GET /api/schema/` | Raw OpenAPI 3 JSON schema |

---

## Authentication

The API uses **JWT Bearer tokens** (RFC 7519).

### Obtain tokens

```http
POST /api/token/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

Response:

```json
{
  "access": "<access_token>",
  "refresh": "<refresh_token>"
}
```

### Use the access token

```http
GET /api/stations/
Authorization: Bearer <access_token>
```

### Refresh the access token

```http
POST /api/token/refresh/
Content-Type: application/json

{ "refresh": "<refresh_token>" }
```

---

## Permission Model

| Role | Permissions |
|---|---|
| Unauthenticated | ❌ Denied (401) |
| Authenticated user | ✅ Read Journeys, book tickets |
| Staff / Admin | ✅ Full CRUD on Stations, Trains, Routes, Crew |

---

## API Endpoints (implemented progressively)

### Stage 2 — Stations & Trains
| Method | URL | Description |
|---|---|---|
| GET | `/api/stations/` | List stations |
| POST | `/api/stations/` | Create station (staff only) |
| GET | `/api/train-types/` | List train types |
| GET | `/api/trains/` | List trains |

### Stage 3 — Journeys & Crew
| Method | URL | Description |
|---|---|---|
| GET | `/api/journeys/` | List journeys (with filters) |
| GET | `/api/crew/` | List crew members |

### Stage 4 — Booking
| Method | URL | Description |
|---|---|---|
| GET | `/api/orders/` | My orders |
| POST | `/api/orders/` | Create order with tickets |

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | (insecure default) | Django secret key |
| `DJANGO_DEBUG` | `True` | Debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost 127.0.0.1` | Allowed hosts |
| `POSTGRES_DB` | `train_station_db` | Database name |
| `POSTGRES_USER` | `train_user` | DB username |
| `POSTGRES_PASSWORD` | `train_password` | DB password |
| `POSTGRES_HOST` | `db` | DB host (Docker service name) |
| `POSTGRES_PORT` | `5432` | DB port |

---

## Development Stages

- [x] **Stage 1** — Infrastructure (Docker, PostgreSQL, JWT, Swagger, flake8)
- [ ] **Stage 2** — Data Models (Station, TrainType, Train, Route)
- [ ] **Stage 3** — Journeys & Crew (filtering, search)
- [ ] **Stage 4** — Booking System (Orders, Tickets, transactions)
- [ ] **Stage 5** — Full API & Documentation polish

---

## License

MIT
