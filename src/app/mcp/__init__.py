"""MCP (Model Context Protocol) Integration Module.

This module provides MCP server configuration and management for the Azure AI Agent Framework.
"""
from app.mcp.bridge import MCPToolBridge
from app.mcp.circuit_breaker import CircuitBreaker, CircuitState
from app.mcp.client import MCPClient, MCPSTDIOClient, MCPSSEClient
from app.mcp.config import MCPServerConfig, MCPServersConfig, TransportType
from app.mcp.discovery import discover_tools, discover_tools_from_manager
from app.mcp.exceptions import MCPConnectionError, MCPTimeoutError, MCPTransportError
from app.mcp.factory import MCPClientFactory
from app.mcp.loader import MCPConfigError, load_mcp_config
from app.mcp.manager import MCPConnectionManager
from app.mcp.registry import MCPToolRegistry
from app.mcp.tool_schema import MCPToolSchema, mcp_to_agent_framework

__all__ = [
    # Configuration
    "MCPServerConfig",
    "MCPServersConfig",
    "TransportType",
    "load_mcp_config",
    "MCPConfigError",
    # Clients
    "MCPClient",
    "MCPSTDIOClient",
    "MCPSSEClient",
    "MCPClientFactory",
    # Manager
    "MCPConnectionManager",
    # Tool Discovery & Registry
    "MCPToolSchema",
    "MCPToolRegistry",
    "discover_tools",
    "discover_tools_from_manager",
    "mcp_to_agent_framework",
    # Bridge
    "MCPToolBridge",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitState",
    # Exceptions
    "MCPConnectionError",
    "MCPTimeoutError",
    "MCPTransportError",
]
