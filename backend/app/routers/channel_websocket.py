from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from jose import jwt

from ..config import settings
from ..database import get_db_context, get_new_db_session
from ..models.channel import Channel, ChannelMessage
from ..models.user import User
from .channels import check_channel_membership

router = APIRouter()


# Connection Manager for Channel WebSockets
class ChannelConnectionManager:
    def __init__(self):
        # Dictionary to store active connections: {channel_id: {user_id: WebSocket}}
        self.channel_connections: Dict[int, Dict[int, WebSocket]] = {}

    async def connect(self, channel_id: int, user_id: int, websocket: WebSocket):
        """Register a new WebSocket connection for a user in a channel"""
        await websocket.accept()

        if channel_id not in self.channel_connections:
            self.channel_connections[channel_id] = {}

        self.channel_connections[channel_id][user_id] = websocket

    def disconnect(self, channel_id: int, user_id: int):
        """Remove a WebSocket connection for a user in a channel"""
        if channel_id in self.channel_connections:
            if user_id in self.channel_connections[channel_id]:
                del self.channel_connections[channel_id][user_id]

            # Clean up empty channel connections
            if not self.channel_connections[channel_id]:
                del self.channel_connections[channel_id]

    async def broadcast_to_channel(
        self, channel_id: int, message: dict, exclude_user_id: Optional[int] = None
    ):
        """Send a message to all users in a channel except the excluded one"""
        if channel_id not in self.channel_connections:
            return

        disconnected_users = []

        for user_id, connection in self.channel_connections[channel_id].items():
            if exclude_user_id is not None and user_id == exclude_user_id:
                continue

            try:
                await connection.send_json(message)
            except Exception:
                disconnected_users.append(user_id)

        # Clean up any disconnected users
        for user_id in disconnected_users:
            self.disconnect(channel_id, user_id)


# Initialize the channel connection manager
channel_manager = ChannelConnectionManager()


# Function to authenticate WebSocket connections for channels
async def get_user_from_token_channel(websocket: WebSocket, token: str):
    """
    Authenticate WebSocket connection using token for channels.
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


# WebSocket route for real-time channel messaging
@router.websocket("/{channel_id}/ws/")
async def channel_websocket_endpoint(websocket: WebSocket, channel_id: int, token: str):
    # Authenticate the connection
    user = await get_user_from_token_channel(websocket, token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = user.id

    # Check if user is a member of the channel
    try:
        with get_db_context() as db:
            if not check_channel_membership(db, channel_id, user_id):
                await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
                return
    except Exception:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return

    # Connect using the channel connection manager
    await channel_manager.connect(channel_id, user_id, websocket)

    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_json()

            # Validate the message structure
            if "content" not in data:
                await websocket.send_json({"error": "Invalid message format"})
                continue

            content = data["content"]

            # Use context manager for database operations
            try:
                with get_db_context() as db:
                    # Verify user is still a member
                    if not check_channel_membership(db, channel_id, user_id):
                        await websocket.send_json(
                            {"error": "No longer a member of this channel"}
                        )
                        break

                    # Create and save the message to the database
                    db_message = ChannelMessage(
                        content=content,
                        channel_id=channel_id,
                        sender_id=user_id,
                        created_at=datetime.now(),
                    )
                    db.add(db_message)
                    db.flush()  # Flush to get the ID without committing

                    # Update channel's updated_at timestamp
                    channel = db.query(Channel).filter(Channel.id == channel_id).first()
                    if channel:
                        channel.updated_at = datetime.now()

                    # Prepare message data to send
                    message_data = {
                        "id": db_message.id,
                        "content": db_message.content,
                        "created_at": db_message.created_at.isoformat(),
                        "channel_id": db_message.channel_id,
                        "sender_id": db_message.sender_id,
                        "sender": {
                            "id": user.id,
                            "username": user.username,
                            "avatar_url": user.avatar_url,
                            "full_name": user.full_name,
                        },
                    }

                    # Broadcast to all channel members except the sender
                    await channel_manager.broadcast_to_channel(
                        channel_id=channel_id,
                        message={"type": "new_channel_message", "data": message_data},
                        exclude_user_id=user_id,
                    )

                    # Send confirmation back to the sender
                    await websocket.send_json(
                        {
                            "type": "message_status",
                            "data": {
                                "status": "sent",
                                "message": message_data,
                            },
                        }
                    )

            except Exception as db_error:
                print(f"Database error in Channel WebSocket: {db_error}")
                await websocket.send_json({"error": "Failed to save message"})

    except WebSocketDisconnect:
        # Remove the connection when client disconnects
        channel_manager.disconnect(channel_id, user_id)
    except Exception:
        # Handle any other exceptions
        channel_manager.disconnect(channel_id, user_id)
        await websocket.close()
