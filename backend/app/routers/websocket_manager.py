from typing import Dict, Optional

from fastapi import WebSocket, status
from jose import jwt

from ..config import settings
from ..database import get_new_db_session
from ..logger import init_logger
from ..models.user import User

logger = init_logger(__name__)


class ConnectionManager:
    def __init__(self):
        # Dictionary to store active connections: {user_id: WebSocket}
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        """Register a new WebSocket connection for a user"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected for user: {user_id}")

    def disconnect(self, user_id: int):
        """Remove a WebSocket connection for a user"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"WebSocket disconnected for user: {user_id}")

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

    def get_connected_users(self) -> list[int]:
        """Get list of currently connected user IDs"""
        return list(self.active_connections.keys())

    def is_user_connected(self, user_id: int) -> bool:
        """Check if a specific user is currently connected"""
        return user_id in self.active_connections


async def authenticate_websocket_user(
    websocket: WebSocket, token: str
) -> Optional[User]:
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
            logger.warning("WebSocket authentication failed: No username in token")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None

        # Create a new database session for this operation
        db = get_new_db_session()

        # Get user from database
        user = db.query(User).filter(User.username == username).first()
        if user is None or not user.is_active:
            logger.warning(f"WebSocket authentication failed: Invalid user {username}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None

        return user
    except Exception as e:
        logger.warning(f"WebSocket authentication failed: {str(e)}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    finally:
        # Always close the database session
        if db:
            db.close()


# Global connection manager instance
connection_manager = ConnectionManager()
