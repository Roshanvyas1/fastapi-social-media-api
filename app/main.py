from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import post, user, auth, vote

# Creating instance of an FastAPI
app = FastAPI()

# Although we can specify any specific origins/websites to work our applications(but here allowed for everyone).
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allowed every methods(get, post, etc) can be used.
    allow_headers=["*"],
)

# It will create model/table in our database.
# models.Base.metadata.create_all(bind=engine)   # Since we currently using alembic(migration tool) therefore we don't use this further.

app.include_router(post.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(vote.router)


@app.get("/")
def root():
    return {"message": "Hello, Dunia"}
