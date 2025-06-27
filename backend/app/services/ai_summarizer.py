from datetime import datetime
from typing import Dict, List

from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser

from ..config import settings
from ..logger import init_logger
from .prompts import CHAT_SUMMARIZATION_TEMPLATE

logger = init_logger(__name__)


class AIChatSummarizer:
    """AI-powered chat conversation summarizer using LangChain and Gemini."""

    def __init__(self):
        """Initialize the AI Chat Summarizer with LangChain."""
        try:
            self.llm = init_chat_model(
                model=settings.GEMINI_MODEL_NAME,
                api_key=settings.GEMINI_API_KEY,
                temperature=0.3,
            )

            self.prompt_template = CHAT_SUMMARIZATION_TEMPLATE

            # Create the summarization chain
            self.summarizer_chain = self.prompt_template | self.llm | StrOutputParser()

            logger.info("AI Chat Summarizer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize AI Chat Summarizer: {str(e)}")
            raise

    def format_messages_for_summary(self, messages: List[Dict]) -> str:
        """
        Format a list of message dictionaries into a readable conversation string.

        Args:
            messages: List of message dictionaries with sender and content information

        Returns:
            Formatted conversation string with timestamps and sender names
        """
        if not messages:
            return ""

        formatted_lines = []
        for msg in messages:
            # Extract sender name
            sender_name = "Unknown User"
            if msg.get("sender"):
                sender_name = msg["sender"].get("full_name") or msg["sender"].get(
                    "username", "Unknown User"
                )

            # Format timestamp
            try:
                created_at = msg.get("created_at")
                if isinstance(created_at, str):
                    timestamp = datetime.fromisoformat(created_at)
                else:
                    timestamp = created_at
                time_str = timestamp.strftime("%H:%M")
            except Exception:
                time_str = "00:00"

            # Format message content
            content = msg.get("content", "").strip()
            if content:
                formatted_lines.append(f"[{time_str}] {sender_name}: {content}")

        return "\n".join(formatted_lines)

    async def summarize_conversation(
        self,
        messages: List[Dict],
    ) -> Dict[str, any]:
        """
        Generate an AI summary of a conversation between two users.

        Args:
            messages: List of message dictionaries to summarize

        Returns:
            Dictionary containing success status, summary text, and metadata
        """
        try:
            if not messages:
                return {
                    "success": False,
                    "error": "No messages to summarize",
                    "summary": None,
                }

            # Format messages for AI processing
            formatted_conversation = self.format_messages_for_summary(messages)

            if not formatted_conversation.strip():
                return {
                    "success": False,
                    "error": "No valid message content found",
                    "summary": None,
                }

            actual_count = len(messages)
            logger.info(f"Generating summary for {actual_count} messages")

            # Generate summary using the chain
            summary = await self.summarizer_chain.ainvoke(
                {"conversation": formatted_conversation, "message_count": actual_count}
            )

            if not summary or not summary.strip():
                return {
                    "success": False,
                    "error": "AI model returned empty response",
                    "summary": None,
                }

            logger.info("Summary generated successfully")
            return {
                "success": True,
                "summary": summary.strip(),
                "message_count": len(messages),
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "model_used": settings.GEMINI_MODEL_NAME,
            }
        except Exception as e:
            logger.error(f"Failed to summarize conversation: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to generate summary: {str(e)}",
                "summary": None,
            }


ai_chat_summarizer = AIChatSummarizer()
