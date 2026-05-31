from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

# Required attributes to create a post.
class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1)
    published: bool = True
    # owner_id: int              # We don't need this to pass it from request explicitly (it would be fetched from current_user).
    
# Required attribute to update a post.
class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=120)
    content: Optional[str] = Field(None, min_length=1)
    published: Optional[bool] = None
    # owner_id: int | None = None  # Modern way of using optional.  # Illogical to add this (since a user cannot able to update anyone's owner_id)
    
class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    published: bool
    created_at: datetime
    owner_id: int
    owner: 'UserResponse'   # Using '' because UserResponse haven't defined yet (now python won't throw error).

    # Allowing conversion from orm objects using object attributes.
    model_config = {
        'from_attributes': True
    }

class PostVoteResponse(BaseModel):
    Post: PostResponse
    votes: int = 0      # default for newly created post.

    # Allowing conversion from orm objects using object attributes.
    model_config = {
        'from_attributes': True
    }

class UserCreate(BaseModel):
    email: EmailStr 
    password: str = Field(min_length=8)

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    # Allowing conversion from orm objects using object attributes.
    model_config = {
        'from_attributes': True
    }

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: int | None = None

class Vote(BaseModel):
    post_id: int
    dir: int = Field(ge=0, le=1)  # can only pass either 0 or 1.