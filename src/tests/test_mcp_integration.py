"""Integration tests for MCP configuration, client factory, and connection manager."""
import pytest
from unittest.mock import AsyncMock, patch

from app.mcp import (
    MCPConnectionManager,
    MCPClientFactory,
    MCPServerConfig,
    MCPServersConfig,
    TransportType,
    load_mcp_config,
)


class TestMCPIntegration:
    """Integration tests combining config, factory, and manager."""

    @pytest.mark.asyncio
    async def test_end_to_end_stdio_workflow(self):
        """Test complete workflow: config -> factory -> manager -> client."""
        # 1. Create configuration
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

        # 2. Initialize manager
        manager = MCPConnectionManager()
        await manager.initialize(config)

        # 3. Connect using factory internally
        with patch("app.mcp.client.MCPSTDIOClient.connect", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = True

            await manager.connect_server("filesystem")

            # 4. Get client and verify it's the right type
            client = await manager.get_client("filesystem")
            assert client is not None

            # 5. Health check
            with patch("app.mcp.client.MCPSTDIOClient.is_healthy", new_callable=AsyncMock) as mock_health:
                mock_health.return_value = True
                health = await manager.health_check_all()
                assert health["filesystem"] is True

            # 6. Cleanup
            with patch("app.mcp.client.MCPSTDIOClient.disconnect", new_callable=AsyncMock):
                await manager.shutdown()

    @pytest.mark.asyncio
    async def test_end_to_end_sse_workflow(self):
        """Test complete workflow with SSE transport."""
        config = MCPServersConfig(
            mcpServers={
                "api": MCPServerConfig(
                    command="http://localhost:8080/sse",
                    transport=TransportType.SSE,
                    enabled=True,
                )
            }
        )

        manager = MCPConnectionManager()
        await manager.initialize(config)

        with patch("app.mcp.client.httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.is_success = True
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_httpx.return_value = mock_client

            await manager.connect_server("api")

            client = await manager.get_client("api")
            assert client is not None

            health = await manager.health_check_all()
            assert health["api"] is True

            await manager.shutdown()

    @pytest.mark.asyncio
    async def test_mixed_transport_types(self):
        """Test manager handling both STDIO and SSE transports simultaneously."""
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
            with patch("app.mcp.client.httpx.AsyncClient") as mock_httpx:
                mock_stdio.return_value = True

                mock_http_client = AsyncMock()
                mock_response = AsyncMock()
                mock_response.status_code = 200
                mock_response.is_success = True
                mock_http_client.get = AsyncMock(return_value=mock_response)
                mock_httpx.return_value = mock_http_client

                # Connect both servers
                results = await manager.connect_all_enabled()

                assert results["filesystem"] is True
                assert results["api"] is True

                # Get both clients
                fs_client = await manager.get_client("filesystem")
                api_client = await manager.get_client("api")

                assert fs_client is not None
                assert api_client is not None
                assert fs_client != api_client

                # Cleanup
                with patch("app.mcp.client.MCPSTDIOClient.disconnect", new_callable=AsyncMock):
                    await manager.shutdown()

    @pytest.mark.asyncio
    async def test_factory_creates_correct_client_types(self):
        """Test factory creates appropriate client for each transport type."""
        from app.mcp.client import MCPSTDIOClient, MCPSSEClient

        stdio_config = MCPServerConfig(
            command="npx",
            args=["-y", "test"],
            transport=TransportType.STDIO,
        )

        sse_config = MCPServerConfig(
            command="http://localhost:8080/sse",
            transport=TransportType.SSE,
        )

        stdio_client = MCPClientFactory.create_client(stdio_config)
        sse_client = MCPClientFactory.create_client(sse_config)

        assert isinstance(stdio_client, MCPSTDIOClient)
        assert isinstance(sse_client, MCPSSEClient)

    @pytest.mark.asyncio
    async def test_configuration_to_manager_integration(self, tmp_path):
        """Test loading config from file and using with manager."""
        # Create temporary config file
        config_file = tmp_path / "test_mcp_servers.json"
        config_file.write_text(
            """
            {
                "mcpServers": {
                    "test-server": {
                        "command": "npx",
                        "args": ["-y", "test"],
                        "enabled": true,
                        "transport": "stdio"
                    }
                }
            }
            """
        )

        # Load config
        config = load_mcp_config(str(config_file))

        # Use with manager
        manager = MCPConnectionManager()
        await manager.initialize(config)

        with patch("app.mcp.client.MCPSTDIOClient.connect", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = True

            await manager.connect_server("test-server")

            client = await manager.get_client("test-server")
            assert client is not None

            with patch("app.mcp.client.MCPSTDIOClient.disconnect", new_callable=AsyncMock):
                await manager.shutdown()
