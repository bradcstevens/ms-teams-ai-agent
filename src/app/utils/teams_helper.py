"""Teams-specific helper functions for message processing."""
import re
from typing import Optional
from botbuilder.schema import Activity


def extract_message_text(activity: Activity) -> str:
    """Extract clean message text from Teams activity.

    Handles @mentions and removes bot mentions from the message text.

    Args:
        activity: Bot Framework activity

    Returns:
        Clean message text without bot mentions
    """
    if not activity.text:
        return ""

    text = activity.text.strip()

    # Remove @mentions (Teams adds mentions as <at>botname</at>)
    # Pattern matches: <at>...</at>
    text = re.sub(r'<at>.*?</at>', '', text)

    # Clean up extra whitespace
    text = ' '.join(text.split())

    return text.strip()


def format_teams_response(text: str) -> str:
    """Format response text for Teams display.

    For MVP, this is a simple pass-through. In production, you might:
    - Convert markdown to Teams format
    - Add adaptive cards
    - Format code blocks appropriately

    Args:
        text: Response text from agent

    Returns:
        Formatted text for Teams
    """
    # For MVP, return text as-is
    # Teams supports basic markdown automatically
    return text


def is_direct_message(activity: Activity) -> bool:
    """Check if activity is a direct message vs. channel message.

    Args:
        activity: Bot Framework activity

    Returns:
        True if direct message, False if channel message
    """
    if not activity.conversation:
        return False

    # In Teams, personal conversations have conversationType set to "personal"
    return activity.conversation.conversation_type == "personal"


def extract_user_name(activity: Activity) -> Optional[str]:
    """Extract user's display name from activity.

    Args:
        activity: Bot Framework activity

    Returns:
        User's display name if available, None otherwise
    """
    if activity.from_property and activity.from_property.name:
        return activity.from_property.name
    return None


def sanitize_input(text: str, max_length: int = 4000) -> str:
    """Sanitize user input to prevent injection or overly long messages.

    Args:
        text: User input text
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "... [truncated]"

    # Remove any null bytes
    text = text.replace('\x00', '')

    return text.strip()
