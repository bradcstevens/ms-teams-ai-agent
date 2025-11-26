"""Azure OpenAI agent using Microsoft Agent Framework."""
from typing import Optional, Callable
from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import DefaultAzureCredential, AzureCliCredential, get_bearer_token_provider
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential

from app.config.settings import settings
from app.telemetry.logger import get_logger

logger = get_logger(__name__)


class TeamsAIAgent:
    """Teams AI Agent wrapper using Microsoft Agent Framework."""

    def __init__(self):
        """Initialize the Teams AI Agent."""
        self._agent: Optional[ChatAgent] = None
        self._credential = None
        self._token_provider: Optional[Callable] = None

    async def initialize(self):
        """Initialize the agent with Azure OpenAI client.

        Uses DefaultAzureCredential for managed identity authentication
        in production, or AzureCliCredential for local development.
        """
        try:
            # Choose credential based on environment
            if settings.is_production:
                logger.info("Initializing agent with DefaultAzureCredential (production)")
                self._credential = DefaultAzureCredential()
            else:
                logger.info("Initializing agent with AzureCliCredential (development)")
                self._credential = AzureCliCredential()

            # Create token provider for Azure OpenAI
            self._token_provider = get_bearer_token_provider(
                self._credential,
                "https://cognitiveservices.azure.com/.default"
            )

            # Create Azure OpenAI chat client
            chat_client = AzureOpenAIChatClient(
                endpoint=settings.azure_openai_endpoint,
                ad_token_provider=self._token_provider,
                deployment_name=settings.azure_openai_deployment_name,
                api_version=settings.azure_openai_api_version
            )

            # Create the agent
            self._agent = ChatAgent(
                chat_client=chat_client,
                name=settings.agent_name,
                instructions=settings.agent_instructions
            )

            logger.info(
                "Agent initialized successfully",
                properties={
                    "agent_name": settings.agent_name,
                    "endpoint": settings.azure_openai_endpoint,
                    "deployment": settings.azure_openai_deployment_name
                }
            )

        except Exception as e:
            logger.error(
                "Failed to initialize agent",
                properties={"error": str(e)}
            )
            raise

    async def run(
        self,
        message: str,
        thread_id: Optional[str] = None
    ) -> str:
        """Run the agent with a message.

        Args:
            message: User message to process
            thread_id: Optional conversation thread ID for context

        Returns:
            Agent response text

        Raises:
            ValueError: If agent not initialized
            Exception: If agent execution fails
        """
        if not self._agent:
            raise ValueError("Agent not initialized. Call initialize() first.")

        try:
            logger.info(
                "Processing message",
                properties={
                    "message_length": len(message),
                    "has_thread": thread_id is not None
                }
            )

            # Get or create thread
            if thread_id:
                thread = self._agent.get_thread(thread_id)
            else:
                thread = self._agent.get_new_thread()

            # Run agent
            result = await self._agent.run(message, thread=thread)

            logger.info(
                "Agent response generated",
                properties={
                    "response_length": len(result.text),
                    "thread_id": thread.id
                }
            )

            return result.text

        except Exception as e:
            logger.error(
                "Agent execution failed",
                properties={
                    "error": str(e),
                    "message_preview": message[:100]
                }
            )
            raise

    async def run_streaming(
        self,
        message: str,
        thread_id: Optional[str] = None
    ):
        """Run the agent with streaming response.

        Args:
            message: User message to process
            thread_id: Optional conversation thread ID for context

        Yields:
            Response chunks as they are generated

        Raises:
            ValueError: If agent not initialized
            Exception: If agent execution fails
        """
        if not self._agent:
            raise ValueError("Agent not initialized. Call initialize() first.")

        try:
            logger.info(
                "Processing message with streaming",
                properties={
                    "message_length": len(message),
                    "has_thread": thread_id is not None
                }
            )

            # Get or create thread
            if thread_id:
                thread = self._agent.get_thread(thread_id)
            else:
                thread = self._agent.get_new_thread()

            # Stream agent response
            async for chunk in self._agent.run_stream(message, thread=thread):
                yield chunk

            logger.info(
                "Streaming response completed",
                properties={"thread_id": thread.id}
            )

        except Exception as e:
            logger.error(
                "Streaming agent execution failed",
                properties={
                    "error": str(e),
                    "message_preview": message[:100]
                }
            )
            raise

    async def cleanup(self):
        """Cleanup resources."""
        if self._credential and hasattr(self._credential, 'close'):
            await self._credential.close()
        logger.info("Agent resources cleaned up")


# Global agent instance
_agent_instance: Optional[TeamsAIAgent] = None


async def get_agent() -> TeamsAIAgent:
    """Get or create the global agent instance.

    Returns:
        TeamsAIAgent instance
    """
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = TeamsAIAgent()
        await _agent_instance.initialize()
    return _agent_instance
