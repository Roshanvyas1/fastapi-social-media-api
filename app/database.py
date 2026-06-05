from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

SQLALCHEMY_DATABASE_URL = settings.database_url

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)

AsyncSessionLocal = async_sessionmaker(
                        bind=engine,
                        expire_on_commit=False, 
                        autoflush=False
                    )

class Base(DeclarativeBase):
    pass

# Creating Session Dependency
async def get_db():
    async with AsyncSessionLocal() as db:
        yield db