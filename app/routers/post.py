from fastapi import HTTPException, status, Depends, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, update, func
from app import models
from app.database import get_db
from app.schemas import PostCreate, PostUpdate, PostResponse, PostVoteResponse, UserResponse
from app.oauth2 import get_current_user

# Creating a router object
router = APIRouter(
    prefix='/posts',
    tags=['Posts']
)

# Get posts
@router.get("/", response_model=list[PostVoteResponse]) 
def get_posts(
    db: Session = Depends(get_db), 
    current_user: UserResponse = Depends(get_current_user),
    limit: int = 10,
    skip: int = 0,
    search: str = ""
    ):

    # creating here so that it can be reused later.
    vote_count = func.count(models.Vote.post_id).label('votes') 
    stmt = (
        select(models.Post, vote_count)
        .outerjoin(models.Vote, models.Post.id == models.Vote.post_id)
        .group_by(models.Post.id).order_by(vote_count.desc())    # groupby works here because Post.id is uniquely identifies other attributes here.
        .where(models.Post.title.icontains(search))
        .limit(limit)
        .offset(skip)
        )
    posts = db.execute(stmt).mappings().all()  # using mappings because here we are selecting multiple columns instead of only orm object.

    return posts

# Create post
@router.post('/', status_code=status.HTTP_201_CREATED, response_model=PostResponse) 
def create_posts(
    post: PostCreate, 
    db: Session = Depends(get_db), 
    current_user: UserResponse = Depends(get_current_user)
    ): 

    # Unpacking post so that we don't have to pass key arguments manually.
    new_post = models.Post(
        **post.model_dump(),
        owner_id=current_user.id      # As obvious owner_id must be the id of current_user(who is currently logged in)
        )
    
    db.add(new_post) # adding in database
    db.commit() # commit changes
    db.refresh(new_post) # re-fetching new_post after commit 
    
    return {"Post": new_post}

# Get specific post.
@router.get("/{id}", response_model=PostVoteResponse) # id represents path parameter.
def get_post(
    id: int, 
    db: Session = Depends(get_db), 
    current_user: UserResponse = Depends(get_current_user)  # checks logged in or not.
    ):

    # Creating cte.
    vote_counts = (
        select(
            models.Vote.post_id, 
            func.count().label('votes')
            )
            .group_by(models.Vote.post_id)
            .cte('vote_counts')
        )
    
    stmt = (
        select(
            models.Post,
            func.coalesce(vote_counts.c.votes, 0).label('votes')  # null handlings (whichever post don't have votes will get null).
        )
        .outerjoin(
            vote_counts,
            vote_counts.c.post_id == models.Post.id    # .c is used for accessing column (directly not possible).
            )
        .where(models.Post.id == id)
    )

    post = db.execute(stmt).mappings().first()

    # Checking whether the post exist or not.
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,    # manually sending the routerropriate status_code
            detail="Post was not found!"
            )
    
    return post

# Delete specific post.
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT) 
def delete_post(
    id: int, 
    db: Session = Depends(get_db), 
    current_user: UserResponse = Depends(get_current_user)
    ):

    # Using get method, work only for primary attributes and is more optimize(uses sqlalchemy internal memory first for what we search).
    post = db.get(models.Post, id)

    # If post doesn't exist.
    if post is None :
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post was not found!"
            )
    
    # Checking if the selected post belongs to current_user or not.
    if post.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not Authorized!"
        )
    
    db.delete(post)
    db.commit()
    
# Update post.
@router.patch("/{id}", response_model=PostResponse)
def update_post(
    id: int, 
    post: PostUpdate, 
    db: Session = Depends(get_db), 
    current_user: UserResponse = Depends(get_current_user)
    ):
    
    # ORM style
    existing_post = db.get(models.Post, id)

    # Checking whether the post exists or not.
    if existing_post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,    
            detail="Post was not found!"
            )
    
    # Checking if the selected post belongs to current_user or not.
    if existing_post.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not Authorized!"
        )
    
    # Converting in dict and excluding values that contains None.
    required_change_post = post.model_dump(exclude_unset=True)

    # Checking if there is anything to update or not.
    if not required_change_post:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,    
            detail=f"No field provided to update!"
            )
    
    # updating rows through instance of Post using setattr method works like(instance.key=value)
    for key, value in required_change_post.items():
        setattr(existing_post, key, value)

    db.commit()
    db.refresh(existing_post) # re-fetching existing_post after commit

    return existing_post