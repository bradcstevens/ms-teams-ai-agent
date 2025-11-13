"""Conversation state management for Teams bot."""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from threading import Lock

from app.config.settings import settings
from app.telemetry.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ConversationContext:
    """Conversation context for a single conversation."""

    conversation_id: str
    thread_id: Optional[str] = None
    user_id: Optional[str] = None
    last_activity: datetime = field(default_factory=datetime.utcnow)
    message_count: int = 0
    metadata: Dict[str, str] = field(default_factory=dict)

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
        self.message_count += 1


class ConversationStore:
    """In-memory conversation state store.

    Note: For production with multiple instances, migrate to Azure Redis Cache
    or Azure Cosmos DB for distributed state management.
    """

    def __init__(self):
        """Initialize conversation store."""
        self._conversations: Dict[str, ConversationContext] = {}
        self._lock = Lock()
        logger.info("ConversationStore initialized (in-memory)")

    def get_or_create(self, conversation_id: str, user_id: Optional[str] = None) -> ConversationContext:
        """Get existing conversation context or create new one.

        Args:
            conversation_id: Unique conversation identifier
            user_id: Optional user identifier

        Returns:
            ConversationContext for the conversation
        """
        with self._lock:
            if conversation_id not in self._conversations:
                context = ConversationContext(
                    conversation_id=conversation_id,
                    user_id=user_id
                )
                self._conversations[conversation_id] = context
                logger.info(
                    "Created new conversation context",
                    properties={
                        "conversation_id": conversation_id,
                        "user_id": user_id
                    }
                )
            else:
                context = self._conversations[conversation_id]
                context.update_activity()

            return context

    def get(self, conversation_id: str) -> Optional[ConversationContext]:
        """Get conversation context if exists.

        Args:
            conversation_id: Unique conversation identifier

        Returns:
            ConversationContext if exists, None otherwise
        """
        with self._lock:
            return self._conversations.get(conversation_id)

    def update_thread_id(self, conversation_id: str, thread_id: str):
        """Update thread ID for conversation.

        Args:
            conversation_id: Unique conversation identifier
            thread_id: Agent framework thread ID
        """
        with self._lock:
            if conversation_id in self._conversations:
                self._conversations[conversation_id].thread_id = thread_id
                logger.debug(
                    "Updated thread ID for conversation",
                    properties={
                        "conversation_id": conversation_id,
                        "thread_id": thread_id
                    }
                )

    def cleanup_expired(self):
        """Remove expired conversation contexts.

        Conversations are considered expired after configured timeout.
        """
        timeout = timedelta(minutes=settings.conversation_timeout_minutes)
        cutoff_time = datetime.utcnow() - timeout

        with self._lock:
            expired = [
                conv_id
                for conv_id, context in self._conversations.items()
                if context.last_activity < cutoff_time
            ]

            for conv_id in expired:
                del self._conversations[conv_id]

            if expired:
                logger.info(
                    "Cleaned up expired conversations",
                    properties={"count": len(expired)}
                )

    def get_stats(self) -> Dict[str, int]:
        """Get conversation store statistics.

        Returns:
            Dictionary with statistics
        """
        with self._lock:
            return {
                "total_conversations": len(self._conversations),
                "active_threads": sum(
                    1 for c in self._conversations.values() if c.thread_id
                )
            }


# Global conversation store instance
_conversation_store: Optional[ConversationStore] = None


def get_conversation_store() -> ConversationStore:
    """Get or create global conversation store instance.

    Returns:
        ConversationStore instance
    """
    global _conversation_store
    if _conversation_store is None:
        _conversation_store = ConversationStore()
    return _conversation_store
