from sqlalchemy.orm import Session

from ..models.user import User
from .jwt import verify_password


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def get_user_by_provider_and_id(db: Session, provider: str, provider_id: str):
    return (
        db.query(User)
        .filter(User.auth_provider == provider, User.provider_user_id == provider_id)
        .first()
    )


def create_user(db: Session, user_data: dict):
    db_user = User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        user = get_user_by_email(db, username)  # Try with email
        if not user:
            return False
    if not user.hashed_password:  # Social auth user
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user
