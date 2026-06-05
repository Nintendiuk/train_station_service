# 🚂 TrainStation Service API

A production-ready REST API for managing railway stations, trains, routes,
journeys, orders and tickets.

**Built with:** Django 4.2 · Django REST Framework · SimpleJWT · drf-spectacular · Docker

---

## 📋 Table of Contents

- [Features](#-features)
- [DB Structure](#-db-structure)
- [Tech Stack](#-tech-stack)
- [Quick Start with Docker](#-quick-start-with-docker)
- [Local Setup (without Docker)](#-local-setup-without-docker)
- [Running Tests](#-running-tests)
- [Getting Access](#-getting-access)
- [API Endpoints](#-api-endpoints)
- [Browsable API Screenshots](#-browsable-api-screenshots)

---

## ✨ Features

- 🔐 **JWT Authentication** — email-based login, no username required
- 🛡 **Role-based permissions** — admins manage data, users browse and order
- 🎫 **Atomic order creation** — all tickets saved or none (transaction-safe)
- 💺 **Seat validation** — cargo/seat numbers validated against real train capacity
- 📊 **Live seat availability** — `tickets_available` per journey, optimised with DB annotation (no N+1)
- 🗺 **Journey filtering** — filter by source station, destination, or departure date
- 🖼 **Train image upload** — dedicated upload endpoint per train
- 📖 **OpenAPI 3.0 docs** — Swagger UI + ReDoc auto-generated
- 🐳 **Docker ready** — one command to run the full stack
- ✅ **82 tests** — full pytest coverage across models, serializers, permissions and views

---

## 🗄 DB Structure

```
Station ──────────────────────────────────────────┐
  id, name, latitude, longitude                   │ source / destination
                                                  ▼
Route ────────────────────────────────────── Journey ──── Train
  id, source, destination, distance       id, route,       id, name, cargo_num,
                                          train,           places_in_cargo,
                                          departure_time,  train_type, image
Crew ◄──── M2M ────────────────────────── arrival_time
  id, first_name, last_name                    │
                                               │ 1:N
                                            Ticket
                                          id, cargo, seat,
                                          journey, order
                                               │ N:1
                                            Order
                                          id, created_at, user
```

> 📌 Full diagram: see `/docs/db_diagram.png` in the repository.

### Model relationships

| Model | Relations |
|---|---|
| `Station` | used as `source` and `destination` in `Route` |
| `Route` | ForeignKey → `Station` × 2 |
| `TrainType` | ForeignKey ← `Train` |
| `Train` | ForeignKey → `TrainType`; has `capacity` property |
| `Crew` | ManyToMany ↔ `Journey` |
| `Journey` | ForeignKey → `Route`, `Train`; M2M → `Crew` |
| `Order` | ForeignKey → `User` |
| `Ticket` | ForeignKey → `Journey`, `Order`; unique on `(journey, cargo, seat)` |

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 4.2, Django REST Framework 3.14 |
| Auth | djangorestframework-simplejwt 5.3 |
| Docs | drf-spectacular 0.27 (OpenAPI 3.0) |
| Filtering | django-filter 23 |
| Database | PostgreSQL 15 (production), SQLite :memory: (tests) |
| Images | Pillow 10 |
| Server | Gunicorn 21 |
| Containers | Docker + Docker Compose |
| Testing | pytest 7, pytest-django 4.7 |
| Linting | flake8 6.1 (max-line-length 79) |

---

## 🐳 Quick Start with Docker

> **Prerequisites:** Docker and Docker Compose installed.

```bash
# 1. Clone the repository
git clone https://github.com/your-username/train-station-service.git
cd train-station-service

# 2. Build and start all services (web + PostgreSQL)
docker-compose up --build

# 3. In a second terminal — create a superuser
docker-compose exec web python manage.py createsuperuser

# 4. Open the API
open http://localhost:8000/api/
# Swagger UI docs:
open http://localhost:8000/api/docs/
```

The API will be available at **http://localhost:8000/api/**

---

## 💻 Local Setup (without Docker)

> **Prerequisites:** Python 3.10+, pip

```bash
# 1. Clone the repository
git clone https://github.com/your-username/train-station-service.git
cd train-station-service

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply migrations
python manage.py migrate

# 5. Create a superuser (admin access)
python manage.py createsuperuser

# 6. Run the development server
python manage.py runserver
```

The API will be available at **http://127.0.0.1:8000/api/**

---

## ✅ Running Tests

The test suite uses SQLite `:memory:` — no database server needed.

```bash
# Run all 82 tests
pytest

# With verbose output
pytest -v

# Run a specific file
pytest tests/test_models.py -v
pytest tests/test_views.py -v

# Stop on first failure
pytest -x

# Show slowest tests
pytest --durations=5
```

Expected result: **82 passed** in under 2 seconds.

---

## 🔑 Getting Access

### Step 1 — Register a user

```http
POST /api/users/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "yourpassword"
}
```

### Step 2 — Obtain JWT tokens

```http
POST /api/token/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "yourpassword"
}
```

Response:

```json
{
  "access": "<access_token>",
  "refresh": "<refresh_token>"
}
```

### Step 3 — Use the API

Add the access token to every request header:

```http
GET /api/journeys/
Authorization: Bearer <access_token>
```

### Step 4 — Refresh the token (when expired)

```http
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "<refresh_token>"
}
```

> **Access token lifetime:** 60 minutes  
> **Refresh token lifetime:** 7 days

### Admin access

To perform write operations (create/update/delete), your user account must have `is_staff = True`.  
Create an admin via:

```bash
python manage.py createsuperuser
# or via Docker:
docker-compose exec web python manage.py createsuperuser
```

---

## 📡 API Endpoints

### 📚 Documentation

| URL | Description |
|---|---|
| `GET /api/docs/` | Swagger UI (interactive) |
| `GET /api/redoc/` | ReDoc |
| `GET /api/schema/` | OpenAPI JSON schema |

### 🔐 Authentication

| Method | URL | Description |
|---|---|---|
| `POST` | `/api/token/` | Obtain access + refresh tokens |
| `POST` | `/api/token/refresh/` | Refresh access token |
| `POST` | `/api/token/verify/` | Verify token validity |

### 👤 Users

| Method | URL | Auth | Description |
|---|---|---|---|
| `POST` | `/api/users/` | ❌ open | Register new user |
| `GET` | `/api/users/{id}/` | ✅ user | Get own profile |
| `PUT/PATCH` | `/api/users/{id}/` | ✅ user | Update own profile |

### 🚉 Stations

| Method | URL | Auth | Description |
|---|---|---|---|
| `GET` | `/api/stations/` | ✅ user | List all stations |
| `POST` | `/api/stations/` | 👑 admin | Create a station |
| `GET` | `/api/stations/{id}/` | ✅ user | Retrieve a station |
| `PUT/PATCH` | `/api/stations/{id}/` | 👑 admin | Update a station |
| `DELETE` | `/api/stations/{id}/` | 👑 admin | Delete a station |

### 🚆 Train Types

| Method | URL | Auth | Description |
|---|---|---|---|
| `GET` | `/api/train-types/` | ✅ user | List train types |
| `POST` | `/api/train-types/` | 👑 admin | Create a train type |
| `GET/PUT/PATCH/DELETE` | `/api/train-types/{id}/` | 👑 admin write | CRUD |

### 🚂 Trains

| Method | URL | Auth | Description |
|---|---|---|---|
| `GET` | `/api/trains/` | ✅ user | List trains (with `capacity`) |
| `POST` | `/api/trains/` | 👑 admin | Create a train |
| `GET` | `/api/trains/{id}/` | ✅ user | Detail (nested train type) |
| `PUT/PATCH` | `/api/trains/{id}/` | 👑 admin | Update a train |
| `DELETE` | `/api/trains/{id}/` | 👑 admin | Delete a train |
| `POST` | `/api/trains/{id}/upload-image/` | 👑 admin | Upload train image |

### 👥 Crew

| Method | URL | Auth | Description |
|---|---|---|---|
| `GET` | `/api/crew/` | ✅ user | List crew members |
| `POST` | `/api/crew/` | 👑 admin | Create crew member |
| `GET/PUT/PATCH/DELETE` | `/api/crew/{id}/` | 👑 admin write | CRUD |

### 🗺 Routes

| Method | URL | Auth | Description |
|---|---|---|---|
| `GET` | `/api/routes/` | ✅ user | List routes |
| `POST` | `/api/routes/` | 👑 admin | Create a route |
| `GET` | `/api/routes/{id}/` | ✅ user | Detail (nested stations) |
| `PUT/PATCH` | `/api/routes/{id}/` | 👑 admin | Update a route |
| `DELETE` | `/api/routes/{id}/` | 👑 admin | Delete a route |

### 🗓 Journeys

| Method | URL | Auth | Description |
|---|---|---|---|
| `GET` | `/api/journeys/` | ✅ user | List journeys with `tickets_available` |
| `POST` | `/api/journeys/` | 👑 admin | Create a journey |
| `GET` | `/api/journeys/{id}/` | ✅ user | Detail with `taken_places` list |
| `PUT/PATCH` | `/api/journeys/{id}/` | 👑 admin | Update a journey |
| `DELETE` | `/api/journeys/{id}/` | 👑 admin | Delete a journey |

#### Journey filters

```
GET /api/journeys/?source=Kyiv
GET /api/journeys/?destination=Lviv
GET /api/journeys/?date=2025-06-01
GET /api/journeys/?source=Kyiv&destination=Lviv&date=2025-06-01
```

### 🎫 Orders

| Method | URL | Auth | Description |
|---|---|---|---|
| `GET` | `/api/orders/` | ✅ user | List **own** orders only |
| `POST` | `/api/orders/` | ✅ user | Create order with tickets |
| `GET` | `/api/orders/{id}/` | ✅ user | Detail with nested tickets |

#### Create order example

```http
POST /api/orders/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "tickets": [
    {"cargo": 1, "seat": 5, "journey": 3},
    {"cargo": 1, "seat": 6, "journey": 3}
  ]
}
```

> Tickets are validated against the train's capacity. All tickets are created atomically — if any ticket is invalid, the entire order is rejected.

---

## 🔒 Permissions Summary

| Role | Read | Write |
|---|---|---|
| 🔴 Anonymous | ❌ 401 | ❌ 401 |
| 🟡 Authenticated user | ✅ | ❌ 403 |
| 🟢 Admin / Staff | ✅ | ✅ |

Orders are additionally scoped: **users see only their own orders**. Admins see all.

---

## 🖼 Browsable API Screenshots

> Add your screenshots here after running the project locally.

| Page | URL |
|---|---|
| API Root | `http://127.0.0.1:8000/api/` |
| Journeys list | `http://127.0.0.1:8000/api/journeys/` |
| Journey detail | `http://127.0.0.1:8000/api/journeys/1/` |
| Swagger UI | `http://127.0.0.1:8000/api/docs/` |
| Orders | `http://127.0.0.1:8000/api/orders/` |

---

## 📝 Custom Logic Highlights

- **`Train.capacity`** — computed property: `cargo_num × places_in_cargo`
- **`tickets_available`** on Journey list — uses DB `annotate(Count("tickets"))` to avoid N+1 queries
- **`taken_places`** on Journey detail — returns list of `{cargo, seat}` for booked seats
- **Seat validation** — `Ticket.validate_seat()` checks cargo and seat numbers against the train's actual capacity at both model and serializer level
- **Atomic orders** — `OrderCreateSerializer.create()` is wrapped in `@transaction.atomic`
- **Custom 401** — `CustomTokenObtainPairView` returns `401 Unauthorized` (not `400`) on bad credentials

---

## 🌿 Git Commit Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(infra): add Dockerfile, docker-compose, flake8, pytest config
feat(models): add all domain models with validation
feat(serializers): add DRF serializers with nested structures
feat(auth): add SimpleJWT and custom permissions
feat(views): add ModelViewSets with filtering and image upload
feat(docs): configure drf-spectacular and finalize README
```
