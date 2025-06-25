from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .config import settings
from .database import Base, engine
from .logger import init_logger
from .routers import auth, direct_message, users, websocket_routes

logger = init_logger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastAPI Chat")

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
app.include_router(
    direct_message.router, prefix="/direct-messages", tags=["direct-messages"]
)
app.include_router(
    websocket_routes.router, prefix="/direct-messages", tags=["websockets"]
)


@app.get("/")
async def root():
    return {
        "message": "Welcome to FastAPI Chat API",
        "docs": "/docs",
        "login_endpoints": {
            "google": "/auth/login/google",
        },
        "websocket_endpoint": "/direct-messages/ws/",
    }
