from fastapi import APIRouter, Depends

from ..auth.jwt import get_current_active_user
from ..models.user import User

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
