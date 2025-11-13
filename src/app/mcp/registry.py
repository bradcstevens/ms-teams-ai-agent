"""MCP tool registry for managing discovered tools.

This module provides a thread-safe registry for storing and retrieving MCP tools
with automatic name conflict resolution.
"""
import threading
from typing import Optional

from app.mcp.tool_schema import MCPToolSchema


class MCPToolRegistry:
    """Thread-safe registry for MCP tools.

    Stores tools with metadata and handles name conflicts by prefixing with server name.
    All operations are thread-safe using a lock.
    """

    def __init__(self):
        """Initialize an empty tool registry."""
        self._tools: dict[str, MCPToolSchema] = {}
        self._lock = threading.Lock()

    def register_tool(self, server_name: str, tool: MCPToolSchema) -> str:
        """Register a tool in the registry.

        Sets server_name and full_name metadata on the tool.
        Full name is constructed as 'server_name.tool_name' to avoid conflicts.

        Args:
            server_name: Name of the MCP server providing this tool
            tool: Tool schema to register

        Returns:
            Full name of the registered tool (server_name.tool_name)
        """
        with self._lock:
            # Construct full name with server prefix
            full_name = f"{server_name}.{tool.name}"

            # Set metadata on tool
            tool.server_name = server_name
            tool.full_name = full_name

            # Store in registry
            self._tools[full_name] = tool

            return full_name

    def get_tool(self, full_name: str) -> Optional[MCPToolSchema]:
        """Retrieve a tool by its full name.

        Args:
            full_name: Full name of the tool (server_name.tool_name)

        Returns:
            Tool schema if found, None otherwise
        """
        with self._lock:
            return self._tools.get(full_name)

    def list_tools(self, server_name: Optional[str] = None) -> list[MCPToolSchema]:
        """List all registered tools, optionally filtered by server.

        Args:
            server_name: If provided, only return tools from this server

        Returns:
            List of tool schemas (independent copy)
        """
        with self._lock:
            if server_name is None:
                # Return all tools
                return list(self._tools.values())
            else:
                # Filter by server name
                return [
                    tool
                    for tool in self._tools.values()
                    if tool.server_name == server_name
                ]

    def remove_tool(self, full_name: str) -> bool:
        """Remove a tool from the registry.

        Args:
            full_name: Full name of the tool to remove

        Returns:
            True if tool was removed, False if it didn't exist
        """
        with self._lock:
            if full_name in self._tools:
                del self._tools[full_name]
                return True
            return False

    def clear(self) -> None:
        """Clear all tools from the registry."""
        with self._lock:
            self._tools.clear()

    def get_tool_count(self) -> int:
        """Get the total number of registered tools.

        Returns:
            Number of tools in the registry
        """
        with self._lock:
            return len(self._tools)
