"""Tests for MCP client implementations (STDIO and SSE transports)."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch
import pytest

from app.mcp.client import MCPClient, MCPSTDIOClient, MCPSSEClient
from app.mcp.config import MCPServerConfig, TransportType
from app.mcp.exceptions import MCPConnectionError, MCPTransportError, MCPTimeoutError


class TestMCPSTDIOClient:
    """Test suite for STDIO transport client."""

    def test_stdio_client_creation(self):
        """Test STDIO client can be created with valid configuration."""
        config = MCPServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            transport=TransportType.STDIO,
        )
        client = MCPSTDIOClient(config)
        assert client is not None
        assert isinstance(client, MCPClient)

    @pytest.mark.asyncio
    async def test_stdio_client_connect_success(self):
        """Test STDIO client successfully connects via subprocess."""
        config = MCPServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            transport=TransportType.STDIO,
        )
        client = MCPSTDIOClient(config)

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.stdout = AsyncMock()
            mock_process.stdin = AsyncMock()
            mock_process.returncode = None
            mock_subprocess.return_value = mock_process

            result = await client.connect()

            assert result is True
            mock_subprocess.assert_called_once()
            # Verify command and args were passed correctly
            call_args = mock_subprocess.call_args
            assert call_args[0][0] == "npx"
            assert "-y" in call_args[0]

    @pytest.mark.asyncio
    async def test_stdio_client_connect_failure(self):
        """Test STDIO client handles connection failure gracefully."""
        config = MCPServerConfig(
            command="nonexistent_command",
            transport=TransportType.STDIO,
        )
        client = MCPSTDIOClient(config)

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_subprocess.side_effect = FileNotFoundError("Command not found")

            with pytest.raises(MCPConnectionError):
                await client.connect()

    @pytest.mark.asyncio
    async def test_stdio_client_disconnect(self):
        """Test STDIO client properly terminates subprocess on disconnect."""
        config = MCPServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            transport=TransportType.STDIO,
        )
        client = MCPSTDIOClient(config)

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.stdout = AsyncMock()
            mock_process.stdin = AsyncMock()
            mock_process.returncode = None
            mock_process.wait = AsyncMock()
            mock_subprocess.return_value = mock_process

            await client.connect()
            await client.disconnect()

            mock_process.terminate.assert_called_once()
            mock_process.wait.assert_called_once()

    @pytest.mark.asyncio
    async def test_stdio_client_send_request(self):
        """Test STDIO client can send JSON-RPC requests."""
        config = MCPServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            transport=TransportType.STDIO,
        )
        client = MCPSTDIOClient(config)

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.stdout = AsyncMock()
            mock_process.stdout.readline = AsyncMock(
                return_value=b'{"jsonrpc": "2.0", "result": {"tools": []}, "id": 1}\n'
            )
            mock_process.stdin = AsyncMock()
            mock_process.returncode = None
            mock_subprocess.return_value = mock_process

            await client.connect()

            request = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}
            response = await client.send_request(request)

            assert response["jsonrpc"] == "2.0"
            assert "result" in response
            mock_process.stdin.write.assert_called_once()

    @pytest.mark.asyncio
    async def test_stdio_client_request_timeout(self):
        """Test STDIO client handles request timeout."""
        config = MCPServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            transport=TransportType.STDIO,
        )
        client = MCPSTDIOClient(config)

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.stdout = AsyncMock()
            # Simulate timeout by never returning
            mock_process.stdout.readline = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_process.stdin = AsyncMock()
            mock_process.returncode = None
            mock_subprocess.return_value = mock_process

            await client.connect()

            request = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}

            with pytest.raises(MCPTimeoutError):
                await client.send_request(request, timeout=0.1)

    @pytest.mark.asyncio
    async def test_stdio_client_health_check_healthy(self):
        """Test STDIO client health check returns True for healthy process."""
        config = MCPServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            transport=TransportType.STDIO,
        )
        client = MCPSTDIOClient(config)

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.stdout = AsyncMock()
            mock_process.stdin = AsyncMock()
            mock_process.returncode = None  # Process still running
            mock_subprocess.return_value = mock_process

            await client.connect()
            is_healthy = await client.is_healthy()

            assert is_healthy is True

    @pytest.mark.asyncio
    async def test_stdio_client_health_check_unhealthy(self):
        """Test STDIO client health check returns False for dead process."""
        config = MCPServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            transport=TransportType.STDIO,
        )
        client = MCPSTDIOClient(config)

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.stdout = AsyncMock()
            mock_process.stdin = AsyncMock()
            mock_process.returncode = None
            mock_subprocess.return_value = mock_process

            await client.connect()

            # Simulate process death
            mock_process.returncode = 1

            is_healthy = await client.is_healthy()

            assert is_healthy is False

    @pytest.mark.asyncio
    async def test_stdio_client_environment_variables(self):
        """Test STDIO client passes environment variables to subprocess."""
        config = MCPServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            env={"API_KEY": "test_key", "DEBUG": "true"},
            transport=TransportType.STDIO,
        )
        client = MCPSTDIOClient(config)

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.stdout = AsyncMock()
            mock_process.stdin = AsyncMock()
            mock_process.returncode = None
            mock_subprocess.return_value = mock_process

            await client.connect()

            # Verify environment variables were passed
            call_kwargs = mock_subprocess.call_args[1]
            assert "env" in call_kwargs
            env = call_kwargs["env"]
            assert env["API_KEY"] == "test_key"
            assert env["DEBUG"] == "true"


class TestMCPSSEClient:
    """Test suite for SSE transport client."""

    def test_sse_client_creation(self):
        """Test SSE client can be created with valid configuration."""
        config = MCPServerConfig(
            command="http://localhost:8080/sse",
            transport=TransportType.SSE,
        )
        client = MCPSSEClient(config)
        assert client is not None
        assert isinstance(client, MCPClient)

    @pytest.mark.asyncio
    async def test_sse_client_connect_success(self):
        """Test SSE client successfully connects to HTTP endpoint."""
        config = MCPServerConfig(
            command="http://localhost:8080/sse",
            transport=TransportType.SSE,
        )
        client = MCPSSEClient(config)

        with patch("app.mcp.client.httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.is_success = True
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_httpx.return_value = mock_client

            result = await client.connect()

            assert result is True

    @pytest.mark.asyncio
    async def test_sse_client_connect_failure(self):
        """Test SSE client handles connection failure."""
        config = MCPServerConfig(
            command="http://localhost:8080/sse",
            transport=TransportType.SSE,
        )
        client = MCPSSEClient(config)

        with patch("app.mcp.client.httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
            mock_httpx.return_value = mock_client

            with pytest.raises(MCPConnectionError):
                await client.connect()

    @pytest.mark.asyncio
    async def test_sse_client_disconnect(self):
        """Test SSE client properly closes HTTP connection."""
        config = MCPServerConfig(
            command="http://localhost:8080/sse",
            transport=TransportType.SSE,
        )
        client = MCPSSEClient(config)

        with patch("app.mcp.client.httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.is_success = True
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_httpx.return_value = mock_client

            await client.connect()
            await client.disconnect()

            # Verify client was properly closed
            mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_sse_client_send_request(self):
        """Test SSE client can send HTTP requests."""
        config = MCPServerConfig(
            command="http://localhost:8080/sse",
            transport=TransportType.SSE,
        )
        client = MCPSSEClient(config)

        with patch("app.mcp.client.httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_connect_response = AsyncMock()
            mock_connect_response.status_code = 200
            mock_connect_response.is_success = True

            mock_request_response = AsyncMock()
            mock_request_response.status_code = 200
            mock_request_response.is_success = True
            mock_request_response.json = Mock(
                return_value={"jsonrpc": "2.0", "result": {"tools": []}, "id": 1}
            )

            mock_client.get = AsyncMock(return_value=mock_connect_response)
            mock_client.post = AsyncMock(return_value=mock_request_response)
            mock_httpx.return_value = mock_client

            await client.connect()

            request = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}
            response = await client.send_request(request)

            assert response["jsonrpc"] == "2.0"
            assert "result" in response
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_sse_client_request_timeout(self):
        """Test SSE client handles request timeout."""
        config = MCPServerConfig(
            command="http://localhost:8080/sse",
            transport=TransportType.SSE,
        )
        client = MCPSSEClient(config)

        with patch("app.mcp.client.httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_connect_response = AsyncMock()
            mock_connect_response.status_code = 200
            mock_connect_response.is_success = True

            mock_client.get = AsyncMock(return_value=mock_connect_response)
            mock_client.post = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_httpx.return_value = mock_client

            await client.connect()

            request = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}

            with pytest.raises(MCPTimeoutError):
                await client.send_request(request, timeout=0.1)

    @pytest.mark.asyncio
    async def test_sse_client_health_check_healthy(self):
        """Test SSE client health check returns True for responsive server."""
        config = MCPServerConfig(
            command="http://localhost:8080/sse",
            transport=TransportType.SSE,
        )
        client = MCPSSEClient(config)

        with patch("app.mcp.client.httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.is_success = True
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_httpx.return_value = mock_client

            await client.connect()
            is_healthy = await client.is_healthy()

            assert is_healthy is True

    @pytest.mark.asyncio
    async def test_sse_client_health_check_unhealthy(self):
        """Test SSE client health check returns False for unresponsive server."""
        config = MCPServerConfig(
            command="http://localhost:8080/sse",
            transport=TransportType.SSE,
        )
        client = MCPSSEClient(config)

        with patch("app.mcp.client.httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_connect_response = AsyncMock()
            mock_connect_response.status_code = 200
            mock_connect_response.is_success = True

            mock_client.get = AsyncMock(return_value=mock_connect_response)
            mock_httpx.return_value = mock_client

            await client.connect()

            # Simulate server becoming unresponsive
            mock_client.get = AsyncMock(side_effect=Exception("Connection error"))

            is_healthy = await client.is_healthy()

            assert is_healthy is False

    @pytest.mark.asyncio
    async def test_sse_client_headers_from_env(self):
        """Test SSE client includes headers from environment variables."""
        config = MCPServerConfig(
            command="http://localhost:8080/sse",
            env={"AUTHORIZATION": "Bearer token123", "X-API-KEY": "key456"},
            transport=TransportType.SSE,
        )
        client = MCPSSEClient(config)

        with patch("app.mcp.client.httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.is_success = True
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_httpx.return_value = mock_client

            await client.connect()

            # Verify headers were included in connection
            call_kwargs = mock_client.get.call_args[1]
            assert "headers" in call_kwargs
            headers = call_kwargs["headers"]
            assert headers["AUTHORIZATION"] == "Bearer token123"
            assert headers["X-API-KEY"] == "key456"
