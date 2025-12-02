# MCP (Model Context Protocol) Integration Guide

## Overview

This Azure AI Agent Framework MVP includes comprehensive Model Context Protocol (MCP) integration, enabling the Teams bot to dynamically connect to external tools and data sources through standardized MCP servers.

## Architecture

### Core Components

1. **Configuration System** (`app/mcp/config.py`, `app/mcp/loader.py`)
   - Pydantic-based schema validation
   - JSON configuration file loading
   - Environment variable substitution for secrets
   - Enable/disable flags for individual servers

2. **Client Implementation** (`app/mcp/client.py`, `app/mcp/factory.py`)
   - Abstract base class for MCP clients
   - STDIO transport for process-based servers
   - SSE (Server-Sent Events) transport for HTTP-based servers
   - Factory pattern for transport-aware client creation

3. **Connection Management** (`app/mcp/manager.py`)
   - Connection pooling for multiple MCP servers
   - Retry logic with exponential backoff and jitter
   - Health checking for connected servers
   - Graceful shutdown and cleanup

4. **Tool Discovery & Registry** (`app/mcp/discovery.py`, `app/mcp/registry.py`)
   - Automatic tool discovery via JSON-RPC `tools/list`
   - Thread-safe tool registry with metadata caching
   - Name conflict resolution with server prefixes

5. **Agent Framework Bridge** (`app/mcp/bridge.py`)
   - Tool schema translation to Agent Framework format
   - Tool invocation routing to appropriate MCP servers
   - Result streaming and error handling

6. **Error Handling & Resilience** (`app/mcp/circuit_breaker.py`)
   - Circuit breaker pattern for fault isolation
   - Three states: CLOSED, OPEN, HALF_OPEN
   - Automatic recovery attempts after timeout
   - Manual reset capability for operations

## Configuration

The MCP integration supports two configuration methods that can be used independently or together:

1. **JSON Configuration File** (`mcp_servers.json`)
2. **Environment Variables** (recommended for containerized deployments)

When both methods are used, environment variables take precedence for servers with matching names, enabling configuration overrides without modifying JSON files.

### Method 1: JSON Configuration File

Create `mcp_servers.json` in the project root:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/path/to/allowed/directory"
      ],
      "transport": "stdio",
      "enabled": true,
      "description": "File system access for agent"
    },
    "web-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "${BRAVE_API_KEY}"
      },
      "transport": "stdio",
      "enabled": true,
      "description": "Web search via Brave Search API"
    },
    "custom-api": {
      "command": "https://api.example.com/mcp",
      "env": {
        "Authorization": "Bearer ${API_TOKEN}"
      },
      "transport": "sse",
      "enabled": false,
      "description": "Custom HTTP-based MCP server"
    }
  }
}
```

### Method 2: Environment Variable Configuration

MCP servers can be configured entirely through environment variables using a structured naming convention. This is the **recommended approach** for Azure Container Apps and other containerized deployments.

#### Environment Variable Naming Convention

MCP servers are defined using the pattern `MCP_SERVER_N_*` where `N` is a sequential number (1, 2, 3, etc.):

**Core Server Configuration:**
- `MCP_SERVER_N_NAME` (required): Unique server identifier
- `MCP_SERVER_N_COMMAND` (required): Executable command or URL
- `MCP_SERVER_N_ARGS` (optional): JSON array of command arguments
- `MCP_SERVER_N_TRANSPORT` (required): `stdio` or `sse`
- `MCP_SERVER_N_ENABLED` (optional): `true` or `false` (default: `true`)
- `MCP_SERVER_N_DESCRIPTION` (optional): Human-readable description

**Server-Specific Environment Variables:**
- `MCP_SERVER_N_ENV_<VAR_NAME>`: Environment variables passed to the MCP server
- Example: `MCP_SERVER_1_ENV_API_KEY`, `MCP_SERVER_2_ENV_AUTH_TOKEN`

**Optional Optimization:**
- `MCP_SERVER_COUNT`: Number of configured servers (improves startup performance)

#### Single Server Example

```bash
# Filesystem MCP Server
export MCP_SERVER_1_NAME="filesystem"
export MCP_SERVER_1_COMMAND="npx"
export MCP_SERVER_1_ARGS='["-y", "@modelcontextprotocol/server-filesystem", "/app/data"]'
export MCP_SERVER_1_TRANSPORT="stdio"
export MCP_SERVER_1_ENABLED="true"
export MCP_SERVER_1_DESCRIPTION="File system access for agent workspace"
```

#### Multiple Servers Example

```bash
# Server 1: Filesystem
export MCP_SERVER_1_NAME="filesystem"
export MCP_SERVER_1_COMMAND="npx"
export MCP_SERVER_1_ARGS='["-y", "@modelcontextprotocol/server-filesystem", "/app/data"]'
export MCP_SERVER_1_TRANSPORT="stdio"
export MCP_SERVER_1_ENABLED="true"

