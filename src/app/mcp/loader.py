"""MCP configuration file loader.

This module provides functionality to load and validate MCP server configurations
from JSON files with environment variable substitution support.
"""
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional

from pydantic import ValidationError

from app.mcp.config import MCPServersConfig, MCPServerConfig, parse_env_var_servers

logger = logging.getLogger(__name__)


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
    """Load and validate MCP server configuration from JSON file and environment variables.

    This function:
    1. Attempts to read the JSON configuration file (optional if env vars present)
    2. Substitutes environment variables (${VAR_NAME} syntax) in JSON config
    3. Parses MCP server configurations from environment variables
    4. Merges configurations (environment variables override JSON)
    5. Validates against the MCPServersConfig schema
    6. Returns a validated configuration object

    Configuration sources (in priority order):
    1. Environment variables (MCP_SERVER_N_*) - highest priority
    2. JSON configuration file - lower priority

    Args:
        config_path: Path to the MCP configuration file (default: mcp_servers.json)

    Returns:
        Validated MCPServersConfig object

    Raises:
        MCPConfigError: If configuration fails validation or has missing environment variables

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

    # Initialize with empty servers dict
    json_servers: Dict[str, MCPServerConfig] = {}

    # Try to load JSON configuration (optional if env vars present)
    if config_file.exists():
        logger.info(f"Loading MCP configuration from JSON file: {config_path}")

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

        # Substitute environment variables in JSON
        try:
            processed_data = _substitute_env_in_dict(raw_data)
        except MCPConfigError:
            # Re-raise environment variable errors
            raise
        except Exception as e:
            raise MCPConfigError(
                f"Error processing configuration file '{config_path}': {str(e)}"
            )

        # Extract servers from JSON
        if "mcpServers" in processed_data:
            try:
                # Validate JSON servers
                json_config = MCPServersConfig(**processed_data)
                json_servers = json_config.mcpServers
                logger.info(f"Loaded {len(json_servers)} server(s) from JSON configuration")
            except ValidationError as e:
                error_details = []
                for error in e.errors():
                    location = " -> ".join(str(loc) for loc in error['loc'])
                    error_details.append(f"{location}: {error['msg']}")

                raise MCPConfigError(
                    f"JSON configuration validation failed for '{config_path}':\n" +
                    "\n".join(f"  - {detail}" for detail in error_details)
                )
    else:
        logger.info(f"JSON configuration file not found: {config_path}, checking environment variables")

    # Parse environment variable servers
    env_servers = parse_env_var_servers()
    if env_servers:
        logger.info(f"Loaded {len(env_servers)} server(s) from environment variables")

    # Merge configurations: start with JSON, override with env vars
    merged_servers: Dict[str, MCPServerConfig] = {}

    # Add all JSON servers first
    for name, server in json_servers.items():
        merged_servers[name] = server
        logger.debug(f"Added server '{name}' from JSON configuration")

    # Override with environment variable servers
    for name, server in env_servers.items():
        if name in merged_servers:
            logger.info(f"Environment variable overriding JSON configuration for server '{name}'")
        else:
            logger.debug(f"Added server '{name}' from environment variables")
        merged_servers[name] = server

    # Log final configuration summary
    total_servers = len(merged_servers)
    enabled_count = sum(1 for s in merged_servers.values() if s.enabled)
    logger.info(
        f"MCP configuration loaded: {total_servers} total server(s), "
        f"{enabled_count} enabled, {total_servers - enabled_count} disabled"
    )

    # Create final configuration object
    final_config = MCPServersConfig(mcpServers=merged_servers)

    return final_config
