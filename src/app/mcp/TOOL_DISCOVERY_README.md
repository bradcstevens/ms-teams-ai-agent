# MCP Tool Discovery & Registration System

This module provides tool discovery and registration capabilities for MCP (Model Context Protocol) integration with the Azure AI Agent Framework.

## Overview

The tool discovery system enables:
- Automatic discovery of tools from MCP servers via JSON-RPC
- Thread-safe tool registry with name conflict resolution
- Schema conversion from MCP format to Agent Framework format
- Tool execution via JSON-RPC with proper error handling

## Components

### 1. MCPToolSchema (`tool_schema.py`)

Dataclass representing an MCP tool with its schema:

```python
from app.mcp import MCPToolSchema

tool = MCPToolSchema(
    name="read_file",
    description="Read contents of a file",
    input_schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path"}
        },
        "required": ["path"]
    },
    server_name="filesystem",
    full_name="filesystem.read_file"
)
```

### 2. MCPToolRegistry (`registry.py`)

Thread-safe registry for managing discovered tools:

```python
from app.mcp import MCPToolRegistry

registry = MCPToolRegistry()

# Register a tool
full_name = registry.register_tool("filesystem", tool)
# Returns: "filesystem.read_file"

# Retrieve a tool
tool = registry.get_tool("filesystem.read_file")

# List all tools
all_tools = registry.list_tools()

# List tools from specific server
fs_tools = registry.list_tools(server_name="filesystem")

# Remove a tool
registry.remove_tool("filesystem.read_file")

# Clear all tools
registry.clear()
```

**Name Conflict Resolution:**
Tools are automatically prefixed with server name to avoid conflicts:
- `filesystem.read_file`
- `cloud.read_file`

### 3. Tool Discovery (`discovery.py`)

Discover tools from MCP servers via JSON-RPC:

```python
from app.mcp import discover_tools, discover_tools_from_manager

# Discover from single server
async def discover_from_server(client):
    tools = await discover_tools(client)
    for tool in tools:
        print(f"Discovered: {tool.name}")
    return tools

# Discover from all managed servers
async def discover_from_all(manager):
    server_tools = await discover_tools_from_manager(manager)
    # Returns: {"filesystem": [tool1, tool2], "web": [tool3]}
    return server_tools
```

**JSON-RPC Protocol:**
```json
Request:
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 1,
  "params": {}
}

Response:
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "read_file",
        "description": "Read file contents",
        "inputSchema": {
          "type": "object",
          "properties": {
            "path": {"type": "string"}
          },
          "required": ["path"]
        }
      }
    ]
  }
}
```

### 4. Schema Conversion (`tool_schema.py`)

Convert MCP schemas to Agent Framework format:

```python
from app.mcp import mcp_to_agent_framework

# Convert tool schema
agent_format = mcp_to_agent_framework(tool)
# Returns:
# {
#   "name": "filesystem.read_file",
#   "description": "Read contents of a file",
#   "parameters": {
#     "type": "object",
#     "properties": {
#       "path": {"type": "string", "description": "File path"}
#     },
#     "required": ["path"]
#   }
# }
```

**Supported Schema Features:**
- Nested objects
- Arrays with item schemas
- Enums
- Default values
- Optional vs required parameters
- All JSON Schema types (string, number, integer, boolean, object, array)

### 5. MCPToolBridge (`bridge.py`)

Bridge for executing tools and Agent Framework integration:

```python
from app.mcp import MCPToolBridge

# Initialize bridge
bridge = MCPToolBridge(registry, manager)

# Execute a tool
async def run_tool():
    result = await bridge.execute_tool(
        "filesystem.read_file",
        {"path": "/workspace/file.txt"}
    )
    return result

# Get tools in Agent Framework format
agent_tools = bridge.get_available_tools()
# Returns list of tools ready for Agent Framework
```

**Tool Execution (JSON-RPC):**
```json
Request:
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "id": 2,
  "params": {
    "name": "read_file",
    "arguments": {
      "path": "/workspace/file.txt"
    }
  }
}

Response:
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": "file contents here..."
  }
}
```

## Complete Usage Example

```python
import asyncio
from app.mcp import (
    MCPConnectionManager,
    MCPToolRegistry,
    MCPToolBridge,
    discover_tools_from_manager
)

async def main():
    # Initialize components
    manager = MCPConnectionManager()
    registry = MCPToolRegistry()
    bridge = MCPToolBridge(registry, manager)

    # Connect to MCP servers
    await manager.connect_server("filesystem", filesystem_config)
    await manager.connect_server("web", web_config)

    # Discover tools from all servers
    server_tools = await discover_tools_from_manager(manager)

    # Register discovered tools
    for server_name, tools in server_tools.items():
        for tool in tools:
            full_name = registry.register_tool(server_name, tool)
            print(f"Registered: {full_name}")

    # Get tools for Agent Framework
    agent_tools = bridge.get_available_tools()
    print(f"Available tools: {len(agent_tools)}")

    # Execute a tool
    result = await bridge.execute_tool(
        "filesystem.read_file",
        {"path": "/workspace/config.json"}
    )
    print(f"Result: {result}")

    # Cleanup
    await manager.disconnect_all()

asyncio.run(main())
```

## Error Handling

All operations handle MCP-specific errors:

```python
from app.mcp.exceptions import (
    MCPConnectionError,
    MCPTimeoutError,
    MCPTransportError
)

try:
    tools = await discover_tools(client)
except MCPConnectionError as e:
    print(f"Connection error: {e}")
except MCPTimeoutError as e:
    print(f"Request timed out: {e}")
except MCPTransportError as e:
    print(f"Transport error: {e}")
```

## Thread Safety

The `MCPToolRegistry` is thread-safe and can be used concurrently:

```python
from concurrent.futures import ThreadPoolExecutor

def register_tool(server_name, tool):
    return registry.register_tool(server_name, tool)

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [
        executor.submit(register_tool, "server1", tool)
        for tool in tools
    ]
    results = [f.result() for f in futures]
```

## Testing

Comprehensive test suite with 69 tests:
- Schema conversion: 15 tests
- Registry management: 19 tests (including thread safety)
- Tool discovery: 17 tests (with error handling)
- Bridge integration: 18 tests (execution and listing)

Run tests:
```bash
pytest tests/test_mcp_tool_schema.py -v
pytest tests/test_mcp_registry.py -v
pytest tests/test_mcp_discovery.py -v
pytest tests/test_mcp_bridge.py -v
```

## Integration with Agent Framework

The tool discovery system integrates with Task 3.6 (Agent Framework Tool Bridge):

1. **Tool Discovery**: Automatic discovery from MCP servers
2. **Schema Conversion**: MCP format to Agent Framework format
3. **Tool Registration**: Centralized registry with conflict resolution
4. **Tool Execution**: JSON-RPC routing to correct MCP server

Ready for full Agent Framework integration!
