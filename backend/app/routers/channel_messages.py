from datetime import datetime
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session, joinedload

from ..auth.jwt import get_current_user
from ..database import get_db
from ..models.channel import Channel, ChannelMessage
from ..models.user import User
from ..schemas.channel import (
    ChannelMessageCreate,
    ChannelMessageResponse,
    ChannelMessageUpdate,
)
from .channels import check_channel_membership
from .channel_websocket import channel_manager

router = APIRouter()


# Channel message CRUD operations
@router.post(
    "/{channel_id}/messages",
    response_model=ChannelMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_channel_message(
    channel_id: int,
    message_data: ChannelMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message to a channel"""
    # Check if channel exists
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    # Check if user is a member
    if not check_channel_membership(db, channel_id, current_user.id):
        raise HTTPException(
            status_code=403, detail="You are not a member of this channel"
        )

    # Create the message
    db_message = ChannelMessage(
        content=message_data.content,
        channel_id=channel_id,
        sender_id=current_user.id,
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    # Load sender information
    db_message.sender = current_user

    # Update channel's updated_at timestamp
    channel.updated_at = datetime.now()
    db.commit()

    # Prepare message data for WebSocket broadcast
    message_dict = {
        "id": db_message.id,
        "content": db_message.content,
        "created_at": db_message.created_at.isoformat(),
        "channel_id": db_message.channel_id,
        "sender_id": db_message.sender_id,
        "sender": {
            "id": current_user.id,
            "username": current_user.username,
            "avatar_url": current_user.avatar_url,
            "full_name": current_user.full_name,
        },
    }

    # Broadcast to all channel members except the sender
    await channel_manager.broadcast_to_channel(
        channel_id=channel_id,
        message={"type": "new_channel_message", "data": message_dict},
        exclude_user_id=current_user.id,
    )

    return db_message


@router.get("/{channel_id}/messages", response_model=List[ChannelMessageResponse])
async def get_channel_messages(
    channel_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get messages from a channel"""
    # Check if channel exists
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    # Check if user is a member
    if not check_channel_membership(db, channel_id, current_user.id):
        raise HTTPException(
            status_code=403, detail="You are not a member of this channel"
        )

    # Get messages with sender information
    messages = (
        db.query(ChannelMessage)
        .options(joinedload(ChannelMessage.sender))
        .filter(ChannelMessage.channel_id == channel_id)
        .order_by(ChannelMessage.created_at)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return messages


@router.put(
    "/{channel_id}/messages/{message_id}", response_model=ChannelMessageResponse
)
async def update_channel_message(
    channel_id: int,
    message_id: int,
    message_data: ChannelMessageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a channel message (only the sender can update)"""
    # Get the message
    message = (
        db.query(ChannelMessage)
        .options(joinedload(ChannelMessage.sender))
        .filter(
            ChannelMessage.id == message_id, ChannelMessage.channel_id == channel_id
        )
        .first()
    )

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Check if user is the sender
    if message.sender_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="You can only edit your own messages"
        )

    # Update the message
    message.content = message_data.content
    db.commit()
    db.refresh(message)

    # Prepare message data for WebSocket broadcast
    message_dict = {
        "id": message.id,
        "content": message.content,
        "created_at": message.created_at.isoformat(),
        "channel_id": message.channel_id,
        "sender_id": message.sender_id,
        "sender": {
            "id": message.sender.id,
            "username": message.sender.username,
            "avatar_url": message.sender.avatar_url,
            "full_name": message.sender.full_name,
        },
    }

    # Broadcast the update to all channel members
    await channel_manager.broadcast_to_channel(
        channel_id=channel_id,
        message={"type": "channel_message_updated", "data": message_dict},
    )

    return message


@router.delete("/{channel_id}/messages/{message_id}")
async def delete_channel_message(
    channel_id: int,
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a channel message (sender can delete their own message)"""
    # Get the message
    message = (
        db.query(ChannelMessage)
        .filter(
            ChannelMessage.id == message_id, ChannelMessage.channel_id == channel_id
        )
        .first()
    )

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Check if user is the sender (removed role-based permissions)
    if message.sender_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="You can only delete your own messages"
        )

    # Delete the message
    db.delete(message)
    db.commit()

    # Broadcast the deletion to all channel members
    await channel_manager.broadcast_to_channel(
        channel_id=channel_id,
        message={
            "type": "channel_message_deleted",
            "data": {"message_id": message_id, "channel_id": channel_id},
        },
    )

    return {"status": "success", "message": "Message deleted successfully"}
