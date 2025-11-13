"""Teams bot adapter and activity handler."""
from typing import Optional
from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from botbuilder.schema import Activity, ActivityTypes, ChannelAccount

from app.agent.ai_agent import get_agent
from app.bot.conversation_state import get_conversation_store
from app.telemetry.logger import get_logger
from app.utils.teams_helper import extract_message_text, format_teams_response

logger = get_logger(__name__)


class TeamsBot(ActivityHandler):
    """Teams bot activity handler integrated with AI agent."""

    def __init__(self):
        """Initialize Teams bot handler."""
        super().__init__()
        self.conversation_store = get_conversation_store()
        logger.info("TeamsBot initialized")

    async def on_message_activity(self, turn_context: TurnContext):
        """Handle incoming message activities.

        Args:
            turn_context: Turn context containing the incoming activity
        """
        try:
            # Extract message text (handle @mentions)
            message_text = extract_message_text(turn_context.activity)

            if not message_text or not message_text.strip():
                logger.warning("Received empty message")
                return

            # Get conversation context
            conversation_id = turn_context.activity.conversation.id
            user_id = turn_context.activity.from_property.id if turn_context.activity.from_property else None

            context = self.conversation_store.get_or_create(conversation_id, user_id)

            logger.info(
                "Processing message",
                properties={
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "message_count": context.message_count,
                    "has_thread": context.thread_id is not None
                }
            )

            # Send typing indicator
            await self._send_typing_indicator(turn_context)

            # Get agent and process message
            agent = await get_agent()
            response_text = await agent.run(
                message=message_text,
                thread_id=context.thread_id
            )

            # Update thread ID if this is first message
            # Note: Agent Framework manages thread internally
            # We track it in conversation store for reference
            if not context.thread_id:
                # In production, extract thread_id from agent response
                # For MVP, we'll generate one from conversation_id
                context.thread_id = f"thread-{conversation_id}"
                self.conversation_store.update_thread_id(conversation_id, context.thread_id)

            # Format and send response
            formatted_response = format_teams_response(response_text)
            await turn_context.send_activity(MessageFactory.text(formatted_response))

            logger.info(
                "Message processed successfully",
                properties={
                    "conversation_id": conversation_id,
                    "response_length": len(response_text)
                }
            )

        except Exception as e:
            logger.error(
                "Error processing message",
                properties={
                    "conversation_id": turn_context.activity.conversation.id if turn_context.activity else "unknown",
                    "error": str(e)
                }
            )
            # Send user-friendly error message
            error_message = (
                "I apologize, but I encountered an error processing your message. "
                "Please try again in a moment."
            )
            await turn_context.send_activity(MessageFactory.text(error_message))

    async def on_conversation_update_activity(self, turn_context: TurnContext):
        """Handle conversation update activities (bot added to conversation).

        Args:
            turn_context: Turn context containing the conversation update activity
        """
        try:
            if turn_context.activity.members_added:
                for member in turn_context.activity.members_added:
                    # Check if bot was added
                    if member.id != turn_context.activity.recipient.id:
                        welcome_message = (
                            f"Hello! I'm {turn_context.activity.recipient.name}, "
                            "your AI assistant. How can I help you today?"
                        )
                        await turn_context.send_activity(MessageFactory.text(welcome_message))
                        logger.info(
                            "Sent welcome message",
                            properties={"conversation_id": turn_context.activity.conversation.id}
                        )
        except Exception as e:
            logger.error(
                "Error handling conversation update",
                properties={"error": str(e)}
            )

    async def on_teams_members_added(self, members_added: list[ChannelAccount], turn_context: TurnContext):
        """Handle Teams-specific members added event.

        Args:
            members_added: List of members added to the conversation
            turn_context: Turn context
        """
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    MessageFactory.text(
                        f"Welcome to the conversation! I'm here to help. "
                        f"Feel free to ask me anything."
                    )
                )

    async def _send_typing_indicator(self, turn_context: TurnContext):
        """Send typing indicator to show bot is processing.

        Args:
            turn_context: Turn context
        """
        try:
            typing_activity = Activity(
                type=ActivityTypes.typing,
                relates_to=turn_context.activity.relates_to
            )
            await turn_context.send_activity(typing_activity)
        except Exception as e:
            # Typing indicator is non-critical, log but don't fail
            logger.debug(f"Failed to send typing indicator: {e}")
