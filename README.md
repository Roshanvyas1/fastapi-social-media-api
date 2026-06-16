**Live API:** https://fastapi-social-media-api-yom4.onrender.com/docs

# FastAPI Social Media API

A production-style backend API built with FastAPI and Python 3.12, demonstrating async architecture, JWT security, containerization, and automated CI/CD — structured the way a real engineering team would build it.

---

## What This Project Demonstrates

**Fully Async Stack**  
Every layer — database engine, session, route handlers, and tests — uses Python's `async/await`. Built on SQLAlchemy 2.0's async interface with psycopg v3, not the sync wrappers most tutorials use.

**JWT Authentication with Timing Attack Mitigation**  
Login runs a dummy `verify_password` call even when the user doesn't exist, equalizing response time between "wrong email" and "wrong password." This prevents user enumeration via timing — a real security concern most implementations miss.

**Ownership-Enforced CRUD**  
Posts are tied to their creator via a foreign key. Update and delete operations verify ownership at the application layer before touching the database, returning `403 Forbidden` (not `404`) to avoid leaking resource existence.

**Partial Updates via PATCH**  
Update endpoint uses `PATCH` with `model_dump(exclude_unset=True)` — only fields explicitly provided in the request are updated. Clients aren't required to send the full object.

**Vote System with SQL Aggregation**  
Posts are returned with their vote counts using `outerjoin` + `func.count` aggregation in a single query. The single-post endpoint uses a CTE for the same. No N+1 queries.

**Rate Limiting**  
`/login` and `/users/` (register) are protected with per-IP rate limiting via slowapi, returning `429 Too Many Requests` after the threshold is exceeded. Prevents brute force attacks on public endpoints.

**Isolated Async Test Suite**  
Tests use `httpx.AsyncClient` with FastAPI's `ASGITransport` — requests never touch a real network. The `get_db` dependency is overridden per-test with a dedicated test database that is created and dropped around each test, guaranteeing full isolation.

**Docker with Proper Startup Sequencing**  
The FastAPI container waits for a `pg_isready` health check before starting — not just a `depends_on: db` which doesn't guarantee readiness. On startup, `alembic upgrade head` runs automatically before the server starts.

**CI/CD Pipeline**  
GitHub Actions runs three independent jobs on every push: Ruff linter, `pip-audit` for dependency CVEs, and the full test suite against a live Postgres service. Merges to `main` build and push a tagged Docker image to GHCR.

---

## Architecture

```
app/
├── main.py        # App instance, CORS, router registration
├── config.py      # Env var loading via pydantic-settings, DB URL construction
├── database.py    # Async engine, session factory, get_db dependency
├── models.py      # ORM models: User, Post, Vote (with cascade deletes)
├── schemas.py     # Pydantic v2 request/response schemas with field validation
├── oauth2.py      # JWT creation/decoding, get_current_user dependency
├── utils.py       # Argon2 password hashing via pwdlib
└── routers/
    ├── auth.py    # POST /login
    ├── post.py    # Full CRUD — GET, POST, PATCH, DELETE /posts
    ├── user.py    # GET, POST, GET /{id} /users
    └── vote.py    # POST /votes (upvote / unvote)

tests/
├── conftest.py    # Fixtures: session, client, authorized_client, test data
├── test_auth.py
├── test_posts.py
├── test_users.py
└── test_votes.py
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/login` | No | Login and receive JWT token |
| POST | `/users/` | No | Register a new user |
| GET | `/users/` | Yes | List all users |
| GET | `/users/{id}` | Yes | Get a single user |
| GET | `/posts/` | Yes | Get all posts, sorted by votes |
| POST | `/posts/` | Yes | Create a post |
| GET | `/posts/{id}` | Yes | Get a single post with vote count |
| PATCH | `/posts/{id}` | Yes | Partially update a post (owner only) |
| DELETE | `/posts/{id}` | Yes | Delete a post (owner only) |
| POST | `/votes/` | Yes | Vote (`dir: 1`) or unvote (`dir: 0`) a post |

`GET /posts/` supports `?limit=10&skip=0&search=` query params.
`GET /users/` supports `?limit=10&skip=0&search=` query params.

---

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `DATABASE_HOSTNAME` | Postgres host | `localhost` |
| `DATABASE_PORT` | Postgres port | `5432` |
| `DATABASE_USERNAME` | Postgres user | `postgres` |
| `DATABASE_PASSWORD` | Postgres password | `secret` |
| `DATABASE_NAME` | Main database | `fastapi` |
| `TEST_DATABASE_NAME` | Test database | `fastapi_test` |
| `SECRET_KEY` | JWT signing key | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `30` |

---

## Tech Stack

FastAPI · PostgreSQL · SQLAlchemy 2.0 (async) · Alembic · Pydantic v2 · PyJWT · pwdlib · slowapi · pytest-asyncio · Docker · GitHub Actions

---

## Quick Start

```bash
cp .env.example .env        # add your values
docker compose up --build   # starts postgres + api with migrations
```

Local: `pip install -r requirements.txt` → `alembic upgrade head` → `uvicorn app.main:app --reload`

API docs at `http://localhost:8000/docs`
**Live API:** https://fastapi-social-media-api-yom4.onrender.com/docs

---

## Running Tests

```bash
pytest -v
```

Requires `TEST_DATABASE_NAME` set in `.env` and the database created in Postgres.
