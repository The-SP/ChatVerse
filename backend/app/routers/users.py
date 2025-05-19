from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..auth.jwt import get_current_active_user
from ..database import get_db
from ..models.user import User
from ..schemas.user import UserSearchResponse

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


@router.get("/search/", response_model=List[UserSearchResponse])
async def search_users(
    query: str = Query(None, min_length=1, max_length=100),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Search for users by username, full_name, or email.

    - The search is case-insensitive and matches partial strings
    - Returns a maximum of `limit` results
    """
    if not query:
        return []

    # Create a search pattern for SQL LIKE (case-insensitive partial match)
    search_pattern = f"%{query}%"

    # Build the query to search across multiple fields
    search_results = (
        db.query(User)
        .filter(
            or_(
                User.username.ilike(search_pattern),
                User.full_name.ilike(search_pattern),
                User.email.ilike(search_pattern),
            )
        )
        .limit(limit)
        .all()
    )

    response = []
    for user in search_results:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "avatar_url": user.avatar_url,
            # Only include email if it's the current user or if you want to allow email discovery
            "email": user.email if user.id == current_user.id else None,
        }
        response.append(user_dict)

    return response
