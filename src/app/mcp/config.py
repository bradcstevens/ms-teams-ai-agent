"""MCP server configuration models and schema.

This module defines Pydantic models for MCP (Model Context Protocol) server configuration.
It provides JSON schema validation, type checking, and default values for MCP server settings.
"""
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class TransportType(str, Enum):
    """Supported MCP transport types.

    STDIO: Standard input/output communication (process-based)
    SSE: Server-Sent Events over HTTP
    """
    STDIO = "stdio"
    SSE = "sse"


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server.

    Attributes:
        command: Executable command to start the server (required)
        args: Command-line arguments to pass to the server
        env: Environment variables to set for the server process
        enabled: Whether the server is enabled (default: True)
        transport: Communication transport type (default: stdio)
        description: Human-readable description of the server
    """
    command: str = Field(
        ...,
        description="Executable command to start the MCP server",
        min_length=1,
    )
    args: List[str] = Field(
        default_factory=list,
        description="Command-line arguments for the server",
    )
    env: Dict[str, str] = Field(
        default_factory=dict,
        description="Environment variables for the server process",
    )
    enabled: bool = Field(
        default=True,
        description="Whether the server is enabled",
    )
    transport: TransportType = Field(
        default=TransportType.STDIO,
        description="Communication transport type",
    )
    description: Optional[str] = Field(
        default=None,
        description="Human-readable server description",
    )

    @field_validator("command")
    @classmethod
    def validate_command(cls, v: str) -> str:
        """Validate command is not empty after stripping whitespace."""
        if not v or not v.strip():
            raise ValueError("Command cannot be empty")
        return v.strip()


class MCPServersConfig(BaseModel):
    """Root configuration model for all MCP servers.

    Attributes:
        mcpServers: Dictionary mapping server names to their configurations
    """
    mcpServers: Dict[str, MCPServerConfig] = Field(
        default_factory=dict,
        description="MCP server configurations keyed by server name",
    )

    @field_validator("mcpServers")
    @classmethod
    def validate_server_names(cls, v: Dict[str, MCPServerConfig]) -> Dict[str, MCPServerConfig]:
        """Validate server names are valid identifiers."""
        for name in v.keys():
            if not name or not name.strip():
                raise ValueError("Server name cannot be empty")
            # Check for valid server name (alphanumeric, hyphens, underscores)
            if not all(c.isalnum() or c in ("-", "_") for c in name):
                raise ValueError(
                    f"Server name '{name}' contains invalid characters. "
                    "Use only alphanumeric characters, hyphens, and underscores."
                )
        return v