# Server 2: Brave Search
export MCP_SERVER_2_NAME="brave-search"
export MCP_SERVER_2_COMMAND="npx"
export MCP_SERVER_2_ARGS='["-y", "@modelcontextprotocol/server-brave-search"]'
export MCP_SERVER_2_TRANSPORT="stdio"
export MCP_SERVER_2_ENABLED="true"
export MCP_SERVER_2_ENV_BRAVE_API_KEY="${BRAVE_API_KEY}"

# Server 3: Custom SSE Server
export MCP_SERVER_3_NAME="custom-api"
export MCP_SERVER_3_COMMAND="https://api.example.com/mcp"
export MCP_SERVER_3_TRANSPORT="sse"
export MCP_SERVER_3_ENABLED="false"
export MCP_SERVER_3_ENV_Authorization="Bearer ${API_TOKEN}"

# Optional: Specify server count for faster startup
export MCP_SERVER_COUNT="3"
```

#### Server with API Keys and Secrets

```bash
# Web search with API key from Azure Key Vault
export MCP_SERVER_1_NAME="web-search"
export MCP_SERVER_1_COMMAND="npx"
export MCP_SERVER_1_ARGS='["-y", "@modelcontextprotocol/server-brave-search"]'
export MCP_SERVER_1_TRANSPORT="stdio"
export MCP_SERVER_1_ENV_BRAVE_API_KEY="secretref:brave-api-key"  # Azure Key Vault reference
export MCP_SERVER_1_DESCRIPTION="Web search via Brave Search API"

# Database access with multiple credentials
export MCP_SERVER_2_NAME="database"
export MCP_SERVER_2_COMMAND="python"
export MCP_SERVER_2_ARGS='["-m", "mcp_server_postgres"]'
export MCP_SERVER_2_TRANSPORT="stdio"
export MCP_SERVER_2_ENV_DB_HOST="secretref:db-host"
export MCP_SERVER_2_ENV_DB_USER="secretref:db-user"
export MCP_SERVER_2_ENV_DB_PASSWORD="secretref:db-password"
export MCP_SERVER_2_ENV_DB_NAME="production"
```

### Configuration Priority and Merging

When both JSON configuration and environment variables are present:

1. **Environment variables take precedence** for servers with matching names
2. **JSON-only servers** are loaded as-is
3. **Environment-only servers** are loaded as-is
4. **Merged configuration** combines both sources

**Example Scenario:**

`mcp_servers.json`:
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/default/path"],
      "transport": "stdio",
      "enabled": true
    }
  }
}
```

Environment variables:
```bash
export MCP_SERVER_1_NAME="filesystem"
export MCP_SERVER_1_ARGS='["-y", "@modelcontextprotocol/server-filesystem", "/custom/path"]'
export MCP_SERVER_1_ENABLED="true"
```

**Result**: The `filesystem` server uses `/custom/path` (from environment variable), overriding the JSON configuration.

### Configuration Schema

Each MCP server configuration must include:

- **command** (required): Executable command or URL
  - For STDIO: Command to execute (e.g., `npx`, `python`, `node`)
  - For SSE: HTTP endpoint URL
- **args** (optional): Command-line arguments (STDIO only)
  - JSON format: Must be valid JSON array when using environment variables
- **env** (optional): Environment variables for the server
  - Supports `${VAR_NAME}` syntax for substitution
  - Use `MCP_SERVER_N_ENV_*` pattern for environment variable configuration
