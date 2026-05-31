import jwt 
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone
from app.schemas import TokenData
from app.database import get_db
from app import models
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from typing import Any
from app.config import settings

# CREATED USING CMD (python3 -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
EXPIRE_ACCESS_TOKEN_MINUTES = settings.access_token_expire_minutes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/login')

def create_access_token(data: dict[str,Any]):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_ACCESS_TOKEN_MINUTES)
    to_encode.update({'exp': expire})

    encoded_jwt = jwt.encode(
        payload=to_encode,
        key=SECRET_KEY, 
        algorithm=ALGORITHM
        )
    
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate Credentials',
        headers={'WWW-Authenticate': 'Bearer'}
    )
    try:
        payload = jwt.decode(
            jwt=token,
            key=SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        id = payload.get('user_id')
        if id is None:
            raise credential_exception

        token_data = TokenData(id=id)

    except InvalidTokenError:
        raise credential_exception

    user = db.execute(
        select(models.User).where(models.User.id == token_data.id)
        ).scalars().first()
    if user is None:
        raise credential_exception
    
    return user

