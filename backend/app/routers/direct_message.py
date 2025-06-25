from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..auth.jwt import get_current_user
from ..database import get_db
from ..models.direct_message import DirectMessage
from ..models.user import User
from ..schemas.direct_message import DirectMessageCreate, DirectMessageResponse
from ..schemas.user import UserResponse
from .websocket_manager import connection_manager

router = APIRouter()


@router.post(
    "/", response_model=DirectMessageResponse, status_code=status.HTTP_201_CREATED
)
async def create_direct_message(
    message: DirectMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new direct message"""
    # Check if receiver exists
    receiver = db.query(User).filter(User.id == message.receiver_id).first()
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {message.receiver_id} not found",
        )

    # Create new message
    db_message = DirectMessage(
        content=message.content,
        sender_id=current_user.id,
        receiver_id=message.receiver_id,
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    # Prepare message data for WebSocket notification
    message_data = {
        "id": db_message.id,
        "content": db_message.content,
        "created_at": db_message.created_at.isoformat(),
        "is_read": db_message.is_read,
        "sender_id": db_message.sender_id,
        "receiver_id": db_message.receiver_id,
        "sender": {
            "id": current_user.id,
            "username": current_user.username,
            "avatar_url": current_user.avatar_url,
        },
    }

    # Notify the receiver through WebSocket if they're connected
    await connection_manager.send_personal_message(
        message={"type": "new_message", "data": message_data},
        user_id=message.receiver_id,
    )

    return db_message


@router.get("/", response_model=List[DirectMessageResponse])
async def get_user_messages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    other_user_id: Optional[int] = None,
    limit: int = 50,
    skip: int = 0,
):
    """
    Get messages for the current user, optionally filtered by conversation with another user
    """
    if other_user_id:
        # Get conversation between current user and specific other user
        query = db.query(DirectMessage).filter(
            (
                (DirectMessage.sender_id == current_user.id)
                & (DirectMessage.receiver_id == other_user_id)
            )
            | (
                (DirectMessage.sender_id == other_user_id)
                & (DirectMessage.receiver_id == current_user.id)
            )
        )
    else:
        # Get all messages for current user
        query = db.query(DirectMessage).filter(
            (DirectMessage.sender_id == current_user.id)
            | (DirectMessage.receiver_id == current_user.id)
        )

    # Order by creation date, newest last
    messages = query.order_by(DirectMessage.created_at).offset(skip).limit(limit).all()
    return messages


@router.get("/conversations", response_model=List[UserResponse])
async def get_user_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a list of users the current user has exchanged messages with,
    ordered by the timestamp of the most recent message.
    """
    stmt = text(
        """
        WITH LastMessages AS (
            SELECT 
                CASE 
                    WHEN sender_id = :current_user_id THEN receiver_id 
                    ELSE sender_id 
                END AS user_id,
                MAX(created_at) AS last_message_time
            FROM direct_messages
            WHERE sender_id = :current_user_id OR receiver_id = :current_user_id
            GROUP BY user_id
        )
        SELECT u.*
        FROM users u
        JOIN LastMessages lm ON u.id = lm.user_id
        ORDER BY lm.last_message_time DESC
    """
    )

    result = db.execute(stmt, {"current_user_id": current_user.id})
    users = [User(**row._mapping) for row in result]
    return users


@router.put("/{message_id}/read")
async def mark_message_as_read(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a message as read"""
    message = db.query(DirectMessage).filter(DirectMessage.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message with id {message_id} not found",
        )

    # Verify the user is the receiver of this message
    if message.receiver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only mark messages addressed to you as read",
        )

    # Mark as read
    message.is_read = True
    db.commit()

    return {"status": "success"}


@router.get("/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get count of unread messages"""
    count = (
        db.query(DirectMessage)
        .filter(DirectMessage.receiver_id == current_user.id, not DirectMessage.is_read)
        .count()
    )

    return {"unread_count": count}


@router.get("/online-users")
async def get_online_users(
    current_user: User = Depends(get_current_user),
):
    """Get list of currently connected user IDs"""
    connected_users = connection_manager.get_connected_users()
    return {"online_users": connected_users}


@router.get("/user-status/{user_id}")
async def check_user_online_status(
    user_id: int,
    current_user: User = Depends(get_current_user),
):
    """Check if a specific user is currently online"""
    is_online = connection_manager.is_user_connected(user_id)
    return {"user_id": user_id, "is_online": is_online}
