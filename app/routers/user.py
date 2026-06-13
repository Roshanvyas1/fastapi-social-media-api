from fastapi import HTTPException, status, Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models
from app.database import get_db
from app.schemas import UserCreate, UserResponse
from app.utils import hash_password

# Creating router object
router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=list[UserResponse])
async def get_users(db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(models.User))

    users = result.scalars().all()

    return users


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):

    # Converting password into hashed password for security.
    hashed_password = hash_password(user.password)
    user.password = hashed_password

    new_user = models.User(**user.model_dump())

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

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user
