"""Filesystem MCP server integration helper.

This module provides utilities for configuring and validating the
@modelcontextprotocol/server-filesystem MCP server.

The filesystem server allows agents to read, write, and search files
within configured directories using STDIO transport.
"""
import logging
from pathlib import Path
from typing import Optional

from app.mcp.config import MCPServerConfig, TransportType

logger = logging.getLogger(__name__)


class FilesystemServerHelper:
    """Helper for filesystem MCP server configuration and validation.

    The filesystem MCP server is a Node.js package that provides file operations
    through the Model Context Protocol. It uses STDIO transport for communication.

    Configuration example in mcp_servers.json:
    ```json
    {
      "mcpServers": {
        "filesystem": {
          "command": "npx",
          "args": [
            "-y",
            "@modelcontextprotocol/server-filesystem",
            "/path/to/allowed/directory"
          ],
          "transport": "stdio",
          "enabled": true,
          "description": "File system access for agent"
        }
      }
    }
    ```

    Security Considerations:
    - ONLY grant access to necessary directories
    - Use absolute paths to prevent directory traversal
    - Consider read-only access for sensitive directories
    - Never expose system directories (/etc, /usr, etc.)
    - Use environment variables for dynamic paths
    """

    SERVER_PACKAGE = "@modelcontextprotocol/server-filesystem"

    @staticmethod
    def create_config(
        allowed_directory: str,
        enabled: bool = True,
        description: Optional[str] = None,
    ) -> MCPServerConfig:
        """Create filesystem server configuration.

        Args:
            allowed_directory: Absolute path to directory the server can access
            enabled: Whether the server should be enabled
            description: Optional description for the server

        Returns:
            MCPServerConfig configured for filesystem server

        Raises:
            ValueError: If allowed_directory is not an absolute path

        Examples:
            >>> config = FilesystemServerHelper.create_config("/home/user/documents")
            >>> config.command
            'npx'
            >>> config.args
            ['-y', '@modelcontextprotocol/server-filesystem', '/home/user/documents']
        """
        # Validate path
        path = Path(allowed_directory)
        if not path.is_absolute():
            raise ValueError(
                f"Allowed directory must be an absolute path, got: {allowed_directory}"
            )

        # Build configuration
        return MCPServerConfig(
            command="npx",
            args=[
                "-y",  # Yes to package install prompts
                FilesystemServerHelper.SERVER_PACKAGE,
                str(path),
            ],
            transport=TransportType.STDIO,
            enabled=enabled,
            description=description or f"Filesystem access to {path}",
        )

    @staticmethod
    def validate_directory(directory: str) -> tuple[bool, str]:
        """Validate that a directory is safe for filesystem server access.

        Security checks:
        - Directory must be absolute path
        - Directory should exist (warning if not)
        - Directory should not be a system directory
        - Directory should be readable

        Args:
            directory: Directory path to validate

        Returns:
            Tuple of (is_valid, message)
            - is_valid: True if directory is safe to use
            - message: Validation result message
        """
        path = Path(directory)

        # Check absolute path
        if not path.is_absolute():
            return False, f"Path must be absolute: {directory}"

        # Check for dangerous system directories
        dangerous_paths = {"/", "/etc", "/usr", "/bin", "/sbin", "/sys", "/proc", "/dev"}
        if str(path) in dangerous_paths or any(
            str(path).startswith(dp + "/") for dp in dangerous_paths
        ):
            return False, f"Cannot grant access to system directory: {directory}"

        # Check if directory exists
        if not path.exists():
            return True, f"Directory does not exist (will be created if needed): {directory}"

        if not path.is_dir():
            return False, f"Path is not a directory: {directory}"

        # Check readability
        try:
            # Attempt to list directory
            list(path.iterdir())
        except PermissionError:
            return False, f"Directory is not readable: {directory}"

        return True, f"Directory is valid and accessible: {directory}"

    @staticmethod
    def get_available_tools() -> list[str]:
        """Get list of tools provided by filesystem server.

        Returns:
            List of tool names provided by this server

        Note:
            Actual tool schemas should be discovered via tools/list JSON-RPC call.
            This is a static list for documentation purposes.
        """
        return [
            "read_file",       # Read file contents
            "write_file",      # Write content to file
            "list_directory",  # List directory contents
            "create_directory",  # Create a directory
            "move_file",       # Move/rename file
            "search_files",    # Search for files by pattern
        ]

    @staticmethod
    def get_security_recommendations() -> dict[str, list[str]]:
        """Get security recommendations for filesystem server deployment.

        Returns:
            Dictionary of security best practices organized by category
        """
        return {
            "directory_permissions": [
                "Use most restrictive permissions possible",
                "Prefer read-only access when write is not needed",
                "Create dedicated directories for agent file access",
                "Never grant access to system directories",
            ],
            "path_configuration": [
                "Always use absolute paths",
                "Use environment variables for user-specific paths",
                "Document all allowed directories in deployment docs",
                "Audit allowed directories regularly",
            ],
            "container_deployment": [
                "Mount only necessary volumes in container",
                "Use read-only mounts where possible",
                "Implement file size limits",
                "Monitor file system usage and quotas",
            ],
            "monitoring": [
                "Log all file operations via Application Insights",
                "Set up alerts for unusual file access patterns",
                "Track file operation success/failure rates",
                "Monitor disk usage trends",
            ],
        }
