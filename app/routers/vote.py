from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app import models
from app.schemas import Vote
from app.database import get_db
from app.oauth2 import get_current_user

router = APIRouter(
    prefix='/vote',
    tags=['Vote']
)

@router.post('/', status_code=status.HTTP_200_OK) # Since we doing both add and delete.
def vote(
    vote: Vote,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
    ):
    
    # Retrieving post.
    post_exist = db.get(models.Post, vote.post_id)

    # Checking post exist or not.
    if not post_exist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Post was not found'
        )
    
    # Retrieving vote.
    vote_exist = db.get(models.Vote, (vote.post_id, current_user.id))
    
    # If user wants to add vote(dir=1).
    if vote.dir == 1:

        # If vote already exist.
        if vote_exist:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='Your vote had already registered!'
            )
        
        # Adding new_vote in votes table.
        new_vote = models.Vote(
            post_id=vote.post_id,
            user_id=current_user.id
        )

        db.add(new_vote)
        db.commit()

        return {'message': 'Successfully voted!'}
    
    else:
        # If vote not found.
        if not vote_exist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You haven't voted yet!"
            )
        
        # Deleting vote.
        db.delete(vote_exist)
        db.commit()

        return {'message': 'Successfully unvoted!'}