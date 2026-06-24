from pydantic import BaseModel, Field, model_validator
from typing import Mapping, Optional
from datetime import datetime


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1)
    published: bool = True


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=120)
    content: Optional[str] = Field(None, min_length=1)
    published: Optional[bool] = None


class PostBase(BaseModel):
    id: int
    title: str
    content: str
    published: bool
    owner_id: int
    created_at: datetime


class PostVoteResponse(PostBase):
    votes: int
    voted: bool  # whether the current authenticated user has voted on this post

    # Allowing conversion from orm objects using object attributes.
    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def flatten_post(cls, data):
        if (
            isinstance(data, Mapping) and "Post" in data
        ):  # if comming from sqlalchemy row-mapping and contains Post.
            post = data["Post"]
            return {
                **{col.key: getattr(post, col.key) for col in post.__table__.columns},
                "votes": data.get("votes", 0),
                "voted": data.get("voted", False),
            }
        return data


# Imported here (not at top) to break the circular import with user_schema.
from app.schemas.user_schema import UserResponse  # noqa: E402 (telling ruff to ignore this mid level import)


class PostResponse(PostBase):
    owner: UserResponse

    # Allowing conversion from orm objects using object attributes.
    model_config = {"from_attributes": True}


class PostVoteOwnerResponse(PostResponse):
    owner: UserResponse
    votes: int
    voted: bool

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def flatten_post(cls, data):
        if isinstance(data, Mapping) and "Post" in data:
            post = data["Post"]
            return {
                **{col.key: getattr(post, col.key) for col in post.__table__.columns},
                "owner": post.owner,
                "votes": data.get("votes", 0),
                "voted": data.get("voted", False),
            }
        return data
