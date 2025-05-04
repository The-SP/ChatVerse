from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .config import settings
from .database import Base, engine
from .routers import auth, users, direct_message

# Create tables
Base.metadata.create_all(bind=engine)


app = FastAPI(title="FastAPI Social Auth")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add SessionMiddleware for OAuth flows
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Mount routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(direct_message.router, prefix="/direct-messages", tags=["direct-messages"])


@app.get("/")
async def root():
    return {
        "message": "Welcome to FastAPI Social Auth API",
        "docs": "/docs",
        "login_endpoints": {
            "google": "/auth/login/google",
            "github": "/auth/login/github",
            "facebook": "/auth/login/facebook",
        },
    }