- **transport** (required): `stdio` or `sse`
- **enabled** (optional): Whether server is active (default: `true`)
- **description** (optional): Human-readable description

### Environment Variable Substitution

Environment variables are automatically substituted using `${VAR_NAME}` syntax:

```json
{
  "env": {
    "API_KEY": "${BRAVE_API_KEY}",
    "ENDPOINT": "https://${API_HOST}/v1"
  }
}
```

Set environment variables in Azure Key Vault and configure in Container Apps:

```bash
az containerapp update \
  --name teams-bot \
  --set-env-vars \
    BRAVE_API_KEY=secretref:brave-api-key \
    API_HOST=api.brave.com
```

### Azure Container Apps Integration

The environment variable-based MCP configuration integrates seamlessly with Azure Container Apps through multiple configuration methods.

#### Method 1: Configure via azure.yaml

Add MCP server configuration to your `azure.yaml` file:

```yaml
services:
  teams-bot:
    project: .
    language: python
    host: containerapp
    env:
      # MCP Server 1: Filesystem
      MCP_SERVER_1_NAME: filesystem
      MCP_SERVER_1_COMMAND: npx
      MCP_SERVER_1_ARGS: '["-y", "@modelcontextprotocol/server-filesystem", "/app/data"]'
      MCP_SERVER_1_TRANSPORT: stdio
      MCP_SERVER_1_ENABLED: "true"
      MCP_SERVER_1_DESCRIPTION: "Agent file workspace"

      # MCP Server 2: Web Search (with Key Vault secret)
      MCP_SERVER_2_NAME: brave-search
      MCP_SERVER_2_COMMAND: npx
      MCP_SERVER_2_ARGS: '["-y", "@modelcontextprotocol/server-brave-search"]'
      MCP_SERVER_2_TRANSPORT: stdio
      MCP_SERVER_2_ENABLED: "true"
      MCP_SERVER_2_ENV_BRAVE_API_KEY: ${BRAVE_API_KEY}  # From Key Vault

      # Optimization
      MCP_SERVER_COUNT: "2"
```

Deploy with Azure Developer CLI:

```bash
azd up
```

#### Method 2: Configure via Bicep Parameters

Add MCP configuration to your Bicep template (`infra/main.bicep`):

```bicep
param mcpServers array = [
  {
    name: 'filesystem'
    command: 'npx'
    args: '["-y", "@modelcontextprotocol/server-filesystem", "/app/data"]'
    transport: 'stdio'
    enabled: 'true'
    description: 'Agent file workspace'
  }
  {
    name: 'brave-search'
    command: 'npx'
    args: '["-y", "@modelcontextprotocol/server-brave-search"]'
    transport: 'stdio'
    enabled: 'true'
    envVars: {
      BRAVE_API_KEY: braveApiKey  // From Key Vault
    }
  }
]

// Convert to environment variables for Container App
var mcpEnvVars = [
  for i in range(0, length(mcpServers)): {
    name: 'MCP_SERVER_${i + 1}_NAME'
    value: mcpServers[i].name
  }
  for i in range(0, length(mcpServers)): {
    name: 'MCP_SERVER_${i + 1}_COMMAND'
    value: mcpServers[i].command
  }
  for i in range(0, length(mcpServers)): {
    name: 'MCP_SERVER_${i + 1}_ARGS'
    value: mcpServers[i].args
  }
  for i in range(0, length(mcpServers)): {
    name: 'MCP_SERVER_${i + 1}_TRANSPORT'
    value: mcpServers[i].transport
  }
  for i in range(0, length(mcpServers)): {
    name: 'MCP_SERVER_${i + 1}_ENABLED'
    value: mcpServers[i].enabled
  }
  {
    name: 'MCP_SERVER_COUNT'
    value: string(length(mcpServers))
  }
]

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  properties: {
    template: {
      containers: [
        {
          env: concat(baseEnvVars, mcpEnvVars)
        }
      ]
    }
  }
}
```

#### Method 3: Azure Key Vault Integration for Secrets

Store sensitive MCP server credentials in Azure Key Vault:

