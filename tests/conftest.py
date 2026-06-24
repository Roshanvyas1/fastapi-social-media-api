import pytest
from httpx import AsyncClient, ASGITransport
import jwt
from app.main import app
from app.dependencies import get_db
from app.database import Base
from app import models
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import settings
from app.utils.limiter import limiter
import asyncio
import sys

# This tells Python —> if we are on Windows, use SelectorEventLoop instead of the default ProactorEventLoop.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


TEST_DATABASE_URL = settings.test_database_url

test_engine = create_async_engine(url=TEST_DATABASE_URL)

TestSessionLocal = async_sessionmaker(
    bind=test_engine, expire_on_commit=False, autoflush=False
)


# Creating session fixture which does setup -> run test -> cleanup.
@pytest.fixture
async def session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as db:
        yield db

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(session):
    async def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db  # swapping real db with test_db.

    async with (
        AsyncClient(
            transport=ASGITransport(
                app=app
            ),  # It tells AsyncClient, instead of sending requests over a real network, use this ASGI app directly in memory.
            base_url="http://test",  # It is doing nothing, just for formatting (added because it is required field).
        ) as ac
    ):
        yield ac

    app.dependency_overrides.clear()  # again switching back to real db.


@pytest.fixture
async def test_user(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "dummy@gmail.com", "password": "dummy123"},
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
async def token(test_user, client):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user["email"], "password": "dummy123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

    token = response.json()["access_token"]
    data = jwt.decode(
        jwt=token, key=settings.secret_key, algorithms=[settings.algorithm]
    )
    user_id = data["user_id"]
    assert test_user["id"] == user_id

    return token


@pytest.fixture
async def authorized_client(token, client):
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture
async def test_post(session, test_user):

    post = models.Post(
        title="Dummy Title",
        content="Dummy Content",
        published=True,
        owner_id=test_user["id"],  # created by user1.
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)

    return post


@pytest.fixture
async def test_user2(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "random@gmail.com", "password": "random123"},
    )
    assert response.status_code == 201

    return response.json()


@pytest.fixture
async def test_post2(session, test_user2):
    post = models.Post(
        title="Random Title",
        content="Random Content",
        published=True,
        owner_id=test_user2["id"],  # Created by user2.
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)

    return post


@pytest.fixture
async def test_vote(session, test_post, test_user):
    vote = models.Vote(post_id=test_post.id, user_id=test_user["id"])
    session.add(vote)
    await session.commit()
    await session.refresh(vote)

    return vote


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    limiter.reset()  # Reset rate limiter before every test.
    yield
