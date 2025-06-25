from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..auth import jwt, utils
from ..auth import oauth as oauth_module
from ..config import settings
from ..database import get_db
from ..logger import init_logger
from ..schemas.user import UserCreate

logger = init_logger(__name__)
router = APIRouter()


# Standard username/password login
@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = utils.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"Successful login for user: {user.username}")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=dict)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user_by_email = utils.get_user_by_email(db, user_data.email)
    if db_user_by_email:
        logger.warning(f"Registration failed - email already exists: {user_data.email}")
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user_by_username = utils.get_user_by_username(db, user_data.username)
    if db_user_by_username:
        logger.warning(
            f"Registration failed - username already taken: {user_data.username}"
        )
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create user
    hashed_password = jwt.get_password_hash(user_data.password)
    new_user_data = {
        "email": user_data.email,
        "username": user_data.username,
        "hashed_password": hashed_password,
        "auth_provider": "local",
    }
    user = utils.create_user(db, new_user_data)
    logger.info(f"New user registered: {user.username}")

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


# Google OAuth routes
@router.get("/login/google")
async def login_google(request: Request):
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth_module.oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth_module.oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")

        if not user_info:
            logger.error("Could not fetch user info from Google OAuth")
            raise HTTPException(
                status_code=400, detail="Could not fetch user info from Google"
            )

        # Check if user already exists with this provider
        user = utils.get_user_by_provider_and_id(db, "google", user_info["sub"])

        if not user:
            # Check if email already exists
            user_by_email = utils.get_user_by_email(db, user_info["email"])

            if user_by_email:
                # Link existing account with Google
                user_by_email.auth_provider = "google"
                user_by_email.provider_user_id = user_info["sub"]
                user_by_email.provider_access_token = token.get("access_token")
                user_by_email.avatar_url = user_info.get("picture")
                user_by_email.full_name = user_info.get("name")
                db.commit()
                user = user_by_email
                logger.info(f"Linked existing account with Google OAuth: {user.email}")
            else:
                # Create new user
                username = oauth_module.generate_username(prefix="google")
                user_data = {
                    "email": user_info["email"],
                    "username": username,
                    "auth_provider": "google",
                    "provider_user_id": user_info["sub"],
                    "provider_access_token": token.get("access_token"),
                    "avatar_url": user_info.get("picture"),
                    "full_name": user_info.get("name"),
                }
                user = utils.create_user(db, user_data)
                logger.info(f"New user created via Google OAuth: {user.email}")

        logger.info(f"Google OAuth successful for user: {user.email}")

        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = jwt.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        # Redirect to the frontend with the token
        frontend_url = settings.FRONTEND_URL
        response = RedirectResponse(
            url=f"{frontend_url}/auth/success?token={access_token}"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google OAuth callback failed: {str(e)}")
        raise HTTPException(status_code=400, detail="OAuth authentication failed")


# Success page after OAuth authentication
@router.get("/success")
async def auth_success(token: str):
    return {"access_token": token, "token_type": "bearer"}