**Step 1: Create Key Vault secrets**

```bash
# Create Key Vault (if not exists)
az keyvault create \
  --name ${KEY_VAULT_NAME} \
  --resource-group ${RESOURCE_GROUP} \
  --location ${LOCATION}

# Add MCP server API keys
az keyvault secret set \
  --vault-name ${KEY_VAULT_NAME} \
  --name brave-api-key \
  --value ${BRAVE_API_KEY}

az keyvault secret set \
  --vault-name ${KEY_VAULT_NAME} \
  --name openai-api-key \
  --value ${OPENAI_API_KEY}
```

**Step 2: Grant Container App access to Key Vault**

```bash
# Enable managed identity for Container App
az containerapp identity assign \
  --name teams-bot \
  --resource-group ${RESOURCE_GROUP} \
  --system-assigned

# Get managed identity principal ID
PRINCIPAL_ID=$(az containerapp identity show \
  --name teams-bot \
  --resource-group ${RESOURCE_GROUP} \
  --query principalId -o tsv)

# Grant Key Vault access
az keyvault set-policy \
  --name ${KEY_VAULT_NAME} \
  --object-id ${PRINCIPAL_ID} \
  --secret-permissions get list
```

**Step 3: Configure Container App with Key Vault references**

```bash
az containerapp update \
  --name teams-bot \
  --resource-group ${RESOURCE_GROUP} \
  --set-env-vars \
    MCP_SERVER_1_NAME=brave-search \
    MCP_SERVER_1_COMMAND=npx \
    MCP_SERVER_1_ARGS='["-y", "@modelcontextprotocol/server-brave-search"]' \
    MCP_SERVER_1_TRANSPORT=stdio \
    MCP_SERVER_1_ENABLED=true \
    MCP_SERVER_1_ENV_BRAVE_API_KEY=secretref:brave-api-key \
    MCP_SERVER_2_NAME=openai-tools \
    MCP_SERVER_2_COMMAND=python \
    MCP_SERVER_2_ARGS='["-m", "mcp_server_openai"]' \
    MCP_SERVER_2_TRANSPORT=stdio \
    MCP_SERVER_2_ENV_OPENAI_API_KEY=secretref:openai-api-key \
    MCP_SERVER_COUNT=2
```

**Step 4: Verify configuration**

```bash
# Check environment variables
az containerapp show \
  --name teams-bot \
  --resource-group ${RESOURCE_GROUP} \
  --query properties.template.containers[0].env
```

#### Best Practices for Azure Deployments

1. **Use Key Vault for all secrets**: Never hardcode API keys in environment variables
2. **Enable managed identity**: Use system-assigned identity for Key Vault access
3. **Set MCP_SERVER_COUNT**: Improves container startup time
4. **Use descriptive server names**: Makes debugging easier in Application Insights
5. **Start with disabled servers**: Test MCP servers locally before enabling in production
6. **Monitor MCP metrics**: Track server health and tool invocation rates
7. **Use separate Key Vaults**: Isolate production and development secrets

## Transport Types

### STDIO Transport

Process-based communication using stdin/stdout:

**Advantages:**
- Simple subprocess management
- Works with npm packages and Python modules
- No network overhead

**Use Cases:**
- `@modelcontextprotocol/server-filesystem`
- `@modelcontextprotocol/server-brave-search`
- Local Python MCP servers

**Example:**
```json
{
  "command": "npx",
  "args": ["-y", "package-name"],
  "transport": "stdio"
}
```

### SSE (Server-Sent Events) Transport

HTTP-based communication with Server-Sent Events:

**Advantages:**
- Supports remote MCP servers
- Standard HTTP authentication
- Can use load balancers and proxies

**Use Cases:**
- Remote MCP server APIs
- Multi-tenant MCP services
- Cloud-hosted tools

**Example:**
```json
{
  "command": "https://mcp.example.com",
  "env": {
    "Authorization": "Bearer ${TOKEN}"
  },
  "transport": "sse"
}
```

## Example Server Integrations

### Filesystem Server

Provides file operations within allowed directories:

