from fastapi import HTTPException, status, Depends, APIRouter, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models
from app.dependencies import get_db, get_current_user
from app.schemas.user_schema import UserResponse, UserPostVoteResponse
from app.utils.query_builder import get_posts_with_votes


# Creating router object
router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/", response_model=list[UserResponse], summary="Get existing users account"
)
async def get_users(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    limit: int = Query(default=10, ge=0, le=100),
    skip: int = Query(default=0, ge=0),
    search: str = Query(default=""),
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
    "/me",
    response_model=UserPostVoteResponse,
    summary="Get your own profile (including posts)",
)
async def logged_user(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):

    posts = await get_posts_with_votes(
        db=db, owner_id=current_user.id, current_user_id=current_user.id
    )

    return {"user": current_user, "posts": posts}


@router.get(
    "/{id}",
    response_model=UserPostVoteResponse,
    summary="Get another user profile including their posts (using id)",
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

    posts = await get_posts_with_votes(
        db=db, owner_id=id, current_user_id=current_user.id
    )

    return {"user": user, "posts": posts}
