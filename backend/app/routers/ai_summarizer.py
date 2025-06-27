from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth.jwt import get_current_active_user
from ..database import get_db
from ..logger import init_logger
from ..models.direct_message import DirectMessage
from ..models.user import User
from ..services.ai_summarizer import ai_chat_summarizer

logger = init_logger(__name__)
router = APIRouter()


class SummarizeRequest(BaseModel):
    other_user_id: int = Field(
        ..., description="ID of the other user in the conversation"
    )
    message_count: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of recent messages to summarize (1-50)",
    )


class SummarizeResponse(BaseModel):
    success: bool
    summary: Optional[str] = None
    message_count: int
    conversation_partner: str
    generated_at: str
    model_used: str
    error: Optional[str] = None


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_conversation(
    request: SummarizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate an AI summary of the last N messages between the current user and another user.

    - **other_user_id**: ID of the other user in the conversation
    - **message_count**: Number of recent messages to include (default: 10, max: 50)

    Returns a summary of the conversation including key topics and important points.
    """
    try:
        # Validate that the other user exists
        other_user = db.query(User).filter(User.id == request.other_user_id).first()
        if not other_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {request.other_user_id} not found",
            )

        # Prevent users from summarizing conversations with themselves
        if current_user.id == request.other_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot summarize conversation with yourself",
            )

        # Fetch the most recent messages between the two users
        messages = (
            db.query(DirectMessage)
            .filter(
                (
                    (DirectMessage.sender_id == current_user.id)
                    & (DirectMessage.receiver_id == request.other_user_id)
                )
                | (
                    (DirectMessage.sender_id == request.other_user_id)
                    & (DirectMessage.receiver_id == current_user.id)
                )
            )
            .order_by(DirectMessage.created_at.desc())
            .limit(request.message_count)
            .all()
        )

        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No messages found between these users",
            )

        # Reverse the messages to get chronological order for summarization
        messages.reverse()

        # Convert messages to the format expected by the AI summarizer
        formatted_messages = []
        for msg in messages:
            # Determine sender info
            if msg.sender_id == current_user.id:
                sender_info = {
                    "full_name": current_user.full_name,
                    "username": current_user.username,
                }
            else:
                sender_info = {
                    "full_name": other_user.full_name,
                    "username": other_user.username,
                }

            formatted_messages.append(
                {
                    "id": msg.id,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat()
                    if msg.created_at
                    else None,
                    "sender_id": msg.sender_id,
                    "receiver_id": msg.receiver_id,
                    "sender": sender_info,
                }
            )

        # Generate AI summary
        summary_result = await ai_chat_summarizer.summarize_conversation(
            formatted_messages
        )

        # Determine conversation partner name
        partner_name = other_user.full_name or other_user.username

        if summary_result["success"]:
            logger.info(
                f"Successfully generated summary for conversation between "
                f"user {current_user.id} and user {request.other_user_id}"
            )

            return SummarizeResponse(
                success=True,
                summary=summary_result["summary"],
                message_count=len(messages),
                conversation_partner=partner_name,
                generated_at=summary_result["generated_at"],
                model_used=summary_result["model_used"],
            )
        else:
            logger.error(f"Failed to generate summary: {summary_result['error']}")

            return SummarizeResponse(
                success=False,
                summary=None,
                message_count=len(messages),
                conversation_partner=partner_name,
                generated_at="",
                model_used="",
                error=summary_result["error"],
            )
    except Exception as e:
        logger.error(f"Unexpected error in summarize_conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the summary",
        )
