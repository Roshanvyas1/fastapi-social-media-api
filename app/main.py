from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.limiter import limiter
from sqlalchemy import text
from app.routers import post, user, auth, vote
from app.database import get_db

# Creating instance of an FastAPI
app = FastAPI()

# Makes the limiter available to middleware.
app.state.limiter = limiter

# Converts slowapi exception into HTTP response.
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

# Although we can specify any specific origins/websites to work our applications(but here allowed for everyone).
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,  # Not needed for jwt authentication.
    allow_methods=["*"],  # Allowed every methods(get, post, etc) can be used.
    allow_headers=["*"],
)

# It will create model/table in our database.
# models.Base.metadata.create_all(bind=engine)   # Since we currently using alembic(migration tool) therefore we don't use this further.

app.include_router(post.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(vote.router)


@app.get("/health", tags=["Health-Check"])
async def health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database Unavailable",
        )
