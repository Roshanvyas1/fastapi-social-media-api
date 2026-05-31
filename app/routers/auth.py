from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi.security import OAuth2PasswordRequestForm
from app.database import get_db
from app import models
from app.utils import verify_password, DUMMY_HASHED
from app.schemas import LoginRequest, LoginResponse
from app.oauth2 import create_access_token

router = APIRouter(tags=['Authentication'])

@router.post('/login', response_model=LoginResponse)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Using OAuth2PasswordRequestForm instead of LoginRequest, that have username and password fields only (required)
    user = db.execute(
        select(models.User).where(models.User.email == user_credentials.username)
        ).scalars().first()
    
    if not user:
        verify_password(user_credentials.password, DUMMY_HASHED) # This is for time-eqalization(security from atackers)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Invalid email or password!'
        )
    
    if not verify_password(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Invalid email or password!'
            )
    
    access_token = create_access_token(data={'user_id': user.id})

    return {
        'access_token': access_token, 
        'token_type': 'bearer'
        }