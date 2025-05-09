from fastapi import APIRouter, Depends

from ..auth.jwt import get_current_active_user
from ..models.user import User
from sqlalchemy.orm import Session
from ..database import get_db

router = APIRouter()


@router.get("/me", response_model=dict)
async def get_user_me(current_user: User = Depends(get_current_active_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "avatar_url": current_user.avatar_url,
        "full_name": current_user.full_name,
        "auth_provider": current_user.auth_provider,
        "created_at": current_user.created_at,
    }


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "full_name": user.full_name,
        "auth_provider": user.auth_provider,
        "created_at": user.created_at,
    }
