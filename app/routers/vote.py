from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app import models
from app.schemas import Vote
from app.database import get_db
from app.oauth2 import get_current_user

router = APIRouter(prefix="/votes", tags=["Vote"])


@router.post("/", status_code=status.HTTP_200_OK)
async def vote(
    vote: Vote,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):

    # Retrieving post.
    existing_post = await db.get(models.Post, vote.post_id)

    # Checking post exist or not.
    if not existing_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post was not found"
        )

    # Retrieving user existing vote.
    existing_vote = await db.get(models.Vote, (vote.post_id, current_user.id))

    # If user wants to add vote(dir=1).
    if vote.dir == 1:
        # If vote already exist.
        if existing_vote:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Your vote had already registered!",
            )

        # Adding new_vote.
        new_vote = models.Vote(post_id=vote.post_id, user_id=current_user.id)

        db.add(new_vote)
        await db.commit()

        return {"message": "Successfully voted!"}

    else:
        # If vote not found.
        if not existing_vote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Your vote doesn't exist!"
            )

        # Deleting vote.
        await db.delete(existing_vote)
        await db.commit()

        return {"message": "Successfully unvoted!"}
