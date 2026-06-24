from pydantic import BaseModel
from typing import Literal


class Vote(BaseModel):
    post_id: int
    dir: Literal[0, 1]  # can only pass either 0 or 1.
