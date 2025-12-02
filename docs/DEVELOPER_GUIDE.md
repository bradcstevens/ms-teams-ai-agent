# MS Teams AI Agent - Developer Guide

Comprehensive guide for developers covering local setup, development workflow, API reference, testing, and contributing to the MS Teams AI Agent project.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Project Structure](#project-structure)
4. [Development Workflow](#development-workflow)
5. [API Reference](#api-reference)
6. [Testing](#testing)
7. [MCP Server Development](#mcp-server-development)
8. [Deployment](#deployment)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

| Tool | Version | Installation |
|------|---------|--------------|
| Python | 3.11+ | [python.org](https://www.python.org/downloads/) |
| Docker | 24+ | [docker.com](https://docs.docker.com/get-docker/) |
| Azure CLI | Latest | [Install Guide](https://docs.microsoft.com/cli/azure/install-azure-cli) |
| Azure Developer CLI | 1.5+ | [Install Guide](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd) |
| Git | Latest | [git-scm.com](https://git-scm.com/downloads) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org/) (for MCP servers) |

### Azure Access

- Azure subscription with Contributor access
- Azure OpenAI service access (requires approval)
- Permissions to create Bot Service registrations

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd ms-teams-ai-agent
```

### 2. Run Setup Script

```bash
./scripts/setup-local.sh
```

This script will:
- Create Python virtual environment
- Install dependencies
- Generate `.env` file from template
- Validate configuration

### 3. Configure Environment

Edit `.env` with your values:

```bash
# Required for local development
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5

# Bot credentials (get from Azure Bot Service)
BOT_APP_ID=your-bot-app-id
BOT_APP_PASSWORD=your-bot-password

# Optional
LOG_LEVEL=DEBUG
MCP_CONFIG_PATH=./mcp_servers.json
```

### 4. Activate Virtual Environment

```bash
# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 5. Run Application Locally

```bash
# Start the FastAPI server
python -m uvicorn src.app.main:app --reload --port 8000
```

### 6. Test Health Endpoint

```bash
curl http://localhost:8000/health
```

---

## Project Structure

```
ms-teams-ai-agent/
├── src/                            # Application source code
│   ├── app/                        # Main application package
│   │   ├── main.py                 # FastAPI entrypoint
│   │   ├── agent/                  # AI agent with Azure OpenAI
│   │   ├── bot/                    # Teams bot (auth, security, state)
│   │   ├── config/                 # Pydantic settings
│   │   ├── mcp/                    # MCP integration
│   │   ├── teams/                  # Manifest generation/validation
│   │   ├── telemetry/              # Application Insights
│   │   └── utils/                  # Shared utilities
│   ├── tests/                      # Unit tests
│   ├── Dockerfile                  # Container definition
│   └── requirements.txt            # Python dependencies
├── infra/                          # Bicep infrastructure
│   ├── main.bicep                  # Main orchestration
│   ├── core/                       # Container Apps, Registry, Key Vault
│   ├── ai/                         # Azure OpenAI
│   └── bot/                        # Azure Bot Service
├── scripts/                        # Automation scripts
├── teams/                          # Teams app manifest & icons
├── tests/                          # Integration tests
│   ├── integration/                # Integration test suite
│   └── docs/                       # Test documentation
├── docs/                           # Project documentation
├── azure.yaml                      # azd configuration
└── .env.example                    # Environment template
```

### Key Files

| File | Purpose |
|------|---------|
| `src/app/main.py` | FastAPI application entry point |
| `src/app/bot/teams_bot.py` | TeamsBot message handler |
| `src/app/agent/ai_agent.py` | AI agent with Azure OpenAI |
| `src/app/mcp/manager.py` | MCP connection manager |
| `infra/main.bicep` | Azure infrastructure definition |
| `teams/manifest.json` | Teams app manifest |

---

## Development Workflow

### Making Changes

1. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes following code standards**

3. **Run tests**
   ```bash
   pytest src/tests/ -v
   ```

4. **Run linting**
   ```bash
   ruff check src/
   mypy src/
   ```

5. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

6. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

### Code Standards

#### Python Style Guide

- Follow PEP 8 style guidelines
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use docstrings for public functions/classes

```python
from typing import Optional

def process_message(
    message: str,
    context: Optional[dict] = None
) -> str:
    """
    Process an incoming message and generate a response.

    Args:
        message: The user's message text
        context: Optional conversation context

    Returns:
        The generated response string
    """
    pass
```

#### Commit Message Format

```
<type>(<scope>): <subject>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat(mcp): add web search server integration
fix(bot): handle empty message payload
docs(readme): update deployment instructions
```

---

## API Reference

### Base URL

- **Local Development**: `http://localhost:8000`
- **Production**: `https://<container-app-name>.<region>.azurecontainerapps.io`

### Endpoints

#### Health Check

```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-25T12:00:00.000Z",
  "components": {
    "openai": "connected",
    "mcp": "operational"
  }
}
```

| Status | Description |
|--------|-------------|
| 200 | Application healthy |
| 503 | Application unhealthy |

#### Bot Messages Webhook

```
POST /api/messages
```

Receives messages from Azure Bot Service (Bot Framework Protocol).

**Headers:**
| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | Bot Framework JWT token |
| `Content-Type` | Yes | `application/json` |

**Request Body:** Bot Framework Activity object

**Response:** 200 OK (empty body per Bot Framework protocol)

| Status | Description |
|--------|-------------|
| 200 | Activity processed |
| 401 | Invalid token |
| 400 | Malformed payload |

#### Root Endpoint

```
GET /
```

Returns application info with links to `/docs` and `/health`.

#### OpenAPI Documentation

```
GET /docs
```

Interactive Swagger UI for testing endpoints.

### Activity Types

| Type | Description | Bot Response |
|------|-------------|--------------|
| `message` | Text message from user | AI-generated response |
| `conversationUpdate` | User added/removed | Welcome message |
| `messageReaction` | User reacted | Logged only |
| `typing` | User is typing | None |

### Error Responses

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description"
  }
}
```

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Invalid token |
| `INVALID_ACTIVITY` | 400 | Malformed payload |
| `RATE_LIMITED` | 429 | Too many requests |
| `OPENAI_ERROR` | 502 | Azure OpenAI error |
| `MCP_ERROR` | 502 | MCP server error |

### Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/messages` | 100 requests | per minute per user |
| `/health` | 1000 requests | per minute |

---

## Testing

### Running Tests

```bash
# All unit tests
pytest src/tests/ -v

# Integration tests
pytest tests/integration/ -v

# With coverage
pytest src/tests/ --cov=src/app --cov-report=html
```

### Test Structure

```
src/tests/
├── conftest.py              # Shared fixtures
├── test_mcp_config.py       # MCP configuration tests
├── test_mcp_discovery.py    # MCP discovery tests
├── test_mcp_client.py       # MCP client tests
├── test_bot_handler.py      # Bot handler tests
└── test_agent.py            # Agent logic tests
```

### Writing Tests

```python
import pytest
from src.app.mcp.config import MCPConfig

class TestMCPConfig:
    """Tests for MCP configuration management."""

    def test_load_valid_config(self, tmp_path):
        """Test loading a valid MCP configuration file."""
        config_file = tmp_path / "mcp_servers.json"
        config_file.write_text('{"mcpServers": {}}')

        config = MCPConfig.load(str(config_file))

        assert config is not None
        assert config.servers == {}
```

### Local Testing with Bot Framework Emulator

1. Download [Bot Framework Emulator](https://github.com/Microsoft/BotFramework-Emulator/releases)

2. Start local server:
   ```bash
   python -m uvicorn src.app.main:app --port 3978
   ```

3. In Emulator, connect to `http://localhost:3978/api/messages`

4. Leave App ID and Password empty for local testing

### Using ngrok for Teams Testing

```bash
# Start ngrok tunnel
ngrok http 3978

# Note the https URL (e.g., https://abc123.ngrok.io)
# Update Bot Service endpoint to: https://abc123.ngrok.io/api/messages
```

---

## MCP Server Development

### Adding a New MCP Server

1. **Create server adapter** in `src/app/mcp/servers/`:

```python
# src/app/mcp/servers/my_server.py
from typing import Any, Dict, List
from ..client import MCPClient

class MyServer:
    """Custom MCP server adapter."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = MCPClient(config)

    async def get_tools(self) -> List[Dict[str, Any]]:
        """Return available tools from this server."""
        return await self.client.list_tools()

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """Execute a tool and return results."""
        return await self.client.call_tool(tool_name, arguments)
```

2. **Register in configuration** (`mcp_servers.json`):

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["-m", "my_mcp_server"],
      "transport": "stdio",
      "enabled": true,
      "description": "My custom MCP server"
    }
  }
}
```

3. **Add tests** in `src/tests/test_my_server.py`

---

## Deployment

### Deploy to Azure

```bash
# Full deployment
azd up

# Infrastructure only
azd provision

# Application only
azd deploy
```

### Environment Management

```bash
# Create new environment
azd env new staging

# Switch environments
azd env select production

# View environment values
azd env get-values
```

### Validate Deployment

```bash
# Run acceptance criteria validation
./scripts/validate-acceptance-criteria.sh

# Full deployment validation
./scripts/validate-full-deployment.sh --environment dev
```

---

## Troubleshooting

### Virtual Environment Issues

```bash
# Recreate virtual environment
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt
```

### Import Errors

```bash
# Ensure you're running from project root
cd /path/to/ms-teams-ai-agent

# Install in editable mode
pip install -e src/
```

### MCP Server Connection Issues

```bash
# Test MCP server manually
npx -y @modelcontextprotocol/server-filesystem /tmp

# Check server health
python -c "
from src.app.mcp.manager import MCPManager
import asyncio
asyncio.run(MCPManager().health_check())
"
```

### Azure CLI Authentication

```bash
# Re-authenticate
az login
azd auth login

# Check current subscription
az account show
```

---

## Resources

### Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture
- [OPERATIONS.md](./OPERATIONS.md) - Operations and monitoring
- [MCP_INTEGRATION.md](./MCP_INTEGRATION.md) - MCP setup guide
- [TEAMS_GUIDE.md](./TEAMS_GUIDE.md) - Teams deployment

### External Resources

- [Bot Framework Documentation](https://docs.microsoft.com/azure/bot-service/)
- [Azure OpenAI Documentation](https://learn.microsoft.com/azure/ai-services/openai/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Azure Container Apps](https://learn.microsoft.com/azure/container-apps/)
- [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/)

---
*Last Updated: 2025-12-01*