```python
from app.mcp.servers.filesystem import FilesystemServerHelper

# Create configuration
config = FilesystemServerHelper.create_config(
    allowed_directory="/app/data",
    enabled=True,
    description="Agent workspace"
)

# Validate directory safety
is_valid, message = FilesystemServerHelper.validate_directory("/app/data")
if not is_valid:
    raise ValueError(message)

# Available tools: read_file, write_file, list_directory, create_directory, etc.
```

**Security Recommendations:**
- Use absolute paths only
- Never grant access to system directories (`/etc`, `/usr`, etc.)
- Prefer read-only access when write is not needed
- Create dedicated directories for agent file access
- Monitor file operations via Application Insights

### Web Search Server

Enables internet search for current information:

```python
from app.mcp.servers.web_search import WebSearchServerHelper

# Brave Search (recommended)
config = WebSearchServerHelper.create_brave_search_config(
    api_key_env_var="BRAVE_API_KEY",
    enabled=True
)

# Google Custom Search
config = WebSearchServerHelper.create_google_search_config(
    api_key_env_var="GOOGLE_API_KEY",
    search_engine_id_env_var="GOOGLE_SEARCH_ENGINE_ID"
)

# SSE-based remote search
config = WebSearchServerHelper.create_sse_search_config(
    endpoint_url="https://search-api.example.com",
    auth_token_env_var="SEARCH_API_TOKEN"
)
```

**Rate Limiting:**
- Brave Search: 15,000 queries/month free tier (500/day)
- Google Custom Search: 100 queries/day free tier
- Implement client-side rate limiting
- Cache search results (5-15 minutes TTL)

## Usage in Application

### Initialization

```python
from app.mcp import (
    load_mcp_config,
    MCPConnectionManager,
    MCPToolRegistry,
    MCPToolBridge,
    discover_tools_from_manager,
)

# Load configuration
config = load_mcp_config("mcp_servers.json")

# Initialize connection manager
manager = MCPConnectionManager()
await manager.initialize(config)

# Connect to enabled servers
results = await manager.connect_all_enabled()
for server_name, success in results.items():
    if success:
        logger.info(f"Connected to {server_name}")
    else:
        logger.warning(f"Failed to connect to {server_name}")

# Discover and register tools
registry = MCPToolRegistry()
tools_by_server = await discover_tools_from_manager(manager)
for server_name, tools in tools_by_server.items():
    for tool in tools:
        full_name = registry.register_tool(server_name, tool)
        logger.info(f"Registered tool: {full_name}")

# Create bridge for agent
bridge = MCPToolBridge(registry, manager)
```

### Tool Execution

```python
# Execute a tool through the bridge
result = await bridge.execute_tool(
    full_tool_name="filesystem.read_file",
    params={"path": "/app/data/document.txt"}
)

# Get all available tools for agent
available_tools = bridge.get_available_tools()
# Returns list of tool definitions in Agent Framework format
```

### Health Monitoring

```python
# Check health of all connected servers
health_status = await manager.health_check_all()
for server_name, is_healthy in health_status.items():
    if not is_healthy:
        logger.warning(f"Server {server_name} is unhealthy")

# Get detailed server status
status = await manager.get_server_status()
# Returns: {"server_name": {"enabled": bool, "connected": bool}}
```

### Graceful Shutdown

```python
# Disconnect all servers and cleanup
await manager.shutdown()
```

## Circuit Breaker Pattern

The circuit breaker protects against cascading failures from unresponsive MCP servers:

```python
from app.mcp import CircuitBreaker

# Create circuit breaker for a server
circuit_breaker = CircuitBreaker(
    name="web-search",
    failure_threshold=5,      # Open after 5 failures
    recovery_timeout=60.0,    # Try recovery after 60 seconds
    success_threshold=2,      # Close after 2 successes in HALF_OPEN
)

# Execute function through circuit breaker
async def call_mcp_server():
    # Your MCP server call here
    pass

try:
    result = await circuit_breaker.call(call_mcp_server)
except MCPConnectionError:
    # Circuit is OPEN, service unavailable
    logger.warning(f"Circuit breaker OPEN for {circuit_breaker.name}")
```

### Circuit States

