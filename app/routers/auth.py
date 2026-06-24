from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi.security import OAuth2PasswordRequestForm
from app import models
from app.schemas.user_schema import UserCreate, UserResponse
from app.schemas.auth_schema import UpdatePassword, TokenResponse
from app.utils.password import hash_password, verify_password, DUMMY_HASHED
from app.utils.oauth2 import create_access_token
from app.dependencies import get_current_user, get_db
from app.utils.limiter import limiter


router = APIRouter(tags=["Authentication"], prefix="/auth")


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
    summary="Create brand new user account",
)
@limiter.limit("3/minutes")
async def create_user(
    request: Request, user: UserCreate, db: AsyncSession = Depends(get_db)
):

    # Selecting User using same email (if any).
    existing_email = (
        (await db.execute(select(models.User).where(models.User.email == user.email)))
        .scalars()
        .first()
    )

    # If user found using existing email then raising exception.
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already exists!"
        )

    # Converting password into hashed password for security.
    hashed_password = hash_password(user.password)
    user.password = hashed_password

    new_user = models.User(**user.model_dump())

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and recieve a JWT access Token",
    description="Login through 'Authorize' button placed at top right corner (recommended)",
)
@limiter.limit("5/minutes")
async def login(
    request: Request,  # To get IP for rate limiting.
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):

    # Fetching user details.
    user = (
        (
            await db.execute(
                select(models.User).where(
                    models.User.email == user_credentials.username
                )
            )
        )
        .scalars()
        .first()
    )

    # If user doesn't exist.
    if not user:
        verify_password(
            user_credentials.password, DUMMY_HASHED
        )  # This is for time-eqalization(needed for security concerns)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid email or password!"
        )

    # If password is wrong.
    if not verify_password(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid email or password!"
        )

    # Creating access token using some information.
    access_token = create_access_token(data={"user_id": user.id})

    return {"access_token": access_token}


@router.patch(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change your own password",
)
async def update_password(
    password: UpdatePassword,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):

    if password.new_password != password.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New and Confirm password must Match.",
        )

    if password.current_password == password.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New and Current password must be different.",
        )

    if not verify_password(password.current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credential."
        )

    await db.execute(
        update(models.User)
        .where(models.User.id == current_user.id)
        .values(password=hash_password(password.new_password))
    )

    await db.commit()

    return {"message": "Password has been changed successfully."}
