"""MCP connection manager with pooling and lifecycle management.

This module provides a connection manager that handles:
- Connection pooling for multiple MCP servers
- Retry logic with exponential backoff and jitter
- Health check monitoring
- Graceful shutdown and cleanup
"""
import asyncio
import logging
import random
from typing import Dict, Optional

from app.mcp.client import MCPClient
from app.mcp.config import MCPServerConfig, MCPServersConfig
from app.mcp.exceptions import MCPConnectionError
from app.mcp.factory import MCPClientFactory

logger = logging.getLogger(__name__)


class MCPConnectionManager:
    """Manages connections to multiple MCP servers with pooling and lifecycle management."""

    def __init__(self):
        """Initialize the connection manager."""
        self._config: Optional[MCPServersConfig] = None
        self._clients: Dict[str, MCPClient] = {}
        self._server_configs: Dict[str, MCPServerConfig] = {}

    async def initialize(self, config: MCPServersConfig) -> None:
        """Initialize manager with server configurations.

        Args:
            config: MCP servers configuration
        """
        self._config = config
        self._server_configs = config.mcpServers.copy()
        logger.info(f"Initialized MCP connection manager with {len(self._server_configs)} servers")

    async def connect_server(self, server_name: str, max_retries: int = 3) -> bool:
        """Connect to a specific MCP server with retry logic.

        Args:
            server_name: Name of the server to connect to
            max_retries: Maximum number of connection retry attempts

        Returns:
            True if connection successful

        Raises:
            MCPConnectionError: If server not found, disabled, or connection fails after retries
        """
        if server_name not in self._server_configs:
            raise MCPConnectionError(f"Server '{server_name}' not found in configuration")

        config = self._server_configs[server_name]

        if not config.enabled:
            raise MCPConnectionError(f"Server '{server_name}' is disabled")

        # Create client using factory
        client = MCPClientFactory.create_client(config)

        # Retry with exponential backoff
        last_error = None
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to '{server_name}' (attempt {attempt + 1}/{max_retries})")
                result = await client.connect()

                if result:
                    self._clients[server_name] = client
                    logger.info(f"Successfully connected to '{server_name}'")
                    return True

            except MCPConnectionError as e:
                last_error = e
                logger.warning(f"Connection attempt {attempt + 1} failed for '{server_name}': {e}")

                if attempt < max_retries - 1:
                    # Calculate backoff delay
                    delay = self._calculate_backoff(attempt)
                    logger.info(f"Retrying in {delay}s...")
                    await asyncio.sleep(delay)

        # All retries exhausted
        error_msg = f"Failed to connect to '{server_name}' after {max_retries} attempts"
        if last_error:
            error_msg += f": {last_error}"
        raise MCPConnectionError(error_msg)

    async def disconnect_server(self, server_name: str) -> None:
        """Disconnect from a specific MCP server.

        Args:
            server_name: Name of the server to disconnect from

        Raises:
            MCPConnectionError: If server not found or not connected
        """
        if server_name not in self._clients:
            raise MCPConnectionError(f"Server '{server_name}' is not connected")

        client = self._clients[server_name]
        await client.disconnect()
        del self._clients[server_name]
        logger.info(f"Disconnected from '{server_name}'")

    async def get_client(self, server_name: str) -> MCPClient:
        """Get the client instance for a connected server.

        Args:
            server_name: Name of the server

        Returns:
            MCPClient instance

        Raises:
            MCPConnectionError: If server not connected
        """
        if server_name not in self._clients:
            raise MCPConnectionError(
                f"Server '{server_name}' is not connected. Call connect_server() first."
            )

        return self._clients[server_name]

    async def health_check_all(self) -> Dict[str, bool]:
        """Perform health check on all connected servers.

        Returns:
            Dictionary mapping server names to health status (True=healthy, False=unhealthy)
        """
        health_status = {}

        for server_name, client in self._clients.items():
            try:
                is_healthy = await client.is_healthy()
                health_status[server_name] = is_healthy
                logger.debug(f"Health check for '{server_name}': {is_healthy}")
            except Exception as e:
                logger.error(f"Health check failed for '{server_name}': {e}")
                health_status[server_name] = False

        return health_status

    async def connect_all_enabled(self) -> Dict[str, bool]:
        """Connect to all enabled servers in parallel.

        Returns:
            Dictionary mapping server names to connection results (True=success, False=failure)
        """
        results = {}

        # Create connection tasks for all enabled servers
        tasks = []
        server_names = []

        for server_name, config in self._server_configs.items():
            if config.enabled:
                tasks.append(self.connect_server(server_name))
                server_names.append(server_name)

        # Execute all connections in parallel
        if tasks:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)

            for server_name, result in zip(server_names, task_results):
                # Type narrowing: result can be bool or BaseException
                if isinstance(result, Exception):
                    logger.error(f"Failed to connect to '{server_name}': {result}")
                    results[server_name] = False
                elif isinstance(result, bool):
                    # Explicit type check to satisfy mypy
                    results[server_name] = result
                else:
                    # Fallback for unexpected types
                    results[server_name] = False

        return results

    async def shutdown(self) -> None:
        """Gracefully shutdown all connections.

        Disconnects from all connected servers and cleans up resources.
        """
        logger.info("Shutting down MCP connection manager...")

        # Disconnect all clients
        disconnect_tasks = []
        for server_name in list(self._clients.keys()):
            disconnect_tasks.append(self.disconnect_server(server_name))

        if disconnect_tasks:
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)

        self._clients.clear()
        logger.info("MCP connection manager shutdown complete")

    async def get_server_status(self) -> Dict[str, Dict[str, bool]]:
        """Get detailed status of all configured servers.

        Returns:
            Dictionary mapping server names to status info (connected, enabled)
        """
        status = {}

        for server_name, config in self._server_configs.items():
            status[server_name] = {
                "enabled": config.enabled,
                "connected": server_name in self._clients,
            }

        return status

    def list_servers(self) -> list[str]:
        """Get list of all configured server names.

        Returns:
            List of server names from configuration
        """
        return list(self._server_configs.keys())

    def _calculate_backoff(
        self, attempt: int, base_delay: float = 1.0, max_delay: float = 30.0, jitter: bool = True
    ) -> float:
        """Calculate exponential backoff delay with optional jitter.

        Args:
            attempt: Current attempt number (0-indexed)
            base_delay: Base delay in seconds
            max_delay: Maximum delay cap in seconds
            jitter: Whether to add random jitter to prevent thundering herd

        Returns:
            Delay in seconds
        """
        delay = base_delay * (2**attempt)
        delay = min(delay, max_delay)

        if jitter:
            # Add random jitter (0-50% of delay)
            jitter_amount = delay * random.uniform(0, 0.5)
            delay += jitter_amount

        return delay
