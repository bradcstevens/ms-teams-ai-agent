"""FastAPI application for Teams AI Agent."""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from botbuilder.core import BotFrameworkAdapterSettings, BotFrameworkAdapter
from botbuilder.schema import Activity

from app.config.settings import settings
from app.bot.teams_bot import TeamsBot
from app.agent.ai_agent import get_agent
from app.bot.conversation_state import get_conversation_store
from app.telemetry.logger import get_logger, configure_tracing

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info("Starting Teams AI Agent application")

    # Configure tracing
    configure_tracing()

    # Initialize agent
    try:
        agent = await get_agent()
        logger.info("Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        raise

    # Start background task for conversation cleanup
    cleanup_task = asyncio.create_task(periodic_cleanup())

    yield

    # Shutdown
    logger.info("Shutting down Teams AI Agent application")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

    # Cleanup agent resources
    if agent:
        await agent.cleanup()

# Create FastAPI app
app = FastAPI(
    title="Teams AI Agent",
    description="AI Agent for Microsoft Teams using Microsoft Agent Framework",
    version="1.0.0",
    lifespan=lifespan
)

# Bot Framework adapter settings
adapter_settings = BotFrameworkAdapterSettings(
    app_id=settings.bot_id,
    app_password=settings.bot_password or ""
)

# Create Bot Framework adapter
bot_adapter = BotFrameworkAdapter(adapter_settings)

# Create bot instance
bot = TeamsBot()


# Error handler
async def on_error(context, error):
    """Handle adapter errors.

    Args:
        context: Turn context
        error: Exception that occurred
    """
    logger.error(
        f"Bot adapter error: {error}",
        properties={
            "conversation_id": context.activity.conversation.id if context.activity else "unknown"
        }
    )
    await context.send_activity("Sorry, something went wrong. Please try again.")

bot_adapter.on_turn_error = on_error


@app.get("/health")
async def health_check():
    """Health check endpoint for Container Apps.

    Returns:
        JSON response with health status
    """
    try:
        # Check if agent is initialized
        agent = await get_agent()
        conversation_store = get_conversation_store()
        stats = conversation_store.get_stats()

        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "service": "teams-ai-agent",
                "agent_initialized": agent is not None,
                "conversations": stats
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.get("/")
async def root():
    """Root endpoint.

    Returns:
        JSON response with service information
    """
    return {
        "service": "Teams AI Agent",
        "version": "1.0.0",
        "status": "running"
    }


@app.post("/api/messages")
async def messages(request: Request):
    """Bot Framework messages endpoint.

    This endpoint receives activities from Teams via Bot Service.

    Args:
        request: FastAPI request object

    Returns:
        Response with status code
    """
    try:
        # Get request body
        body = await request.json()

        # Create activity from request
        activity = Activity().deserialize(body)

        # Get auth header
        auth_header = request.headers.get("Authorization", "")

        # Process activity through adapter
        await bot_adapter.process_activity(activity, auth_header, bot.on_turn)

        return Response(status_code=200)

    except Exception as e:
        logger.error(
            "Error processing activity",
            properties={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def periodic_cleanup():
    """Periodic task to cleanup expired conversations.

    Runs every 10 minutes to remove expired conversation contexts.
    """
    conversation_store = get_conversation_store()

    while True:
        try:
            await asyncio.sleep(600)  # 10 minutes
            conversation_store.cleanup_expired()
            logger.debug("Periodic conversation cleanup completed")
        except asyncio.CancelledError:
            logger.info("Periodic cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        log_level=settings.log_level.lower(),
        reload=not settings.is_production
    )