- **CLOSED**: Normal operation, requests pass through
- **OPEN**: Too many failures, requests fail immediately
- **HALF_OPEN**: Testing recovery, limited requests allowed

### Metrics

```python
metrics = circuit_breaker.get_metrics()
# Returns:
# {
#   "name": "web-search",
#   "state": "closed",
#   "failure_count": 0,
#   "success_count": 0,
#   "time_until_reset": None
# }
```

## Error Handling

### Exception Hierarchy

```python
from app.mcp import (
    MCPConnectionError,   # Connection failures
    MCPTimeoutError,      # Request timeouts
    MCPTransportError,    # Transport-level errors
)

try:
    result = await client.send_request(request)
except MCPConnectionError as e:
    logger.error(f"Connection error: {e}")
    # Handle connection failure
except MCPTimeoutError as e:
    logger.warning(f"Request timeout: {e}")
    # Handle timeout
except MCPTransportError as e:
    logger.error(f"Transport error: {e}")
    # Handle transport error
```

### Retry Logic

Connection manager includes automatic retry with exponential backoff:

```python
# Retry configuration in connect_server()
await manager.connect_server(
    server_name="web-search",
    max_retries=3  # Try up to 3 times
)
# Backoff: 1s, 2s, 4s (with jitter)
```

## Testing

### Unit Tests

```python
# Test configuration loading
from app.mcp import load_mcp_config

config = load_mcp_config("test_config.json")
assert "test-server" in config.mcpServers

# Test client creation
from app.mcp import MCPClientFactory, MCPServerConfig, TransportType

server_config = MCPServerConfig(
    command="npx",
    args=["-y", "package"],
    transport=TransportType.STDIO
)
client = MCPClientFactory.create_client(server_config)
```

### Integration Tests

Run all MCP tests:

```bash
pytest src/tests/test_mcp*.py -v
```

Test coverage:
- Configuration schema and loading (22 tests)
- STDIO and SSE client implementations (18 tests)
- Connection manager and pooling (14 tests)
- Circuit breaker patterns (9 tests)
- Server helpers (18 tests)
- End-to-end integration (5 tests)

**Total: 86 tests**

## Security Considerations

### API Keys and Secrets

- **Never commit API keys** to version control
- Store secrets in **Azure Key Vault**
- Use environment variable substitution in configuration
- Rotate API keys regularly (90 days recommended)
- Monitor API key usage for anomalies

### Filesystem Access

- Grant **minimum necessary permissions**
- Use **absolute paths only**
- **Never expose system directories** (`/etc`, `/usr`, etc.)
- Implement **sandboxing** in containers
- **Monitor file operations** via Application Insights

### Network Security

- Use **HTTPS for SSE transport**
- Validate **SSL/TLS certificates**
- Implement **request authentication** (Bearer tokens)
- Add **rate limiting** to prevent abuse
- **Whitelist allowed endpoints**

### Input Validation

- **Sanitize user input** before tool calls
- **Validate tool parameters** against schemas
- **Limit parameter sizes** (strings, arrays)
- **Filter sensitive data** from logs
- **Audit all tool invocations**

## Monitoring and Telemetry

### Application Insights Integration

```python
from app.telemetry import get_logger

logger = get_logger(__name__)

# Log MCP operations
logger.info(
    "MCP tool invoked",
    extra={
        "tool_name": full_tool_name,
        "server_name": server_name,
        "params": sanitized_params,
    }
)

# Log circuit breaker events
logger.warning(
    "Circuit breaker opened",
    extra={
        "server_name": circuit_breaker.name,
        "failure_count": circuit_breaker._failure_count,
    }
)
```

### Metrics to Monitor

- **Tool invocation success/failure rates**
- **MCP server health check results**
- **Circuit breaker state transitions**
- **Request latencies and timeouts**
- **API quota usage (web search)**
- **File operation counts (filesystem)**

### Alerts

Configure alerts in Azure Monitor:

1. **Circuit Breaker Open**: Alert when circuit opens
2. **High Failure Rate**: > 10% tool invocations failing
3. **Quota Threshold**: Web search quota > 80%
4. **Slow Responses**: Tool latency > 5 seconds
5. **Connection Failures**: MCP server connection failures

