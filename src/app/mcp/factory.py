"""MCP client factory for creating transport-aware client instances.

This module provides a factory for creating the appropriate MCP client
based on the configured transport type (STDIO or SSE).
"""
from app.mcp.client import MCPClient, MCPSSEClient, MCPSTDIOClient
from app.mcp.config import MCPServerConfig, TransportType


class MCPClientFactory:
    """Factory for creating MCP clients based on transport type."""

    @staticmethod
    def create_client(config: MCPServerConfig) -> MCPClient:
        """Create an MCP client instance based on the configured transport.

        Args:
            config: MCP server configuration specifying transport type

        Returns:
            Appropriate MCPClient instance (MCPSTDIOClient or MCPSSEClient)

        Raises:
            ValueError: If transport type is not supported
        """
        if config.transport == TransportType.STDIO:
            return MCPSTDIOClient(config)
        elif config.transport == TransportType.SSE:
            return MCPSSEClient(config)
        else:
            raise ValueError(f"Unsupported transport type: {config.transport}")
