# Users API — Auth & User Management Service

A FastAPI-based REST API providing user registration, JWT authentication,
email verification, role-based access control, and automatic cleanup of
unverified accounts.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI (async) |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL (production) / SQLite (development) |
| Migrations | Alembic |
| Auth | JWT (access + refresh tokens via `python-jose`) |
| Password Hashing | `passlib` + `bcrypt` |
| Task Queue | Celery + Redis |
| Containerisation | Docker & Docker Compose |

## Quick Start (local, SQLite)

```bash
# 1. Create & activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run database migrations
alembic upgrade head

# 4. Start the development server
uvicorn main:app --reload
```

The API is now available at **http://127.0.0.1:8000**.
Interactive docs (Swagger UI) are at **http://127.0.0.1:8000/docs**.

## Quick Start (Docker Compose, PostgreSQL)

```bash
docker compose up --build
```

This starts PostgreSQL, Redis, the API server, a Celery worker, and Celery
Beat. The API is available at **http://localhost:8000**.

## API Endpoints

### Authentication (`/auth`)

| Method | Path | Summary | Auth |
|--------|------|---------|------|
| POST | `/auth/signup` | Register a new user | — |
| POST | `/auth/login` | Authenticate & get tokens | — |
| POST | `/auth/refresh` | Refresh access token | — |
| POST | `/auth/verify` | Verify email code | — |

### Users

| Method | Path | Summary | Auth |
|--------|------|---------|------|
| GET | `/me` | Get current user profile | Bearer |
| GET | `/users` | List all users | Admin |
| GET | `/users/{id}` | Get user by ID | Admin |
| PATCH | `/users/{id}` | Partially update user | Bearer (own) / Admin |
| DELETE | `/users/{id}` | Delete user | Admin |

### Utility

| Method | Path | Summary |
|--------|------|---------|
| GET | `/health` | Health check |

## Roles

| Role | Capabilities |
|------|-------------|
| `user` | Access own profile, update own data |
| `admin` | Full CRUD on all users, role changes |

## Verification Flow

1. User registers via `POST /auth/signup`.
2. A 6-digit verification code is generated and **logged to the console** (dev mode).
3. User submits the code via `POST /auth/verify`.
4. On success the account status changes to **verified**.

> **Production note:** replace the console logger in
> `services/verification_service.py` with a real email/SMS provider
> (e.g. SendGrid, SES, Twilio) dispatched via a Celery task.

## Automatic Cleanup of Unverified Users

Users who have **not verified** their account within **2 days** are
automatically deleted by a Celery Beat scheduled task.

| Setting | Default | Description |
|---------|---------|-------------|
| `UNVERIFIED_USER_TTL_DAYS` | `2` | Days before an unverified account is purged |

The cleanup task (`tasks.cleanup_unverified_users`) runs daily at 03:00 UTC
via Celery Beat. To run it manually:

```bash
celery -A tasks.celery_app call tasks.cleanup_unverified_users
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | *(required)* | JWT signing secret |
| `DATABASE_URL` | `sqlite+aiosqlite:///./dev.db` | Async database URL |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `VERIFICATION_CODE_EXPIRE_MINUTES` | `30` | Verification code lifetime |
| `UNVERIFIED_USER_TTL_DAYS` | `2` | Unverified user cleanup threshold |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection |
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | Celery broker |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/0` | Celery result backend |

## Project Structure

```
users_api/
├── main.py                  # FastAPI application entry point
├── tasks.py                 # Celery app & periodic tasks
├── alembic/                 # Database migrations
├── api/
│   ├── deps.py              # Dependency injection (auth, services)
│   └── routers/
│       ├── auth.py          # /auth/* endpoints
│       └── users.py         # /me, /users/* endpoints
├── core/
│   ├── config.py            # Settings (pydantic-settings)
│   ├── exceptions.py        # Domain-level exceptions
│   ├── logging.py           # Logging configuration
│   └── security.py          # JWT & password utilities
├── db/
│   ├── base.py              # SQLAlchemy declarative base
│   └── session.py           # Async engine & session factory
├── models/
│   └── user.py              # User ORM model + UserRole enum
├── repositories/
│   └── user_repository.py   # Data access layer
├── schemas/
│   ├── auth.py              # Auth request/response schemas
│   └── user.py              # User request/response schemas
├── services/
│   ├── auth_service.py      # Registration, login, token refresh
│   ├── user_service.py      # User CRUD business logic
│   └── verification_service.py  # Code generation & validation
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env
```

## License

This project is provided as-is for educational purposes.
