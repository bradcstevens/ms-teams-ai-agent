"""MCP to Agent Framework bridge.

This module provides basic integration between MCP tools and the Azure AI Agent Framework.
"""
from typing import Any

from app.mcp.exceptions import MCPConnectionError
from app.mcp.manager import MCPConnectionManager
from app.mcp.registry import MCPToolRegistry
from app.mcp.tool_schema import mcp_to_agent_framework


class MCPToolBridge:
    """Bridge between MCP tools and Agent Framework.

    Provides tool execution and listing functionality for Agent Framework integration.
    """

    def __init__(self, registry: MCPToolRegistry, manager: MCPConnectionManager):
        """Initialize the bridge.

        Args:
            registry: Tool registry containing available tools
            manager: Connection manager for routing requests to servers
        """
        self.registry = registry
        self.manager = manager
        self._request_id = 0

    async def execute_tool(self, full_tool_name: str, params: dict[str, Any]) -> Any:
        """Execute a tool by routing to the appropriate MCP server.

        Sends a JSON-RPC 'tools/call' request with the tool name and parameters.

        Args:
            full_tool_name: Full name of tool (server_name.tool_name)
            params: Tool parameters dictionary

        Returns:
            Result from the tool execution

        Raises:
            ValueError: If tool is not found in registry
            MCPConnectionError: If no client is available for the server
            MCPTimeoutError: If request times out
            MCPTransportError: If transport error occurs
            Exception: If server returns an error response
        """
        # Get tool from registry
        tool = self.registry.get_tool(full_tool_name)
        if tool is None:
            raise ValueError(f"Tool not found: {full_tool_name}")

        # Get client for the tool's server (async operation)
        client = await self.manager.get_client(tool.server_name)
        if client is None:
            raise MCPConnectionError(f"No client available for server: {tool.server_name}")

        # Prepare JSON-RPC tools/call request
        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": self._request_id,
            "params": {"name": tool.name, "arguments": params},
        }

        # Send request
        response = await client.send_request(request)

        # Check for error response
        if "error" in response:
            error = response["error"]
            raise Exception(f"Tool execution error: {error.get('message', 'Unknown error')}")

        # Return result
        return response.get("result")

    def get_available_tools(self) -> list[dict[str, Any]]:
        """Get all available tools in Agent Framework format.

        Returns:
            List of tool definitions in Agent Framework format
        """
        tools = self.registry.list_tools()

        # Convert each tool to Agent Framework format
        return [mcp_to_agent_framework(tool) for tool in tools]