## Troubleshooting

### Common Issues

#### MCP Server Not Connecting

**Symptom**: `MCPConnectionError: Failed to connect to server`

**Solutions:**
1. Verify npm/node is installed in container
2. Check environment variables are set correctly
3. Validate server command exists (test with `which npx` or `which python`)
4. Review server logs for errors in Application Insights
5. Test server manually outside container
6. Check server numbering (N) is sequential starting from 1

**Debugging Commands:**
```bash
# Inside container - check environment variables
env | grep MCP_SERVER

# Verify server command is available
which npx
which python3

# Test manual server execution
npx -y @modelcontextprotocol/server-filesystem /app/data
```

#### Tool Discovery Fails

**Symptom**: No tools registered from MCP server

**Solutions:**
1. Verify server implements `tools/list` JSON-RPC method
2. Check server is connected successfully (review startup logs)
3. Inspect JSON-RPC response format
4. Review tool schema validation errors
5. Enable debug logging for discovery
6. Verify server is enabled: `MCP_SERVER_N_ENABLED=true`

**Debug Logging:**
```python
import logging
logging.getLogger("app.mcp").setLevel(logging.DEBUG)
```

#### Environment Variable Configuration Issues

**Symptom**: Server not loading or configuration malformed

**Common Problems and Solutions:**

1. **Invalid JSON in ARGS field**
   - **Error**: `json.JSONDecodeError: Expecting value`
   - **Solution**: Ensure `MCP_SERVER_N_ARGS` is valid JSON array
   - **Correct**: `MCP_SERVER_1_ARGS='["-y", "package"]'`
   - **Incorrect**: `MCP_SERVER_1_ARGS="-y package"`

2. **Missing required NAME field**
   - **Error**: `MCPConfigError: Server N missing NAME`
   - **Solution**: Always set `MCP_SERVER_N_NAME` for each server

3. **Non-sequential server numbers**
   - **Problem**: Server 1 and 3 defined, but not 2
   - **Solution**: Use sequential numbering: 1, 2, 3, etc.
   - **Alternative**: Set `MCP_SERVER_COUNT` to skip auto-detection

4. **Environment variable substitution not working**
   - **Problem**: `${VAR_NAME}` appearing literally in logs
   - **Solution**: Ensure base environment variable is set before MCP loader runs
   - **Check**: `echo $BRAVE_API_KEY` should show value, not empty

5. **Server-specific env vars not passed to process**
   - **Problem**: MCP server reports missing API key
   - **Solution**: Use `MCP_SERVER_N_ENV_<VAR_NAME>` pattern
   - **Example**: `MCP_SERVER_1_ENV_BRAVE_API_KEY=abc123`

**Verification Script:**
```bash
#!/bin/bash
# verify_mcp_config.sh - Run this to debug MCP environment variables

echo "=== MCP Server Configuration ==="
echo "Server count: ${MCP_SERVER_COUNT:-auto-detect}"
echo ""

for i in {1..10}; do
    NAME_VAR="MCP_SERVER_${i}_NAME"
    NAME_VAL="${!NAME_VAR}"

    if [ -z "$NAME_VAL" ]; then
        if [ $i -eq 1 ]; then
            echo "No MCP servers configured via environment variables"
        fi
        break
    fi

    echo "Server $i: $NAME_VAL"
    echo "  Command: ${!MCP_SERVER_${i}_COMMAND}"
    echo "  Args: ${!MCP_SERVER_${i}_ARGS}"
    echo "  Transport: ${!MCP_SERVER_${i}_TRANSPORT}"
    echo "  Enabled: ${!MCP_SERVER_${i}_ENABLED:-true}"

    # Check for env vars
    for var in $(env | grep "^MCP_SERVER_${i}_ENV_" | cut -d= -f1); do
        echo "  Env: $var"
    done
    echo ""
done
```

#### Environment Variable Not Found

**Symptom**: `MCPConfigError: Environment variable 'XXX' not found`

**Solutions:**
1. Add variable to Container Apps environment
2. Reference secret in Azure Key Vault using `secretref:` prefix
3. Update environment variable name in MCP configuration
4. Restart container after adding variables
5. Check Azure Key Vault access policy for managed identity

