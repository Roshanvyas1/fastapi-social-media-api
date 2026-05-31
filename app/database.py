from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

# %40 is used for @ in password since we can't used directly in our url because it can only be used before host_name.
SQLALCHEMY_DATABASE_URL = settings.database_url

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

# Creating Session Dependency
def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally:
        db.close()