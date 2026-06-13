import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone
from app.schemas import TokenData
from app.database import get_db
from app import models
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from typing import Any
from app.config import settings

# Secret key is created USING CMD (python3 -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
EXPIRE_ACCESS_TOKEN_MINUTES = settings.access_token_expire_minutes

# Extract tokens.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def create_access_token(data: dict[str, Any]):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_ACCESS_TOKEN_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(payload=to_encode, key=SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


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
        payload = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=[ALGORITHM])

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
