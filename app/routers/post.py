from fastapi import HTTPException, status, Depends, APIRouter, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Literal
from sqlalchemy.orm import selectinload
from app import models
from app.dependencies import get_db, get_current_user
from app.schemas.post_schema import (
    PostCreate,
    PostUpdate,
    PostResponse,
    PostVoteOwnerResponse,
)
from app.schemas.user_schema import UserResponse
from app.utils.query_builder import get_voted_flag, get_vote_counts_cte

# Creating a router object
router = APIRouter(prefix="/posts", tags=["Posts"])


# Get posts
@router.get(
    "/",
    response_model=list[PostVoteOwnerResponse],
    summary="Get specfic or all user's posts",
)
async def get_posts(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    user_id: int | None = None,
    sort: Literal["top", "new"] = "top",
    limit: int = Query(default=10, ge=0, le=100),
    skip: int = Query(default=0, ge=0),
    search: str = Query(default=""),
):

    # creating here so that it can be reused later.
    vote_count = func.count(models.Vote.post_id).label("votes")

    # Correlated subquery.
    voted_flag = await get_voted_flag(current_user_id=current_user.id)

    stmt = (
        select(models.Post, vote_count, voted_flag)
        .options(selectinload(models.Post.owner))  # Eager loading for serialization.
        .outerjoin(models.Vote, models.Post.id == models.Vote.post_id)
        .group_by(models.Post.id)
        .where(or_(models.Post.published, models.Post.owner_id == current_user.id))
        .where(
            or_(
                models.Post.title.icontains(search),
                models.Post.content.icontains(search),
            )
        )
        .limit(limit)
        .offset(skip)
    )

    if user_id is not None:
        stmt = stmt.where(models.Post.owner_id == user_id)

    if sort == "new":
        stmt = stmt.order_by(models.Post.created_at.desc())
    else:
        stmt = stmt.order_by(vote_count.desc())

    result = await db.execute(stmt)

    posts = result.mappings().all()  # using mappings because here we are selecting both orm object and aggregated col.

    return posts


# Create post
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=PostResponse,
    summary="Create a new post",
)
async def create_posts(
    post: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):

    # Unpacking post so that we don't have to pass key arguments manually.
    new_post = models.Post(**post.model_dump(), owner_id=current_user.id)

    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)  # reload server-side columns (id, created_at, ...)
    await db.refresh(
        new_post, attribute_names=["owner"]
    )  # eager-load relationship for response

    return new_post


# Get specific post.
@router.get(
    "/{id}",
    response_model=PostVoteOwnerResponse,
    summary="Get specific post using post_id",
)
async def get_post(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):

    # Creating cte.
    vote_counts = await get_vote_counts_cte()

    # Correlated subquery.
    voted_flag = await get_voted_flag(current_user_id=current_user.id)

    stmt = (
        select(
            models.Post,
            func.coalesce(vote_counts.c.votes, 0).label("votes"),
            voted_flag,
        )
        .options(selectinload(models.Post.owner))
        .outerjoin(vote_counts, vote_counts.c.post_id == models.Post.id)
        .where(
            models.Post.id == id,
            or_(models.Post.published, models.Post.owner_id == current_user.id),
        )
    )

    result = await db.execute(stmt)

    post = result.mappings().first()

    # Checking whether the post exist or not.
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post was not found!"
        )

    return post


# Delete specific post.
@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a post (owned post only)",
)
async def delete_post(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):

    # Using get method, work only for primary attributes and is more optimize(uses sqlalchemy cache memory first for what we search).
    post = await db.get(models.Post, id)

    # If post doesn't exist.
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post was not found!"
        )

    # Checking if the selected post belongs to current_user or not.
    if post.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not Authorized!"
        )

    await db.delete(post)
    await db.commit()


# Update post.
@router.patch(
    "/{id}",
    response_model=PostResponse,
    summary="Update a post (owned post only)",
    description="ONLY field specified on the request body will be modified.",
)
async def update_post(
    id: int,
    post: PostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):

    # ORM style
    existing_post = await db.get(models.Post, id)

    # Checking whether the post exists or not.
    if existing_post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post was not found!"
        )

    # Checking if the selected post belongs to current_user or not.
    if existing_post.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not Authorized!"
        )

    # Converting in dict and excluding values that contains None.
    required_change_post = post.model_dump(exclude_unset=True)

    # Checking if there is anything to update or not.
    if not required_change_post:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No field provided to update!",
        )

    # updating rows through instance of Post using setattr method works like(instance.key=value)
    for key, value in required_change_post.items():
        setattr(existing_post, key, value)

    await db.commit()
    await db.refresh(existing_post)  # re-fetch columns after commit
    await db.refresh(
        existing_post, attribute_names=["owner"]
    )  # eager-load relationship for response

    return existing_post
