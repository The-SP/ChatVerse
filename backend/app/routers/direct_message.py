from datetime import datetime
from typing import Dict, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from jose import jwt
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..auth.jwt import get_current_user
from ..config import settings
from ..database import get_db, get_db_context, get_new_db_session
from ..models.direct_message import DirectMessage
from ..models.user import User
from ..schemas.direct_message import DirectMessageCreate, DirectMessageResponse
from ..schemas.user import UserResponse

router = APIRouter()


# Connection Manager for WebSockets
class ConnectionManager:
    def __init__(self):
        # Dictionary to store active connections: {user_id: WebSocket}
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        """Register a new WebSocket connection for a user"""
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        """Remove a WebSocket connection for a user"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        """Send a message to a specific user if they are connected"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
                return True
            except Exception:
                # Connection might be broken but not properly closed
                self.disconnect(user_id)
                return False
        return False

    async def broadcast(self, message: dict, exclude_user_id: Optional[int] = None):
        """Send a message to all connected users except the excluded one"""
        disconnected_users = []

        for user_id, connection in self.active_connections.items():
            if exclude_user_id is not None and user_id == exclude_user_id:
                continue

            try:
                await connection.send_json(message)
            except Exception:
                disconnected_users.append(user_id)

        # Clean up any disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)


# Initialize the connection manager
manager = ConnectionManager()


@router.post(
    "/", response_model=DirectMessageResponse, status_code=status.HTTP_201_CREATED
)
async def create_direct_message(
    message: DirectMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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

    # Prepare message data
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

    # Notify the receiver through websocket if they're connected
    await manager.send_personal_message(
        message={"type": "new_message", "data": message_data},
        user_id=message.receiver_id,
    )

    # Return response
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
    query = (
        db.query(DirectMessage).filter(
            (
                (DirectMessage.sender_id == current_user.id)
                & (DirectMessage.receiver_id == other_user_id)
            )
            | (
                (DirectMessage.sender_id == other_user_id)
                & (DirectMessage.receiver_id == current_user.id)
            )
        )
        if other_user_id
        else db.query(DirectMessage).filter(
            (DirectMessage.sender_id == current_user.id)
            | (DirectMessage.receiver_id == current_user.id)
        )
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
    """
    Mark a message as read
    """
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
    """
    Get count of unread messages
    """
    count = (
        db.query(DirectMessage)
        .filter(DirectMessage.receiver_id == current_user.id, not DirectMessage.is_read)
        .count()
    )

    return {"unread_count": count}


# Function to authenticate WebSocket connections - Fixed to not use Depends
async def get_user_from_token(websocket: WebSocket, token: str):
    """
    Authenticate WebSocket connection using token.
    This function creates its own database session to avoid connection pool issues.
    """
    db = None
    try:
        # Use the JWT decoding logic from jwt.py
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None

        # Create a new database session for this operation
        db = get_new_db_session()

        # Get user from database
        user = db.query(User).filter(User.username == username).first()
        if user is None or not user.is_active:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None

        return user
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    finally:
        # Always close the database session
        if db:
            db.close()


# WebSocket route for real-time messaging
@router.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket, token: str):
    # Authenticate the connection
    user = await get_user_from_token(websocket, token)
    if not user:
        # If authentication fails
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = user.id

    # Connect using the connection manager
    await manager.connect(user_id, websocket)

    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_json()

            # Validate the message structure
            if "receiver_id" not in data or "content" not in data:
                await websocket.send_json({"error": "Invalid message format"})
                continue

            receiver_id = int(data["receiver_id"])
            content = data["content"]

            # Use context manager for database operations
            try:
                with get_db_context() as db:
                    # Create and save the message to the database
                    db_message = DirectMessage(
                        content=content,
                        sender_id=user_id,
                        receiver_id=receiver_id,
                        created_at=datetime.now(),
                    )
                    db.add(db_message)
                    db.flush()  # Flush to get the ID without committing

                    # Prepare message data to send
                    message_data = {
                        "id": db_message.id,
                        "content": db_message.content,
                        "created_at": db_message.created_at.isoformat(),
                        "is_read": db_message.is_read,
                        "sender_id": db_message.sender_id,
                        "receiver_id": db_message.receiver_id,
                    }

                    # Send to the receiver if they are connected
                    was_delivered = await manager.send_personal_message(
                        message={"type": "new_message", "data": message_data},
                        user_id=receiver_id,
                    )

                    # Send confirmation back to the sender
                    await websocket.send_json(
                        {
                            "type": "message_status",
                            "data": {
                                "status": "delivered" if was_delivered else "sent",
                                "message": message_data,
                            },
                        }
                    )

            except Exception as db_error:
                print(f"Database error in WebSocket: {db_error}")
                await websocket.send_json({"error": "Failed to save message"})

    except WebSocketDisconnect:
        # Remove the connection when client disconnects
        manager.disconnect(user_id)
    except Exception:
        # Handle any other exceptions
        manager.disconnect(user_id)
        await websocket.close()
