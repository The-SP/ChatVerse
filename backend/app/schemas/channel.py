# schemas/channel.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

from .user import UserResponse


class ChannelBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class ChannelCreate(ChannelBase):
    pass


class ChannelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class ChannelMemberInfo(BaseModel):
    user: UserResponse
    joined_at: datetime

    class Config:
        from_attributes = True


class ChannelResponse(ChannelBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: int
    creator: Optional[UserResponse] = None
    member_count: Optional[int] = None
    is_member: Optional[bool] = None

    class Config:
        from_attributes = True


class ChannelDetailResponse(ChannelResponse):
    members: List[ChannelMemberInfo] = []


class ChannelMessageBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class ChannelMessageCreate(ChannelMessageBase):
    pass


class ChannelMessageUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class ChannelMessageResponse(ChannelMessageBase):
    id: int
    created_at: datetime
    channel_id: int
    sender_id: int

    # Include sender information
    sender: Optional[UserResponse] = None

    class Config:
        from_attributes = True


class ChannelInviteCreate(BaseModel):
    user_ids: List[int] = Field(..., min_items=1, max_items=50)
