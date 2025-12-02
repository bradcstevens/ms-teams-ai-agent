"""MCP server configuration models and schema.

This module defines Pydantic models for MCP (Model Context Protocol) server configuration.
It provides JSON schema validation, type checking, and default values for MCP server settings.
"""
import os
import re
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


def _parse_server_env_vars(prefix: str) -> Dict[str, str]:
    """Parse environment variables for a specific MCP server.

    Extracts MCP_SERVER_N_ENV_* variables and converts them to server env dict.

    Args:
        prefix: Environment variable prefix (e.g., "MCP_SERVER_1")

    Returns:
        Dictionary of environment variables for the server

    Examples:
        >>> os.environ["MCP_SERVER_1_ENV_API_KEY"] = "secret"
        >>> _parse_server_env_vars("MCP_SERVER_1")
        {"API_KEY": "secret"}
    """
    env_vars = {}
    env_prefix = f"{prefix}_ENV_"

    for key, value in os.environ.items():
        if key.startswith(env_prefix):
            # Extract the environment variable name after ENV_
            env_var_name = key[len(env_prefix):]
            env_vars[env_var_name] = value

    return env_vars


def parse_env_var_servers(prefix: str = "MCP_SERVER_") -> Dict[str, MCPServerConfig]:
    """Parse MCP server configurations from environment variables.

    Supports the following environment variable format:
    - MCP_SERVER_N_NAME: Server name (required)
    - MCP_SERVER_N_COMMAND: Command to execute (required)
    - MCP_SERVER_N_ARGS: Comma-separated arguments
    - MCP_SERVER_N_TRANSPORT: Transport type (stdio or sse)
    - MCP_SERVER_N_ENABLED: Boolean enabled flag (true/false)
    - MCP_SERVER_N_DESCRIPTION: Server description
    - MCP_SERVER_N_ENV_*: Environment variables for the server

    MCP_SERVER_COUNT can be used as an optimization hint to limit iteration.

    Args:
        prefix: Environment variable prefix (default: "MCP_SERVER_")

    Returns:
        Dictionary mapping server names to MCPServerConfig objects

    Examples:
        >>> os.environ["MCP_SERVER_1_NAME"] = "filesystem"
        >>> os.environ["MCP_SERVER_1_COMMAND"] = "npx"
        >>> os.environ["MCP_SERVER_1_ARGS"] = "-y,mcp-server-filesystem"
        >>> servers = parse_env_var_servers()
        >>> assert "filesystem" in servers
    """
    servers: Dict[str, MCPServerConfig] = {}

    # Use MCP_SERVER_COUNT as optimization hint if provided
    max_count = int(os.environ.get("MCP_SERVER_COUNT", "100"))

    # Iterate through potential server indices
    for i in range(1, max_count + 1):
        server_prefix = f"{prefix}{i}"
        name_key = f"{server_prefix}_NAME"

        # Check if this server exists
        if name_key not in os.environ:
            # If we have a count hint and haven't found servers in a while, stop
            if "MCP_SERVER_COUNT" in os.environ and i > int(os.environ["MCP_SERVER_COUNT"]):
                break
            continue

        server_name = os.environ[name_key]
        command_key = f"{server_prefix}_COMMAND"

        # Command is required
        if command_key not in os.environ:
            continue

        command = os.environ[command_key]

        # Parse optional fields
        args_key = f"{server_prefix}_ARGS"
        args = []
        if args_key in os.environ:
            # Split comma-separated args
            args = [arg.strip() for arg in os.environ[args_key].split(",") if arg.strip()]

        transport_key = f"{server_prefix}_TRANSPORT"
        transport = TransportType.STDIO
        if transport_key in os.environ:
            transport_value = os.environ[transport_key].lower()
            if transport_value == "sse":
                transport = TransportType.SSE

        enabled_key = f"{server_prefix}_ENABLED"
        enabled = True
        if enabled_key in os.environ:
            enabled = os.environ[enabled_key].lower() in ("true", "1", "yes")

        description_key = f"{server_prefix}_DESCRIPTION"
        description = os.environ.get(description_key, None)

        # Parse server environment variables
        env_vars = _parse_server_env_vars(server_prefix)

        # Create server configuration
        server_config = MCPServerConfig(
            command=command,
            args=args,
            env=env_vars,
            enabled=enabled,
            transport=transport,
            description=description,
        )

        servers[server_name] = server_config

    return servers
