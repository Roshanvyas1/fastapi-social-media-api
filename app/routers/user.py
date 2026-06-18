from fastapi import HTTPException, status, Depends, APIRouter, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models
from app.database import get_db
from app.schemas import UserCreate, UserResponse
from app.utils import hash_password
from app.oauth2 import get_current_user
from app.limiter import limiter

# Creating router object
router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=list[UserResponse], summary="Get existing users detail")
async def get_users(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    limit: int = 10,
    skip: int = 0,
    search: str = "",
):

    result = await db.execute(
        select(models.User)
        .where(models.User.email.icontains(search))
        .limit(limit)
        .offset(skip)
    )

    users = result.scalars().all()

    return users


@router.get(
    "/{id}", response_model=UserResponse, summary="Get single existing user detail"
)
async def get_user(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):

    user = await db.get(models.User, id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found!"
        )

    return user


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
    summary="Create brand new user id",
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
