# FastAPI Social Media API

Designed and deployed a fully asynchronous social media backend supporting authenticated CRUD operations, vote aggregation, CI/CD automation, Dockerized deployment, and isolated integration testing using FastAPI and PostgreSQL.

---

## Live Demo

🌐 Demo Client: https://fastapi-social-media-api.vercel.app/

📖 API Documentation: https://fastapi-social-media-api-yom4.onrender.com/docs

### Try It Yourself

1. Register an account
2. Create posts
3. Vote on posts
4. View ranked feed
5. Explore authenticated endpoints

---

## Tech Stack

FastAPI · PostgreSQL · SQLAlchemy 2.0 (async) · Alembic · Pydantic v2 · PyJWT · pwdlib · slowapi · pytest-asyncio · Docker · GitHub Actions

---

## What This Project Demonstrates

**Fully Async Stack**  
Every layer — database engine, session, route handlers, and tests — uses Python's `async/await`. Built on SQLAlchemy 2.0's async interface with psycopg v3, not the sync wrappers most tutorials use.

**Versioned API**  
All routes are mounted under an `/api/v1` prefix, keeping the public contract stable and leaving room for future versions without breaking existing clients.

**JWT Authentication with Timing Attack Mitigation**  
Login runs a dummy `verify_password` call even when the user doesn't exist, equalizing response time between "wrong email" and "wrong password." This prevents user enumeration via timing — a real security concern most implementations miss.

**Ownership-Enforced CRUD**  
Posts are tied to their creator via a foreign key. Update and delete operations verify ownership at the application layer before touching the database, returning `403 Forbidden` (not `404`) to avoid leaking resource existence.

**Partial Updates via PATCH**  
Update endpoint uses `PATCH` with `model_dump(exclude_unset=True)` — only fields explicitly provided in the request are updated. Clients aren't required to send the full object.

**Vote System with SQL Aggregation**  
Posts are returned with their vote counts using `outerjoin` + `func.count` aggregation in a single query, plus a `voted` flag indicating whether the current user has voted. The single-post endpoint uses a CTE for the same. No N+1 queries.

**Rate Limiting**  
`/auth/register` and `/auth/login` are protected with per-IP rate limiting via slowapi (3/min and 5/min), returning `429 Too Many Requests` once the threshold is exceeded. Prevents brute force on public endpoints.

**Health Check**  
`/api/v1/health` runs a live `SELECT 1` against the database, returning `503` if connectivity is lost — suitable for load-balancer and uptime probes.

**Isolated Async Test Suite**  
Tests use `httpx.AsyncClient` with FastAPI's `ASGITransport` — requests never touch a real network. The `get_db` dependency is overridden per-test with a dedicated test database that is created and dropped around each test, guaranteeing full isolation.

**Docker with Proper Startup Sequencing**  
The FastAPI container waits for a `pg_isready` health check before starting — not just a `depends_on: db` which doesn't guarantee readiness. On startup, `alembic upgrade head` runs automatically before the server starts.

**CI/CD Pipeline**  
GitHub Actions runs three independent jobs on every push: Ruff linter, `pip-audit` for dependency CVEs, and the full 60+ test suite against a live Postgres service. Merges to `main` build and push a tagged Docker image to GHCR.

**Web Client**  
A dependency-free, single-page client (`frontend/`) consumes the API as a working demo — auth, feed, voting, profiles, and post management. It's intentionally lightweight and framework-free: this project's focus is the backend, and the client exists to make the API tangible.

---

## Architecture

```
app/
├── main.py          # App instance, CORS, /api/v1 router registration, /health
├── config.py        # Env loading via pydantic-settings, DB URL construction
├── database.py      # Async engine + session factory
├── dependencies.py  # get_db, get_current_user (JWT decode + lookup)
├── models.py        # ORM models: User, Post, Vote (with cascade deletes)
├── schemas/         # Pydantic v2 request/response schemas, split by domain
│   ├── auth_schema.py
│   ├── post_schema.py
│   ├── user_schema.py
│   └── vote_schema.py
├── utils/
│   ├── oauth2.py        # JWT creation
│   ├── password.py      # Argon2 password hashing via pwdlib
│   ├── limiter.py       # slowapi rate limiter
│   └── query_builder.py # Reusable vote-count / voted-flag SQL
└── routers/
    ├── auth.py      # register, login, change-password
    ├── post.py      # Full CRUD + vote-ranked feed
    ├── user.py      # List users, profiles with their posts
    └── vote.py      # Vote / unvote

frontend/            # Vanilla-JS single-page client (no build step)
├── index.html
├── styles.css
└── app.js

tests/
├── conftest.py      # Fixtures: session, client, authorized_client, test data
├── test_auth.py
├── test_posts.py
├── test_users.py
└── test_votes.py
```

---

## API Endpoints

All endpoints are served under the `/api/v1` prefix.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | No | Register a new user |
| POST | `/auth/login` | No | Login and receive a JWT token |
| PATCH | `/auth/change-password` | Yes | Change your own password |
| GET | `/users/` | Yes | List users |
| GET | `/users/me` | Yes | Your profile, including your posts |
| GET | `/users/{id}` | Yes | A user's profile, including their posts |
| GET | `/posts/` | Yes | List posts, vote-ranked or newest |
| POST | `/posts/` | Yes | Create a post |
| GET | `/posts/{id}` | Yes | Get a single post with vote count |
| PATCH | `/posts/{id}` | Yes | Partially update a post (owner only) |
| DELETE | `/posts/{id}` | Yes | Delete a post (owner only) |
| POST | `/votes/` | Yes | Vote (`dir: 1`) or unvote (`dir: 0`) a post |
| GET | `/health` | No | Liveness + database connectivity check |

`GET /posts/` supports `?sort=top|new&limit=10&skip=0&search=&user_id=` — `search` matches post title or content.
`GET /users/` supports `?limit=10&skip=0&search=`.

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
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `15` |

---

## Quick Start

```bash
cp .env.example .env        # add your values
docker compose up --build   # starts postgres + api with migrations
```

Local: `pip install -r requirements.txt` → `alembic upgrade head` → `uvicorn app.main:app --reload`

API docs at `http://localhost:8000/docs`

The web client is static — open `frontend/index.html` directly, or serve the `frontend/` folder with any static host.

---

## Running Tests

```bash
pytest -v
```

Requires `TEST_DATABASE_NAME` set in `.env` and the database created in Postgres.

---

## Author

**Roshan Vyas**

[LinkedIn](https://www.linkedin.com/in/roshanvyas1/)
