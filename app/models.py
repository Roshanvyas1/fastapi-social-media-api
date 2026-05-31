from sqlalchemy import String, Integer, Boolean, TIMESTAMP, text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from datetime import datetime

# Creating model/table.
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    published: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, 
                                                 server_default=text('now()'))
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey(column='users.id', ondelete='CASCADE'), 
                                          nullable=False)
    
    owner: Mapped["User"] = relationship(back_populates='posts') 
    
class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, 
                                                 server_default=text('now()'))
    
    posts: Mapped[list['Post']] = relationship(back_populates='owner')

class Vote(Base):
    __tablename__ = "votes"

    post_id: Mapped[int] = mapped_column(ForeignKey(column='posts.id', ondelete='CASCADE'), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(column='users.id', ondelete='CASCADE'), primary_key=True)