"""MCP configuration file loader.

This module provides functionality to load and validate MCP server configurations
from JSON files with environment variable substitution support.
"""
import json
import os
import re
from pathlib import Path
from typing import Dict, Any

from pydantic import ValidationError

from app.mcp.config import MCPServersConfig


class MCPConfigError(Exception):
    """Exception raised for MCP configuration errors."""
    pass


def substitute_env_vars(value: str) -> str:
    """Substitute environment variables in a string value.

    Environment variables are specified using ${VAR_NAME} syntax.
    Raises MCPConfigError if a referenced environment variable is not found.

    Args:
        value: String potentially containing environment variable references

    Returns:
        String with environment variables substituted

    Raises:
        MCPConfigError: If a referenced environment variable is not found

    Examples:
        >>> os.environ['API_KEY'] = 'secret123'
        >>> substitute_env_vars('${API_KEY}')
        'secret123'
        >>> substitute_env_vars('https://${HOST}/api')
        'https://localhost/api'
    """
    # Pattern to match ${VAR_NAME}
    pattern = r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}'

    def replace_var(match: re.Match) -> str:
        var_name = match.group(1)
        if var_name not in os.environ:
            raise MCPConfigError(
                f"Environment variable '{var_name}' not found. "
                f"Please set it before loading the configuration."
            )
        return os.environ[var_name]

    return re.sub(pattern, replace_var, value)


def _substitute_env_in_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively substitute environment variables in dictionary values.

    Args:
        data: Dictionary potentially containing environment variable references

    Returns:
        Dictionary with environment variables substituted
    """
    result: Dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = substitute_env_vars(value)
        elif isinstance(value, dict):
            # Recursive substitution for nested dictionaries
            result[key] = _substitute_env_in_dict(value)
        elif isinstance(value, list):
            # Handle list items, preserving type safety
            result[key] = [
                substitute_env_vars(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def load_mcp_config(config_path: str = "mcp_servers.json") -> MCPServersConfig:
    """Load and validate MCP server configuration from JSON file.

    This function:
    1. Reads the JSON configuration file
    2. Substitutes environment variables (${VAR_NAME} syntax)
    3. Validates against the MCPServersConfig schema
    4. Returns a validated configuration object

    Args:
        config_path: Path to the MCP configuration file (default: mcp_servers.json)

    Returns:
        Validated MCPServersConfig object

    Raises:
        MCPConfigError: If the file is not found, contains invalid JSON,
                       fails validation, or has missing environment variables

    Examples:
        >>> config = load_mcp_config('mcp_servers.json')
        >>> enabled_servers = {
        ...     name: server
        ...     for name, server in config.mcpServers.items()
        ...     if server.enabled
        ... }
    """
    # Convert to Path object for easier handling
    config_file = Path(config_path)

    # Check if file exists
    if not config_file.exists():
        raise MCPConfigError(
            f"Configuration file '{config_path}' not found. "
            f"Please create a configuration file or check the path."
        )

    # Read and parse JSON
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except json.JSONDecodeError as e:
        raise MCPConfigError(
            f"Invalid JSON in configuration file '{config_path}': {str(e)}"
        )
    except IOError as e:
        raise MCPConfigError(
            f"Error reading configuration file '{config_path}': {str(e)}"
        )

    # Substitute environment variables
    try:
        processed_data = _substitute_env_in_dict(raw_data)
    except MCPConfigError:
        # Re-raise environment variable errors
        raise
    except Exception as e:
        raise MCPConfigError(
            f"Error processing configuration file '{config_path}': {str(e)}"
        )

    # Validate with Pydantic model
    try:
        config = MCPServersConfig(**processed_data)
    except ValidationError as e:
        error_details = []
        for error in e.errors():
            location = " -> ".join(str(loc) for loc in error['loc'])
            error_details.append(f"{location}: {error['msg']}")

        raise MCPConfigError(
            f"Configuration validation failed for '{config_path}':\n" +
            "\n".join(f"  - {detail}" for detail in error_details)
        )

    return config
