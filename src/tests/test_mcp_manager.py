"""Tests for MCP connection manager with pooling and lifecycle management."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.mcp.manager import MCPConnectionManager
from app.mcp.config import MCPServerConfig, MCPServersConfig, TransportType
from app.mcp.exceptions import MCPConnectionError


class TestMCPConnectionManager:
    """Test suite for MCP connection manager."""

    @pytest.mark.asyncio
    async def test_manager_initialization(self):
        """Test manager initializes with configuration."""
        config = MCPServersConfig(
            mcpServers={
                "filesystem": MCPServerConfig(
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                    transport=TransportType.STDIO,
                )
            }
        )

        manager = MCPConnectionManager()
        await manager.initialize(config)

        assert manager is not None

    @pytest.mark.asyncio
    async def test_manager_connect_server_success(self):
        """Test manager successfully connects to a server."""
        config = MCPServersConfig(
            mcpServers={
                "filesystem": MCPServerConfig(
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                    transport=TransportType.STDIO,
                    enabled=True,
                )
            }
        )

        manager = MCPConnectionManager()
        await manager.initialize(config)

        with patch("app.mcp.client.MCPSTDIOClient.connect", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = True

            result = await manager.connect_server("filesystem")

            assert result is True
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_manager_connect_server_failure(self):
        """Test manager handles server connection failure."""
        config = MCPServersConfig(
            mcpServers={
                "filesystem": MCPServerConfig(
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                    transport=TransportType.STDIO,
                    enabled=True,
                )
            }
        )

        manager = MCPConnectionManager()
        await manager.initialize(config)

        with patch("app.mcp.client.MCPSTDIOClient.connect", new_callable=AsyncMock) as mock_connect:
            mock_connect.side_effect = MCPConnectionError("Failed to connect")

            with pytest.raises(MCPConnectionError):
                await manager.connect_server("filesystem")

    @pytest.mark.asyncio
    async def test_manager_connection_pooling(self):
        """Test manager maintains connection pool for multiple servers."""
        config = MCPServersConfig(
            mcpServers={
                "filesystem": MCPServerConfig(
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                    transport=TransportType.STDIO,
                    enabled=True,
                ),
                "api": MCPServerConfig(
                    command="http://localhost:8080/sse",
                    transport=TransportType.SSE,
                    enabled=True,
                ),
            }
        )

        manager = MCPConnectionManager()
        await manager.initialize(config)

        with patch("app.mcp.client.MCPSTDIOClient.connect", new_callable=AsyncMock) as mock_stdio:
            with patch("app.mcp.client.MCPSSEClient.connect", new_callable=AsyncMock) as mock_sse:
                mock_stdio.return_value = True
                mock_sse.return_value = True

                await manager.connect_server("filesystem")
                await manager.connect_server("api")

                filesystem_client = await manager.get_client("filesystem")
                api_client = await manager.get_client("api")

                assert filesystem_client is not None
                assert api_client is not None
                assert filesystem_client != api_client

    @pytest.mark.asyncio
    async def test_manager_get_client_not_connected(self):
        """Test manager raises error when getting client that's not connected."""
        config = MCPServersConfig(
            mcpServers={
                "filesystem": MCPServerConfig(
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                    transport=TransportType.STDIO,
                )
            }
        )

        manager = MCPConnectionManager()
        await manager.initialize(config)

        with pytest.raises(MCPConnectionError):
            await manager.get_client("filesystem")

    @pytest.mark.asyncio
    async def test_manager_disconnect_server(self):
        """Test manager properly disconnects from server."""
        config = MCPServersConfig(
            mcpServers={
                "filesystem": MCPServerConfig(
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                    transport=TransportType.STDIO,
                    enabled=True,
                )
            }
        )

        manager = MCPConnectionManager()
        await manager.initialize(config)

        with patch("app.mcp.client.MCPSTDIOClient.connect", new_callable=AsyncMock) as mock_connect:
            with patch("app.mcp.client.MCPSTDIOClient.disconnect", new_callable=AsyncMock) as mock_disconnect:
                mock_connect.return_value = True

                await manager.connect_server("filesystem")
                await manager.disconnect_server("filesystem")

                mock_disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_manager_retry_with_exponential_backoff(self):
        """Test manager retries failed connections with exponential backoff."""
        config = MCPServersConfig(
            mcpServers={
                "filesystem": MCPServerConfig(
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                    transport=TransportType.STDIO,
                    enabled=True,
                )
            }
        )

        manager = MCPConnectionManager()
        await manager.initialize(config)

        connection_attempts = []

        async def mock_connect_with_failure():
            connection_attempts.append(asyncio.get_event_loop().time())
            if len(connection_attempts) < 3:
                raise MCPConnectionError("Connection failed")
            return True

        with patch("app.mcp.client.MCPSTDIOClient.connect", new_callable=AsyncMock) as mock_connect:
            mock_connect.side_effect = mock_connect_with_failure

            result = await manager.connect_server("filesystem", max_retries=3)

            assert result is True
            assert len(connection_attempts) == 3

            # Verify exponential backoff (times should increase: 0s, ~1s, ~2s)
            if len(connection_attempts) >= 3:
                time_diff_1 = connection_attempts[1] - connection_attempts[0]
                time_diff_2 = connection_attempts[2] - connection_attempts[1]
                # Second delay should be roughly double the first
                assert time_diff_2 > time_diff_1

    @pytest.mark.asyncio
    async def test_manager_retry_max_attempts_reached(self):
        """Test manager stops retrying after max attempts."""
        config = MCPServersConfig(
            mcpServers={
                "filesystem": MCPServerConfig(
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                    transport=TransportType.STDIO,
                    enabled=True,
                )
            }
        )

        manager = MCPConnectionManager()
        await manager.initialize(config)

        with patch("app.mcp.client.MCPSTDIOClient.connect", new_callable=AsyncMock) as mock_connect:
            mock_connect.side_effect = MCPConnectionError("Always fails")

            with pytest.raises(MCPConnectionError):
                await manager.connect_server("filesystem", max_retries=3)

            # Should have tried 3 times (initial + 2 retries)
            assert mock_connect.call_count == 3

    @pytest.mark.asyncio
    async def test_manager_health_check_all_servers(self):
        """Test manager can health check all connected servers."""
        config = MCPServersConfig(
            mcpServers={
                "filesystem": MCPServerConfig(
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                    transport=TransportType.STDIO,
                    enabled=True,
                ),
                "api": MCPServerConfig(
                    command="http://localhost:8080/sse",
                    transport=TransportType.SSE,
                    enabled=True,
                ),
            }
        )

        manager = MCPConnectionManager()
        await manager.initialize(config)

        with patch("app.mcp.client.MCPSTDIOClient.connect", new_callable=AsyncMock) as mock_stdio_connect:
            with patch("app.mcp.client.MCPSSEClient.connect", new_callable=AsyncMock) as mock_sse_connect:
                with patch("app.mcp.client.MCPSTDIOClient.is_healthy", new_callable=AsyncMock) as mock_stdio_health:
                    with patch("app.mcp.client.MCPSSEClient.is_healthy", new_callable=AsyncMock) as mock_sse_health:
                        mock_stdio_connect.return_value = True
                        mock_sse_connect.return_value = True
                        mock_stdio_health.return_value = True
                        mock_sse_health.return_value = False  # API server unhealthy

                        await manager.connect_server("filesystem")
                        await manager.connect_server("api")

                        health_status = await manager.health_check_all()

                        assert health_status["filesystem"] is True
                        assert health_status["api"] is False

    @pytest.mark.asyncio
    async def test_manager_graceful_shutdown(self):
        """Test manager gracefully shuts down all connections."""
        config = MCPServersConfig(
            mcpServers={
                "filesystem": MCPServerConfig(
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                    transport=TransportType.STDIO,
                    enabled=True,
                ),
                "api": MCPServerConfig(
                    command="http://localhost:8080/sse",
                    transport=TransportType.SSE,
                    enabled=True,
                ),
            }
        )

        manager = MCPConnectionManager()
        await manager.initialize(config)

        with patch("app.mcp.client.MCPSTDIOClient.connect", new_callable=AsyncMock) as mock_stdio_connect:
            with patch("app.mcp.client.MCPSSEClient.connect", new_callable=AsyncMock) as mock_sse_connect:
                with patch("app.mcp.client.MCPSTDIOClient.disconnect", new_callable=AsyncMock) as mock_stdio_disconnect:
                    with patch("app.mcp.client.MCPSSEClient.disconnect", new_callable=AsyncMock) as mock_sse_disconnect:
                        mock_stdio_connect.return_value = True
                        mock_sse_connect.return_value = True

                        await manager.connect_server("filesystem")
                        await manager.connect_server("api")

                        await manager.shutdown()

                        # Verify both clients were disconnected
                        mock_stdio_disconnect.assert_called_once()
                        mock_sse_disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_manager_skips_disabled_servers(self):
        """Test manager doesn't connect to disabled servers."""
        config = MCPServersConfig(
            mcpServers={
                "filesystem": MCPServerConfig(
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                    transport=TransportType.STDIO,
                    enabled=False,  # Disabled
                ),
                "api": MCPServerConfig(
                    command="http://localhost:8080/sse",
                    transport=TransportType.SSE,
                    enabled=True,
                ),
            }
        )

        manager = MCPConnectionManager()
        await manager.initialize(config)

        # Attempting to connect to disabled server should raise error
        with pytest.raises(MCPConnectionError, match="disabled"):
            await manager.connect_server("filesystem")

    @pytest.mark.asyncio
    async def test_manager_connect_all_enabled(self):
        """Test manager can connect to all enabled servers at once."""
        config = MCPServersConfig(
            mcpServers={
                "filesystem": MCPServerConfig(
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                    transport=TransportType.STDIO,
                    enabled=True,
                ),
                "api": MCPServerConfig(
                    command="http://localhost:8080/sse",
                    transport=TransportType.SSE,
                    enabled=True,
                ),
                "disabled": MCPServerConfig(
                    command="test",
                    transport=TransportType.STDIO,
                    enabled=False,
                ),
            }
        )

        manager = MCPConnectionManager()
        await manager.initialize(config)

        with patch("app.mcp.client.MCPSTDIOClient.connect", new_callable=AsyncMock) as mock_stdio:
            with patch("app.mcp.client.MCPSSEClient.connect", new_callable=AsyncMock) as mock_sse:
                mock_stdio.return_value = True
                mock_sse.return_value = True

                results = await manager.connect_all_enabled()

                # Should only connect to enabled servers
                assert "filesystem" in results
                assert "api" in results
                assert "disabled" not in results
                assert results["filesystem"] is True
                assert results["api"] is True

    @pytest.mark.asyncio
    async def test_manager_exponential_backoff_caps_at_max(self):
        """Test exponential backoff caps at maximum delay."""
        config = MCPServersConfig(
            mcpServers={
                "filesystem": MCPServerConfig(
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                    transport=TransportType.STDIO,
                    enabled=True,
                )
            }
        )

        manager = MCPConnectionManager()
        await manager.initialize(config)

        # Test backoff calculation directly (without jitter for deterministic tests)
        delays = []
        for attempt in range(10):
            delay = manager._calculate_backoff(attempt, max_delay=5.0, jitter=False)
            delays.append(delay)

        # First few delays should grow exponentially
        assert delays[0] < delays[1]
        assert delays[1] < delays[2]

        # Later delays should cap at max_delay
        assert all(d <= 5.0 for d in delays)
        # Eventually should reach the cap
        assert delays[-1] == 5.0

        # Test that jitter adds randomness
        jittered_delays = [manager._calculate_backoff(0, jitter=True) for _ in range(10)]
        # With jitter, delays should vary
        assert len(set(jittered_delays)) > 1

    @pytest.mark.asyncio
    async def test_manager_get_server_status(self):
        """Test manager can report status of all servers."""
        config = MCPServersConfig(
            mcpServers={
                "filesystem": MCPServerConfig(
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                    transport=TransportType.STDIO,
                    enabled=True,
                ),
                "api": MCPServerConfig(
                    command="http://localhost:8080/sse",
                    transport=TransportType.SSE,
                    enabled=True,
                ),
                "disabled": MCPServerConfig(
                    command="test",
                    transport=TransportType.STDIO,
                    enabled=False,
                ),
            }
        )

        manager = MCPConnectionManager()
        await manager.initialize(config)

        with patch("app.mcp.client.MCPSTDIOClient.connect", new_callable=AsyncMock) as mock_stdio:
            with patch("app.mcp.client.MCPSSEClient.connect", new_callable=AsyncMock) as mock_sse:
                mock_stdio.return_value = True
                mock_sse.return_value = True

                await manager.connect_server("filesystem")

                status = await manager.get_server_status()

                # filesystem: connected
                # api: not connected
                # disabled: disabled
                assert status["filesystem"]["connected"] is True
                assert status["filesystem"]["enabled"] is True
                assert status["api"]["connected"] is False
                assert status["api"]["enabled"] is True
                assert status["disabled"]["connected"] is False
                assert status["disabled"]["enabled"] is False
