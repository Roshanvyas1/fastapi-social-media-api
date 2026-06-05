from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.security import OAuth2PasswordRequestForm
from app.database import get_db
from app import models
from app.utils import verify_password, DUMMY_HASHED
from app.schemas import TokenResponse
from app.oauth2 import create_access_token

router = APIRouter(tags=['Authentication'])

@router.post('/login', response_model=TokenResponse)
async def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    
    # Fetching user details.
    user = (
        await db.execute(
        select(models.User).where(models.User.email == user_credentials.username)
        )
    ).scalars().first()
    
    # If user doesn't exist.
    if not user:
        verify_password(user_credentials.password, DUMMY_HASHED) # This is for time-eqalization(needed for security concerns)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Invalid email or password!'
        )
    
    # If password is wrong.
    if not verify_password(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Invalid email or password!'
            )
    
    # Creating access token using some information.
    access_token = create_access_token(data={'user_id': user.id})

    return {"access_token": access_token}