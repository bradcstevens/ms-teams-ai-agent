# Teams AI Agent - Agent Implementation

Python AI Agent implementation using Microsoft Agent Framework for Microsoft Teams integration.

## Architecture

```
src/
├── app/
│   ├── agent/          # AI agent implementation
│   │   ├── ai_agent.py # Azure OpenAI agent with Agent Framework
│   │   └── __init__.py
│   ├── bot/            # Bot Framework integration
│   │   ├── teams_bot.py           # Teams bot activity handler
│   │   ├── conversation_state.py  # Conversation state management
│   │   └── __init__.py
│   ├── config/         # Configuration and settings
│   │   ├── settings.py # Pydantic settings from environment
│   │   └── __init__.py
│   ├── mcp/            # MCP (Model Context Protocol) integration
│   │   ├── config.py   # Pydantic configuration models
│   │   ├── loader.py   # Configuration file loader
│   │   ├── README.md   # MCP integration documentation
│   │   └── __init__.py
│   ├── telemetry/      # Logging and Application Insights
│   │   ├── logger.py   # Structured logging with AI integration
│   │   └── __init__.py
│   ├── utils/          # Helper utilities
│   │   ├── teams_helper.py  # Teams message formatting
│   │   └── __init__.py
│   └── main.py         # FastAPI application entry point
├── tests/              # Unit and integration tests
│   ├── test_mcp_config.py  # MCP configuration tests
│   └── ...
├── requirements.txt    # Python dependencies
├── Dockerfile          # Multi-stage container build
├── .env.example        # Environment variable template
├── mcp_servers.json.example  # MCP configuration example
└── README.md           # This file
```

## Features Implemented

### Microsoft Agent Framework
- Azure OpenAI ChatAgent with DefaultAzureCredential
- Support for both managed identity (production) and Azure CLI (development)
- Conversation thread management
- Streaming response support (prepared for future use)

### Bot Framework Adapter
- BotFrameworkAdapter with Teams authentication
- Activity handler for message and conversation update events
- Welcome messages for new users
- Typing indicators during processing

### FastAPI Webhook Application
- `/api/messages` endpoint with Bot Framework authentication
- `/health` endpoint for Container Apps health checks
- Error handling middleware
- Structured logging integration

### Conversation State Management
- In-memory conversation store with thread tracking
- Automatic cleanup of expired conversations (30-minute timeout)
- Thread context persistence across messages
- Migration path documented for Redis/Cosmos DB

### Azure OpenAI Integration
- Integrated through Microsoft Agent Framework
- Managed identity authentication
- Automatic retry logic (handled by Agent Framework)
- Error handling with user-friendly messages

### Teams Message Formatting
- @mention handling and text extraction
- Direct vs. channel message detection
- Input sanitization and validation
- Teams-compatible response formatting

### Error Handling & Telemetry
- Application Insights integration with OpenCensus
- Structured logging with correlation IDs
- Exception handlers at all levels
- User-friendly error messages for Teams

### Container Packaging
- Multi-stage Dockerfile with Python 3.11
- Non-root user execution
- Health check endpoint validation
- Optimized image size with slim base

### MCP Configuration Schema & Loader
- Pydantic models for MCP server configuration validation
- JSON schema support for `mcp_servers.json`
- Environment variable substitution (${VAR_NAME} syntax)
- Server registry with enable/disable flags
- Support for STDIO and SSE transport types
- Comprehensive error handling and validation
- Complete test coverage

## Local Development Setup

### Prerequisites

1. Python 3.11 or later
2. Azure CLI (`az login` authenticated)
3. Azure OpenAI resource with GPT-5 deployment
4. Bot Service registration (can be created later for testing)

### Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your Azure resource values
nano .env
```

### Configuration

#### Required Environment Variables

```bash
# Azure OpenAI (from infrastructure deployment)
AZURE_OPENAI_ENDPOINT=https://oai-<env>-<token>.openai.azure.com
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Bot Service (from infrastructure deployment)
BOT_ID=<your-bot-app-id>
BOT_PASSWORD=  # Empty for managed identity

# Application Insights (from infrastructure deployment)
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...
```

#### MCP Server Configuration (Optional)

The agent supports Model Context Protocol (MCP) servers for extended capabilities:

```bash
# Copy example configuration
cp mcp_servers.json.example mcp_servers.json

# Edit configuration with your MCP servers
nano mcp_servers.json
```

See [MCP Integration Documentation](app/mcp/README.md) for detailed configuration options.

Example MCP server configuration:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
      "transport": "stdio",
      "enabled": true
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      },
      "transport": "stdio",
      "enabled": true
    }
  }
}
```

