"""MCP tool discovery utilities.

This module provides functions for discovering tools from MCP servers via JSON-RPC.
"""

from app.mcp.client import MCPClient
from app.mcp.exceptions import MCPConnectionError, MCPTimeoutError, MCPTransportError
from app.mcp.manager import MCPConnectionManager
from app.mcp.tool_schema import MCPToolSchema


async def discover_tools(client: MCPClient) -> list[MCPToolSchema]:
    """Discover tools from an MCP server.

    Sends a JSON-RPC 'tools/list' request to the server and parses the response.

    Args:
        client: Connected MCP client

    Returns:
        List of discovered tool schemas

    Raises:
        MCPConnectionError: If client is not connected
        MCPTimeoutError: If request times out
        MCPTransportError: If transport error occurs
        ValueError: If response contains invalid tool schemas
        KeyError: If required tool fields are missing
    """
    # Prepare JSON-RPC request
    request = {"jsonrpc": "2.0", "method": "tools/list", "id": 1, "params": {}}

    # Send request and get response
    try:
        response = await client.send_request(request)
    except (MCPConnectionError, MCPTimeoutError, MCPTransportError):
        # Re-raise MCP exceptions
        raise

    # Parse response
    if "result" not in response:
        return []

    result = response["result"]
    if "tools" not in result:
        return []

    # Convert tools to MCPToolSchema objects
    tools = []
    for tool_data in result["tools"]:
        # Validate required fields
        if "name" not in tool_data:
            raise ValueError("Tool missing required 'name' field")

        # MCP spec uses 'inputSchema', convert to our format
        input_schema = tool_data.get("inputSchema", {"type": "object", "properties": {}})

        tool = MCPToolSchema(
            name=tool_data["name"],
            description=tool_data.get("description", ""),
            input_schema=input_schema,
        )
        tools.append(tool)

    return tools


async def discover_tools_from_manager(
    manager: MCPConnectionManager,
) -> dict[str, list[MCPToolSchema]]:
    """Discover tools from all servers managed by a connection manager.

    Args:
        manager: MCP connection manager with active servers

    Returns:
        Dictionary mapping server names to their tool lists.
        Servers with errors are omitted from the results.
    """
    result: dict[str, list[MCPToolSchema]] = {}

    # Get list of all servers
    server_names = manager.list_servers()

    # Discover tools from each server
    for server_name in server_names:
        try:
            # Get client for this server (async operation)
            client = await manager.get_client(server_name)
            if client is None:
                continue

            # Discover tools
            tools = await discover_tools(client)
            result[server_name] = tools

        except (MCPConnectionError, MCPTimeoutError, MCPTransportError):
            # Skip servers with errors
            continue

    return result
