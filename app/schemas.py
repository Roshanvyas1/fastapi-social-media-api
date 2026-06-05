from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1)
    published: bool = True
    
class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=120)
    content: Optional[str] = Field(None, min_length=1)
    published: Optional[bool] = None
    
class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    published: bool
    created_at: datetime
    owner_id: int
    owner: 'UserResponse'   

    # Allowing conversion from orm objects using object attributes.
    model_config = {
        'from_attributes': True
    }

class PostVoteResponse(BaseModel):
    Post: PostResponse
    votes: int       

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

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'Bearer'

class TokenData(BaseModel):
    id: int | None = None

class Vote(BaseModel):
    post_id: int
    dir: int = Field(ge=0, le=1)  # can only pass either 0 or 1.