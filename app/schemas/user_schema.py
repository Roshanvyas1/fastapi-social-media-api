from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    # Allowing conversion from orm objects using object attributes.
    model_config = {"from_attributes": True}


# Imported here (not at top) to break the circular import with post_schema.
from app.schemas.post_schema import PostVoteResponse  # noqa: E402 (telling ruff to ignore this mid level import)


class UserPostVoteResponse(BaseModel):
    user: UserResponse
    posts: list[PostVoteResponse]

    model_config = {"from_attributes": True}
