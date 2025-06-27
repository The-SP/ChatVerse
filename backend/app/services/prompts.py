from langchain_core.prompts import ChatPromptTemplate

# Chat Summarization Prompts
CHAT_SUMMARY_SYSTEM_PROMPT = """You are a helpful assistant that summarizes chat conversations. 
Your job is to create clear, concise summaries that capture the main topics and important details."""

CHAT_SUMMARY_USER_PROMPT = """Please summarize the following conversation between users. The conversation contains the last {message_count} messages.

Conversation:
{conversation}

Instructions:
- Provide a concise summary of the main topics discussed
- Highlight any important decisions, action items, or key points
- Keep the summary clear and easy to understand
- If there are no meaningful topics (just greetings/casual chat), mention that
- Limit the summary to 2-3 paragraphs maximum

Summary:"""

# Create the prompt template
CHAT_SUMMARIZATION_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ("system", CHAT_SUMMARY_SYSTEM_PROMPT),
        ("human", CHAT_SUMMARY_USER_PROMPT),
    ]
)
