from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.utils.limiter import limiter
from sqlalchemy import text
from app.routers import post, user, auth, vote
from app.dependencies import get_db

# Creating instance of an FastAPI with title, description and version.
app = FastAPI(
    title="Social Media API",
    description="""
A production-style Social Media REST API built with FastAPI — demonstrating async architecture, secure auth, and automated CI/CD.

**To test protected endpoints:** click **Authorize** (top right), enter your registered email as username and your password, then click Authorize. Your token is fetched and applied automatically.

**Engineering highlights:**
- Fully async stack — SQLAlchemy 2.0 + psycopg, end to end
- JWT auth with timing-attack mitigation on login
- Ownership-enforced CRUD (403, not 404, to avoid leaking resource existence)
- Vote counts via SQL aggregation — no N+1 queries
- Per-IP rate limiting on auth endpoints
- Alembic-managed schema migrations
- `/health` endpoint with live DB connectivity check
- Automated testing in CI pipeline
- Cloud deployed with automated CI/CD

[GitHub Repository](https://github.com/Roshanvyas1/fastapi-social-media-api) | 
[CI/CD Pipeline](https://github.com/Roshanvyas1/fastapi-social-media-api/actions) |
[Linkedin Profile](https://www.linkedin.com/in/roshanvyas1/)
""",
    version="1.0.0",
)

# Makes the limiter available to middleware.
app.state.limiter = limiter

# Converts slowapi exception into HTTP response.
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

# Although we can specify any specific origins/websites to work our applications.
origins = ["https://fastapi-social-media-api.vercel.app", "http://localhost:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,  # Not needed for jwt authentication.
    allow_methods=["*"],  # Allowed every methods(get, post, etc) can be used.
    allow_headers=["*"],
)

# It will create model/table in our database.
# models.Base.metadata.create_all(bind=engine)   # Since we currently using alembic(migration tool) therefore we don't use this further.

app.include_router(auth.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(post.router, prefix="/api/v1")
app.include_router(vote.router, prefix="/api/v1")


@app.get(
    "/api/v1/health", tags=["Health-Check"], summary="Confirms Database Connection"
)
async def health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database Unavailable",
        )
