from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import and_, func
from sqlalchemy.orm import Session, joinedload

from ..auth.jwt import get_current_user
from ..database import get_db
from ..models.channel import Channel, channel_members
from ..models.user import User
from ..schemas.channel import (
    ChannelCreate,
    ChannelDetailResponse,
    ChannelInviteCreate,
    ChannelResponse,
)

router = APIRouter()


def check_channel_membership(db: Session, channel_id: int, user_id: int):
    """Check if user is a member of the channel"""
    membership = (
        db.query(channel_members)
        .filter(
            and_(
                channel_members.c.channel_id == channel_id,
                channel_members.c.user_id == user_id,
            )
        )
        .first()
    )
    return membership


# Channel CRUD operations
@router.post("/", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    channel_data: ChannelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new channel"""
    # Create the channel
    db_channel = Channel(
        name=channel_data.name,
        created_by=current_user.id,
    )
    db.add(db_channel)
    db.flush()  # Get the ID without committing

    # Add creator as a member
    db.execute(
        channel_members.insert().values(
            user_id=current_user.id,
            channel_id=db_channel.id,
        )
    )

    db.commit()
    db.refresh(db_channel)

    return db_channel


@router.get("/", response_model=List[ChannelResponse])
async def get_user_channels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all channels the user is a member of"""
    channels = (
        db.query(Channel)
        .join(channel_members)
        .filter(channel_members.c.user_id == current_user.id)
        .options(joinedload(Channel.creator))
        .order_by(Channel.updated_at.desc())
        .all()
    )

    result = []
    for channel in channels:
        # Get member count
        member_count = (
            db.query(func.count(channel_members.c.user_id))
            .filter(channel_members.c.channel_id == channel.id)
            .scalar()
        )

        channel_dict = {
            **channel.__dict__,
            "member_count": member_count,
            "is_member": True,
        }
        result.append(channel_dict)

    return result


@router.get("/{channel_id}", response_model=ChannelDetailResponse)
async def get_channel(
    channel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get channel details"""
    channel = (
        db.query(Channel)
        .options(joinedload(Channel.creator))
        .filter(Channel.id == channel_id)
        .first()
    )

    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    # Check if user is a member
    if not check_channel_membership(db, channel_id, current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    # Get members
    members_query = (
        db.query(User, channel_members.c.joined_at)
        .join(channel_members, User.id == channel_members.c.user_id)
        .filter(channel_members.c.channel_id == channel_id)
        .order_by(channel_members.c.joined_at)
    )

    members = []
    for user, joined_at in members_query:
        members.append(
            {
                "user": user,
                "joined_at": joined_at,
            }
        )

    return {
        **channel.__dict__,
        "members": members,
        "member_count": len(members),
        "is_member": True,
    }


@router.post("/{channel_id}/join")
async def join_channel(
    channel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Join a channel"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    # Check if already a member
    if check_channel_membership(db, channel_id, current_user.id):
        raise HTTPException(status_code=400, detail="Already a member of this channel")

    # Add user as member
    db.execute(
        channel_members.insert().values(
            user_id=current_user.id,
            channel_id=channel_id,
        )
    )
    db.commit()

    return {"status": "success", "message": "Joined channel successfully"}


@router.post("/{channel_id}/invite")
async def invite_users(
    channel_id: int,
    invite_data: ChannelInviteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Invite users to a channel (only members can invite)"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    # Check if current user is a member
    if not check_channel_membership(db, channel_id, current_user.id):
        raise HTTPException(status_code=403, detail="Not a member of this channel")

    # Check if users exist and are not already members
    users_to_invite = []
    for user_id in invite_data.user_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            continue  # Skip non-existent users

        if not check_channel_membership(db, channel_id, user_id):
            users_to_invite.append(user_id)

    # Add users to channel
    if users_to_invite:
        for user_id in users_to_invite:
            db.execute(
                channel_members.insert().values(
                    user_id=user_id,
                    channel_id=channel_id,
                )
            )
        db.commit()

    return {
        "status": "success",
        "message": f"Invited {len(users_to_invite)} users to channel",
        "invited_count": len(users_to_invite),
    }
