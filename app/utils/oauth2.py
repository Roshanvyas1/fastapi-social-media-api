import jwt
from datetime import datetime, timedelta, timezone
from typing import Any
from app.config import settings

# Secret key is created USING CMD (python3 -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
EXPIRE_ACCESS_TOKEN_MINUTES = settings.access_token_expire_minutes


def create_access_token(data: dict[str, Any]):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_ACCESS_TOKEN_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(payload=to_encode, key=SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt
