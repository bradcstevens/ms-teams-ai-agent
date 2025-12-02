# MCP Client Factory & Connection Manager

## Overview

This module provides production-ready MCP (Model Context Protocol) client implementations and connection management for the Azure AI Agent Framework.

## Components

### 1. Client Implementations (`client.py`)

#### MCPClient (Abstract Base Class)
Base interface defining required methods for all MCP transport implementations.

**Required Methods:**
- `connect()` - Establish connection to MCP server
- `disconnect()` - Cleanup and close connection
- `send_request(request, timeout)` - Send JSON-RPC request
- `is_healthy()` - Health check connection status
- `get_tools()` - Retrieve available tools from server

#### MCPSTDIOClient
Subprocess-based client for local MCP servers.

**Use Cases:**
- Local MCP servers (npx packages, binaries)
- Example: `npx @modelcontextprotocol/server-filesystem`

**Features:**
- Process lifecycle management (graceful shutdown)
- Environment variable passing
- Zombie process prevention
- Timeout protection (5s graceful termination, then force kill)

**Example:**
```python
from app.mcp import MCPSTDIOClient, MCPServerConfig, TransportType

config = MCPServerConfig(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/data"],
    env={"DEBUG": "true"},
    transport=TransportType.STDIO
)

client = MCPSTDIOClient(config)
await client.connect()

# Send JSON-RPC request
request = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}
response = await client.send_request(request)

# Check health
is_healthy = await client.is_healthy()

await client.disconnect()
```

#### MCPSSEClient
HTTP-based client for remote MCP servers using Server-Sent Events.

**Use Cases:**
- Remote MCP servers over HTTP
- Cloud-hosted MCP services

**Features:**
- Persistent HTTP connection management
- Custom header support (via env config)
- Response timeout protection
- Connection health monitoring

**Example:**
```python
from app.mcp import MCPSSEClient, MCPServerConfig, TransportType

config = MCPServerConfig(
    command="http://api.example.com/mcp",
    env={"Authorization": "Bearer token123"},
    transport=TransportType.SSE
)

client = MCPSSEClient(config)
await client.connect()

# Send request
request = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}
response = await client.send_request(request, timeout=10.0)

await client.disconnect()
```

### 2. Client Factory (`factory.py`)

Automatically creates the correct client based on transport type.

**Example:**
```python
from app.mcp import MCPClientFactory, MCPServerConfig, TransportType

# STDIO client
stdio_config = MCPServerConfig(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    transport=TransportType.STDIO
)
client = MCPClientFactory.create_client(stdio_config)

# SSE client
sse_config = MCPServerConfig(
    command="http://localhost:8080/sse",
    transport=TransportType.SSE
)
client = MCPClientFactory.create_client(sse_config)
```

### 3. Connection Manager (`manager.py`)

Production-grade connection pool and lifecycle manager for multiple MCP servers.

**Features:**
- Connection pooling (multiple servers)
- Retry logic with exponential backoff (1s, 2s, 4s, 8s, max 30s)
- Jitter to prevent thundering herd
- Health check monitoring
- Graceful shutdown
- Server enable/disable support

**Example:**
```python
from app.mcp import MCPConnectionManager, MCPServersConfig, load_mcp_config

# Load configuration
config = load_mcp_config("mcp_servers.json")

# Initialize manager
manager = MCPConnectionManager()
await manager.initialize(config)

# Connect to specific server with retry
await manager.connect_server("filesystem", max_retries=3)

# Or connect to all enabled servers
results = await manager.connect_all_enabled()

# Get client instance
client = await manager.get_client("filesystem")
tools = await client.get_tools()

# Health check all servers
health_status = await manager.health_check_all()
print(health_status)  # {'filesystem': True, 'api': False}

# Get server status
status = await manager.get_server_status()
# {'filesystem': {'enabled': True, 'connected': True}, ...}

# Graceful shutdown
await manager.shutdown()
```

## Retry Logic

The connection manager implements exponential backoff with jitter:

**Base Behavior:**
- Attempt 0: 1s delay
- Attempt 1: 2s delay
- Attempt 2: 4s delay
- Attempt 3: 8s delay
- Max delay: 30s (configurable)

**Jitter:**
- Adds 0-50% random delay to prevent thundering herd
- Can be disabled for testing: `_calculate_backoff(attempt, jitter=False)`

**Example:**
```python
# Connect with custom retry settings
await manager.connect_server("filesystem", max_retries=5)
```

## Error Handling

### Exceptions

**MCPConnectionError:**
- Raised when connection fails
- Raised when trying to use disconnected client
- Raised when server is disabled

**MCPTimeoutError:**
- Raised when request times out
- Default timeout: 30 seconds
- Configurable per request

