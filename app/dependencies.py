import jwt
from jwt.exceptions import InvalidTokenError
from app.schemas.auth_schema import TokenData
from app.database import AsyncSessionLocal
from app import models
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from app.config import settings


# Creating Session Dependency
async def get_db():
    async with AsyncSessionLocal() as db:
        yield db


# Extract tokens.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate Credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decoding for validation.
        payload = jwt.decode(
            jwt=token, key=settings.secret_key, algorithms=[settings.algorithm]
        )

        id = payload.get("user_id")
        if id is None:
            raise credential_exception

        token_data = TokenData(id=id)

    except InvalidTokenError:
        raise credential_exception

    # Retrieving user details.
    user = (
        (await db.execute(select(models.User).where(models.User.id == token_data.id)))
        .scalars()
        .first()
    )

    if user is None:
        raise credential_exception

    return user