### Running Locally

```bash
# Run with uvicorn directly
python -m uvicorn app.main:app --reload --port 8000

# Or use the main module
python -m app.main
```

### Testing with Bot Framework Emulator

1. Download [Bot Framework Emulator](https://github.com/Microsoft/BotFramework-Emulator/releases)
2. Start the local application (port 8000)
3. Connect to `http://localhost:8000/api/messages`
4. Enter Bot ID and leave password empty for local testing

### Testing with ngrok (Teams Integration)

```bash
# Install ngrok
brew install ngrok  # or download from https://ngrok.com

# Start application
python -m app.main

# Start ngrok tunnel
ngrok http 8000

# Update Bot Service messaging endpoint in Azure Portal
# Set to: https://<your-ngrok-url>/api/messages

# Test in Teams!
```

## Docker Build and Run

```bash
# Build image
docker build -t teams-ai-agent:latest .

# Run container
docker run -p 8000:8000 \
  -e AZURE_OPENAI_ENDPOINT="..." \
  -e AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4" \
  -e BOT_ID="..." \
  -e APPLICATIONINSIGHTS_CONNECTION_STRING="..." \
  teams-ai-agent:latest

# Health check
curl http://localhost:8000/health
```

## API Endpoints

### `POST /api/messages`
Bot Framework webhook endpoint. Receives activities from Teams via Azure Bot Service.

**Authentication**: Bot Framework JWT validation

**Request**: Bot Framework Activity JSON

**Response**: 200 OK (empty body)

### `GET /health`
Container Apps health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "service": "teams-ai-agent",
  "agent_initialized": true,
  "conversations": {
    "total_conversations": 5,
    "active_threads": 3
  }
}
```

### `GET /`
Root endpoint with service information.

**Response**:
```json
{
  "service": "Teams AI Agent",
  "version": "1.0.0",
  "status": "running"
}
```

## Deployment

### Azure Container Apps Deployment

The application is designed to deploy to Azure Container Apps via `azd up`:

```bash
# From project root
azd up
```

This will:
1. Build the Docker image
2. Push to Azure Container Registry
3. Deploy to Container Apps
4. Configure environment variables from infrastructure outputs
5. Enable Application Insights telemetry

### Environment Variables (Production)

Set via Azure Container Apps environment:

- `AZURE_OPENAI_ENDPOINT` - From infrastructure output
- `AZURE_OPENAI_DEPLOYMENT_NAME` - From infrastructure output
- `BOT_ID` - From infrastructure output
- `APPLICATIONINSIGHTS_CONNECTION_STRING` - From infrastructure output
- `ENVIRONMENT=production` - Enables managed identity authentication

## Testing

### Unit Tests

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=app tests/
```

### Integration Tests

Test with Bot Framework Emulator or Teams client.

## Post-MVP Enhancements

### Conversation State
- [ ] Migrate to Azure Redis Cache for distributed state
- [ ] Add conversation history persistence
- [ ] Implement conversation analytics

### Agent Capabilities
- [ ] Add function tools for specific domains
- [ ] Implement streaming responses in Teams
- [ ] Add multi-agent orchestration

### Security
- [ ] Implement rate limiting
- [ ] Add input validation middleware
- [ ] Enable VNet integration

### Monitoring
- [ ] Add custom metrics dashboards
- [ ] Implement alerting for errors
- [ ] Add performance monitoring

## Troubleshooting

### Agent Initialization Fails

**Error**: "Failed to initialize agent"

**Solutions**:
- Check Azure CLI is authenticated: `az login`
- Verify Azure OpenAI endpoint and deployment name
- Ensure user has "Cognitive Services OpenAI User" role

### Bot Framework Authentication Fails

**Error**: 401 Unauthorized on `/api/messages`

**Solutions**:
- Verify BOT_ID matches Azure Bot Service registration
- For local testing with emulator, leave BOT_PASSWORD empty
- For Teams, ensure messaging endpoint is configured correctly

### Application Insights Not Receiving Telemetry

**Solutions**:
- Verify APPLICATIONINSIGHTS_CONNECTION_STRING is set
- Check connection string format includes InstrumentationKey
- Ensure no firewall blocking ai telemetry endpoints

### Docker Container Health Check Fails

**Solutions**:
- Check application logs: `docker logs <container-id>`
- Verify port 8000 is exposed correctly
- Test health endpoint: `curl http://localhost:8000/health`

## References

- [Microsoft Agent Framework Documentation](https://learn.microsoft.com/en-us/agent-framework/)
- [Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Bot Framework SDK for Python](https://github.com/microsoft/botbuilder-python)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/)