**Azure Container Apps Check:**
```bash
# List all environment variables for container
az containerapp show \
  --name teams-bot \
  --resource-group ${RESOURCE_GROUP} \
  --query 'properties.template.containers[0].env[].name' -o table

# Check specific secret reference
az containerapp show \
  --name teams-bot \
  --resource-group ${RESOURCE_GROUP} \
  --query "properties.template.containers[0].env[?name=='MCP_SERVER_1_ENV_BRAVE_API_KEY']"
```

#### Circuit Breaker Stuck Open

**Symptom**: Tools fail with "Circuit breaker is OPEN"

**Solutions:**
1. Check MCP server health manually
2. Review failure logs to identify root cause
3. Manually reset circuit breaker if needed
4. Adjust failure threshold if too sensitive (default: 5)
5. Increase recovery timeout if server needs longer (default: 60s)

**Manual Circuit Breaker Reset:**
```python
from app.mcp import manager

# Get circuit breaker for server
cb = manager.get_circuit_breaker("brave-search")

# Manual reset (use with caution)
cb.reset()
```

#### JSON Config and Environment Variables Conflict

**Symptom**: Server behaves unexpectedly or uses wrong configuration

**Understanding Priority:**
- Environment variables **always override** JSON config for same-named servers
- Both sources can coexist - they are merged

**Solution:**
1. Check for duplicate server names in both configs
2. Decide on single source of truth per environment
3. Use environment variables for production (recommended)
4. Use JSON for local development

**Example Conflict:**
```json
// mcp_servers.json
{"mcpServers": {"filesystem": {"enabled": false}}}
```

```bash
# Environment variable (takes precedence)
export MCP_SERVER_1_NAME="filesystem"
export MCP_SERVER_1_ENABLED="true"
```

**Result**: Server is **enabled** (environment variable wins)

#### Logging and Debugging

**Enable detailed MCP logging:**

```python
# In app startup (app/main.py)
import logging

# Enable MCP debug logging
logging.getLogger("app.mcp").setLevel(logging.DEBUG)
logging.getLogger("app.mcp.loader").setLevel(logging.DEBUG)
logging.getLogger("app.mcp.config").setLevel(logging.DEBUG)
```

**Azure Application Insights Queries:**

```kusto
// Find MCP configuration errors
traces
| where message contains "MCP" and severityLevel >= 3
| order by timestamp desc
| take 100

// Track MCP server connections
customEvents
| where name == "MCPServerConnected" or name == "MCPServerFailed"
| summarize count() by name, tostring(customDimensions.server_name)

// Monitor tool invocations
customEvents
| where name == "MCPToolInvoked"
| summarize
    success=countif(customDimensions.success == "true"),
    failure=countif(customDimensions.success == "false")
    by bin(timestamp, 5m), tostring(customDimensions.tool_name)
| render timechart
```

### Best Practices for Troubleshooting

1. **Start simple**: Test with one MCP server before adding multiple
2. **Test locally first**: Verify MCP config works in local environment
3. **Use debug logging**: Enable verbose logging during initial setup
4. **Check sequentially**: Verify each component (config → connection → discovery → execution)
5. **Monitor metrics**: Watch Application Insights for patterns
6. **Use health checks**: Implement and monitor MCP server health endpoints
7. **Keep documentation updated**: Document custom MCP servers and their requirements

## Post-MVP Enhancements

### Planned Features

1. **Dynamic Server Management**
   - Add/remove MCP servers without restart
   - Hot-reload configuration changes
   - Server versioning and upgrades

2. **Advanced Caching**
   - Redis cache for tool results
   - Configurable TTL per tool
   - Cache invalidation strategies

3. **Tool Composition**
   - Chain multiple tools together
   - Conditional tool execution
   - Parallel tool invocation

4. **Enhanced Security**
   - Tool-level access control
   - User-based permissions
   - Audit logging with compliance reports

5. **Performance Optimization**
   - Connection pooling improvements
   - Request batching for bulk operations
   - Lazy server initialization

## References

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [Azure Container Apps Documentation](https://docs.microsoft.com/azure/container-apps/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
