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

### MCP Server Configuration File

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

### Configuration Schema

Each MCP server configuration must include:

- **command** (required): Executable command or URL
  - For STDIO: Command to execute (e.g., `npx`, `python`, `node`)
  - For SSE: HTTP endpoint URL
- **args** (optional): Command-line arguments (STDIO only)
- **env** (optional): Environment variables for the server
  - Supports `${VAR_NAME}` syntax for substitution
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
2. Check environment variables are set
3. Validate server command exists
4. Review server logs for errors
5. Test server manually outside container

#### Tool Discovery Fails

**Symptom**: No tools registered from MCP server

**Solutions:**
1. Verify server implements `tools/list` JSON-RPC method
2. Check server is connected successfully
3. Inspect JSON-RPC response format
4. Review tool schema validation errors
5. Enable debug logging for discovery

#### Environment Variable Not Found

**Symptom**: `MCPConfigError: Environment variable 'XXX' not found`

**Solutions:**
1. Add variable to Container Apps environment
2. Reference secret in Azure Key Vault
3. Update `mcp_servers.json` with correct variable name
4. Restart container after adding variables

#### Circuit Breaker Stuck Open

**Symptom**: Tools fail with "Circuit breaker is OPEN"

**Solutions:**
1. Check MCP server health manually
2. Review failure logs to identify root cause
3. Manually reset circuit breaker if needed
4. Adjust failure threshold if too sensitive
5. Increase recovery timeout if server needs longer

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
