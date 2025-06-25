from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..database import get_db_context
from ..models.direct_message import DirectMessage
from .websocket_manager import authenticate_websocket_user, connection_manager

router = APIRouter()


@router.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    WebSocket endpoint for real-time messaging.

    Query parameters:
    - token: JWT authentication token
    """
    # Authenticate the connection
    user = await authenticate_websocket_user(websocket, token)
    if not user:
        return

    user_id = user.id

    # Connect using the connection manager
    await connection_manager.connect(user_id, websocket)

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
                    was_delivered = await connection_manager.send_personal_message(
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
        connection_manager.disconnect(user_id)
    except Exception:
        # Handle any other exceptions
        connection_manager.disconnect(user_id)
        await websocket.close()
