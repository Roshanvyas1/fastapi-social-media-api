from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app import models


async def get_vote_counts_cte():
    return (
        select(models.Vote.post_id, func.count().label("votes"))
        .group_by(models.Vote.post_id)
        .cte("vote_counts")
    )


async def get_voted_flag(current_user_id: int):
    return (
        select(models.Vote.post_id)
        .where(
            models.Vote.post_id == models.Post.id,
            models.Vote.user_id == current_user_id,
        )
        .correlate(models.Post)
        .exists()
        .label("voted")
    )


async def get_posts_with_votes(db: AsyncSession, owner_id: int, current_user_id: int):

    vote_counts = await get_vote_counts_cte()

    voted_flag = await get_voted_flag(current_user_id)

    posts = (
        (
            await db.execute(
                select(
                    models.Post,
                    func.coalesce(vote_counts.c.votes, 0).label("votes"),
                    voted_flag,
                )
                .outerjoin(vote_counts, vote_counts.c.post_id == models.Post.id)
                .where(
                    models.Post.owner_id == owner_id,
                    or_(models.Post.published, models.Post.owner_id == current_user_id),
                )
                .order_by(models.Post.created_at.desc())
            )
        )
        .mappings()
        .all()
    )

    return posts