**MCPTransportError:**
- Raised for transport-level errors (HTTP, subprocess)
- Invalid JSON responses
- Communication failures

**Example:**
```python
from app.mcp.exceptions import MCPConnectionError, MCPTimeoutError

try:
    await manager.connect_server("filesystem")
except MCPConnectionError as e:
    logger.error(f"Failed to connect: {e}")

try:
    response = await client.send_request(request, timeout=5.0)
except MCPTimeoutError:
    logger.warning("Request timed out")
```

## Health Checks

**STDIO Client Health:**
- Checks if subprocess is still running
- `returncode is None` = healthy

**SSE Client Health:**
- Sends HTTP GET request to endpoint
- 5 second timeout
- Success status code = healthy

**Manager Health Check:**
```python
# Check all connected servers
health_status = await manager.health_check_all()

for server_name, is_healthy in health_status.items():
    if not is_healthy:
        logger.warning(f"Server {server_name} is unhealthy")
        # Optionally reconnect
        await manager.disconnect_server(server_name)
        await manager.connect_server(server_name)
```

## Resource Management

### STDIO Client
- Graceful termination with 5s timeout
- Force kill if termination fails
- No zombie process guarantees
- Proper stdin/stdout cleanup

### SSE Client
- HTTP connection pooling via httpx
- Proper connection closure on disconnect
- Async context manager support

### Connection Manager
- Parallel connection/disconnection
- Exception-safe cleanup
- Resource cleanup on shutdown

## Configuration Integration

Works seamlessly with the configuration system:

**mcp_servers.json:**
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/data"],
      "enabled": true,
      "transport": "stdio",
      "env": {
        "DEBUG": "true"
      }
    },
    "api": {
      "command": "http://api.example.com/mcp",
      "enabled": true,
      "transport": "sse",
      "env": {
        "Authorization": "Bearer ${API_TOKEN}"
      }
    }
  }
}
```

**Usage:**
```python
from app.mcp import load_mcp_config, MCPConnectionManager

config = load_mcp_config("mcp_servers.json")
manager = MCPConnectionManager()
await manager.initialize(config)
await manager.connect_all_enabled()
```

## Testing

The implementation includes comprehensive tests:

**Client Tests (18 tests):**
- STDIO client creation, connection, disconnection
- SSE client creation, connection, disconnection
- Request/response handling
- Timeout handling
- Health checks
- Environment variable handling

**Manager Tests (14 tests):**
- Initialization
- Connection pooling
- Retry logic with exponential backoff
- Health monitoring
- Graceful shutdown
- Server enable/disable

**Run Tests:**
```bash
pytest src/tests/test_mcp_client.py -v
pytest src/tests/test_mcp_manager.py -v
```

## Performance Considerations

**STDIO Client:**
- Subprocess creation overhead (one-time)
- Minimal runtime overhead (stdin/stdout communication)
- No network latency

**SSE Client:**
- HTTP connection reuse (persistent connections)
- Network latency considerations
- Connection timeout protection

**Connection Manager:**
- Parallel connection establishment
- Jittered retry to prevent thundering herd
- Health check caching (implement if needed)

## Production Recommendations

1. **Configure appropriate timeouts:**
   ```python
   response = await client.send_request(request, timeout=10.0)
   ```

2. **Implement health check monitoring:**
   ```python
   async def monitor_health():
       while True:
           health = await manager.health_check_all()
           for server, status in health.items():
               if not status:
                   await handle_unhealthy_server(server)
           await asyncio.sleep(60)  # Check every minute
   ```

3. **Handle reconnection:**
   ```python
   try:
       client = await manager.get_client("filesystem")
   except MCPConnectionError:
       await manager.connect_server("filesystem")
       client = await manager.get_client("filesystem")
   ```

4. **Graceful shutdown:**
   ```python
   import signal

   async def shutdown_handler(sig):
       logger.info("Shutting down...")
       await manager.shutdown()

   signal.signal(signal.SIGTERM, shutdown_handler)
   ```

## Integration with Tool Discovery

The client manager is ready for tool discovery integration:

```python
# Get all tools from all servers
all_tools = {}
for server_name in config.mcpServers.keys():
    client = await manager.get_client(server_name)
    tools = await client.get_tools()
    all_tools[server_name] = tools

# Register tools with Agent Framework
```

## Troubleshooting

**Subprocess won't start:**
- Check command exists: `which npx`
- Verify args are correct
- Check environment variables

**SSE connection fails:**
- Verify URL is reachable
- Check headers/authentication
- Enable debug logging

**Memory leaks:**
- Ensure `disconnect()` is called
- Use `manager.shutdown()` on application exit
- Monitor subprocess cleanup

**Zombie processes:**
- The STDIO client prevents zombies via proper `wait()`
- Force kill after 5s graceful termination timeout
