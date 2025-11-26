"""Tests for MCP to Agent Framework bridge.

Test basic tool execution and Agent Framework integration:
- Tool execution via JSON-RPC
- Parameter passing
- Result parsing
- Error handling
- Tool listing
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.mcp.bridge import MCPToolBridge
from app.mcp.exceptions import MCPConnectionError, MCPTimeoutError, MCPTransportError
from app.mcp.tool_schema import MCPToolSchema


class TestMCPToolBridge:
    """Tests for MCPToolBridge."""

    @pytest.fixture
    def mock_registry(self):
        """Create a mock tool registry."""
        registry = MagicMock()
        return registry

    @pytest.fixture
    def mock_manager(self):
        """Create a mock connection manager."""
        manager = MagicMock()
        return manager

    @pytest.fixture
    def bridge(self, mock_registry, mock_manager):
        """Create a bridge instance."""
        return MCPToolBridge(mock_registry, mock_manager)

    @pytest.fixture
    def sample_tool(self):
        """Create a sample tool schema."""
        return MCPToolSchema(
            name="read_file",
            description="Read a file",
            input_schema={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
            server_name="filesystem",
            full_name="filesystem.read_file",
        )

    @pytest.mark.asyncio
    async def test_execute_tool_success(self, bridge, mock_registry, mock_manager, sample_tool):
        """Test successful tool execution."""
        # Setup mocks
        mock_registry.get_tool.return_value = sample_tool

        mock_client = AsyncMock()
        mock_client.send_request.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"content": "file contents here"},
        }
        mock_manager.get_client = AsyncMock(return_value=mock_client)

        # Execute tool
        result = await bridge.execute_tool(
            "filesystem.read_file", {"path": "/workspace/file.txt"}
        )

        assert result == {"content": "file contents here"}

    @pytest.mark.asyncio
    async def test_execute_tool_sends_correct_request(
        self, bridge, mock_registry, mock_manager, sample_tool
    ):
        """Test that correct JSON-RPC tools/call request is sent."""
        mock_registry.get_tool.return_value = sample_tool

        mock_client = AsyncMock()
        mock_client.send_request.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {},
        }
        mock_manager.get_client = AsyncMock(return_value=mock_client)

        await bridge.execute_tool("filesystem.read_file", {"path": "/test.txt"})

        # Verify the request format
        call_args = mock_client.send_request.call_args
        request = call_args[0][0]

        assert request["jsonrpc"] == "2.0"
        assert request["method"] == "tools/call"
        assert "id" in request
        assert request["params"]["name"] == "read_file"
        assert request["params"]["arguments"] == {"path": "/test.txt"}

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, bridge, mock_registry):
        """Test executing a tool that doesn't exist."""
        mock_registry.get_tool.return_value = None

        with pytest.raises(ValueError, match="Tool not found"):
            await bridge.execute_tool("nonexistent.tool", {})

    @pytest.mark.asyncio
    async def test_execute_tool_no_client(self, bridge, mock_registry, mock_manager, sample_tool):
        """Test executing when client is unavailable."""
        mock_registry.get_tool.return_value = sample_tool
        mock_manager.get_client = AsyncMock(return_value=None)

        with pytest.raises(MCPConnectionError, match="No client available"):
            await bridge.execute_tool("filesystem.read_file", {"path": "/test.txt"})

    @pytest.mark.asyncio
    async def test_execute_tool_connection_error(
        self, bridge, mock_registry, mock_manager, sample_tool
    ):
        """Test handling connection errors during execution."""
        mock_registry.get_tool.return_value = sample_tool

        mock_client = AsyncMock()
        mock_client.send_request.side_effect = MCPConnectionError("Connection lost")
        mock_manager.get_client = AsyncMock(return_value=mock_client)

        with pytest.raises(MCPConnectionError, match="Connection lost"):
            await bridge.execute_tool("filesystem.read_file", {"path": "/test.txt"})

    @pytest.mark.asyncio
    async def test_execute_tool_timeout_error(
        self, bridge, mock_registry, mock_manager, sample_tool
    ):
        """Test handling timeout errors during execution."""
        mock_registry.get_tool.return_value = sample_tool

        mock_client = AsyncMock()
        mock_client.send_request.side_effect = MCPTimeoutError("Request timed out")
        mock_manager.get_client = AsyncMock(return_value=mock_client)

        with pytest.raises(MCPTimeoutError, match="Request timed out"):
            await bridge.execute_tool("filesystem.read_file", {"path": "/test.txt"})

    @pytest.mark.asyncio
    async def test_execute_tool_transport_error(
        self, bridge, mock_registry, mock_manager, sample_tool
    ):
        """Test handling transport errors during execution."""
        mock_registry.get_tool.return_value = sample_tool

        mock_client = AsyncMock()
        mock_client.send_request.side_effect = MCPTransportError("Transport failed")
        mock_manager.get_client = AsyncMock(return_value=mock_client)

        with pytest.raises(MCPTransportError, match="Transport failed"):
            await bridge.execute_tool("filesystem.read_file", {"path": "/test.txt"})

    @pytest.mark.asyncio
    async def test_execute_tool_with_complex_parameters(
        self, bridge, mock_registry, mock_manager
    ):
        """Test executing tool with complex parameter structures."""
        tool = MCPToolSchema(
            name="create_user",
            description="Create user",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "address": {"type": "object"},
                    "tags": {"type": "array"},
                },
            },
            server_name="api",
            full_name="api.create_user",
        )

        mock_registry.get_tool.return_value = tool

        mock_client = AsyncMock()
        mock_client.send_request.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"user_id": "12345"},
        }
        mock_manager.get_client = AsyncMock(return_value=mock_client)

        params = {
            "name": "John Doe",
            "address": {"city": "New York", "zip": "10001"},
            "tags": ["admin", "developer"],
        }

        result = await bridge.execute_tool("api.create_user", params)

        assert result == {"user_id": "12345"}

        # Verify parameters were passed correctly
        call_args = mock_client.send_request.call_args
        request = call_args[0][0]
        assert request["params"]["arguments"] == params

    @pytest.mark.asyncio
    async def test_execute_tool_server_error_response(
        self, bridge, mock_registry, mock_manager, sample_tool
    ):
        """Test handling server error in JSON-RPC response."""
        mock_registry.get_tool.return_value = sample_tool

        mock_client = AsyncMock()
        mock_client.send_request.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32601, "message": "Method not found"},
        }
        mock_manager.get_client = AsyncMock(return_value=mock_client)

        with pytest.raises(Exception, match="Method not found"):
            await bridge.execute_tool("filesystem.read_file", {"path": "/test.txt"})

    def test_get_available_tools_empty(self, bridge, mock_registry):
        """Test getting available tools when registry is empty."""
        mock_registry.list_tools.return_value = []

        tools = bridge.get_available_tools()

        assert tools == []

    def test_get_available_tools_single(self, bridge, mock_registry, sample_tool):
        """Test getting available tools with single tool."""
        mock_registry.list_tools.return_value = [sample_tool]

        tools = bridge.get_available_tools()

        assert len(tools) == 1
        assert tools[0]["name"] in ["filesystem.read_file", "read_file"]
        assert tools[0]["description"] == "Read a file"

    def test_get_available_tools_multiple(self, bridge, mock_registry):
        """Test getting available tools with multiple tools."""
        tool1 = MCPToolSchema(
            name="read_file",
            description="Read",
            input_schema={},
            server_name="filesystem",
            full_name="filesystem.read_file",
        )
        tool2 = MCPToolSchema(
            name="write_file",
            description="Write",
            input_schema={},
            server_name="filesystem",
            full_name="filesystem.write_file",
        )
        tool3 = MCPToolSchema(
            name="search",
            description="Search",
            input_schema={},
            server_name="web",
            full_name="web.search",
        )

        mock_registry.list_tools.return_value = [tool1, tool2, tool3]

        tools = bridge.get_available_tools()

        assert len(tools) == 3
        names = [t["name"] for t in tools]
        assert any("read_file" in name for name in names)
        assert any("write_file" in name for name in names)
        assert any("search" in name for name in names)

    def test_get_available_tools_includes_schema(self, bridge, mock_registry, sample_tool):
        """Test that available tools include parameter schema."""
        mock_registry.list_tools.return_value = [sample_tool]

        tools = bridge.get_available_tools()

        assert len(tools) == 1
        # Should include parameter information
        assert "parameters" in tools[0] or "inputSchema" in tools[0]

    def test_get_available_tools_agent_framework_format(self, bridge, mock_registry, sample_tool):
        """Test that tools are returned in Agent Framework format."""
        mock_registry.list_tools.return_value = [sample_tool]

        tools = bridge.get_available_tools()

        # Should be converted to Agent Framework format
        assert len(tools) == 1
        tool = tools[0]
        assert "name" in tool
        assert "description" in tool
        # Should have converted schema
        assert "parameters" in tool or "inputSchema" in tool

    @pytest.mark.asyncio
    async def test_execute_tool_empty_params(self, bridge, mock_registry, mock_manager):
        """Test executing tool with no parameters."""
        tool = MCPToolSchema(
            name="get_status",
            description="Get status",
            input_schema={"type": "object", "properties": {}},
            server_name="system",
            full_name="system.get_status",
        )

        mock_registry.get_tool.return_value = tool

        mock_client = AsyncMock()
        mock_client.send_request.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"status": "ok"},
        }
        mock_manager.get_client = AsyncMock(return_value=mock_client)

        result = await bridge.execute_tool("system.get_status", {})

        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_execute_tool_result_null(self, bridge, mock_registry, mock_manager, sample_tool):
        """Test executing tool that returns null/None result."""
        mock_registry.get_tool.return_value = sample_tool

        mock_client = AsyncMock()
        mock_client.send_request.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": None,
        }
        mock_manager.get_client = AsyncMock(return_value=mock_client)

        result = await bridge.execute_tool("filesystem.read_file", {"path": "/test.txt"})

        assert result is None

    @pytest.mark.asyncio
    async def test_execute_tool_uses_correct_server(
        self, bridge, mock_registry, mock_manager, sample_tool
    ):
        """Test that tool execution routes to correct server."""
        mock_registry.get_tool.return_value = sample_tool

        mock_client = AsyncMock()
        mock_client.send_request.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {},
        }
        mock_manager.get_client = AsyncMock(return_value=mock_client)

        await bridge.execute_tool("filesystem.read_file", {"path": "/test.txt"})

        # Verify get_client was called with correct server name
        mock_manager.get_client.assert_called_once_with("filesystem")

    def test_get_available_tools_filters_by_server(self, bridge, mock_registry):
        """Test getting tools filtered by server name (if supported)."""
        tool1 = MCPToolSchema(
            name="read",
            description="Read",
            input_schema={},
            server_name="filesystem",
            full_name="filesystem.read",
        )
        tool2 = MCPToolSchema(
            name="search",
            description="Search",
            input_schema={},
            server_name="web",
            full_name="web.search",
        )

        mock_registry.list_tools.return_value = [tool1, tool2]

        tools = bridge.get_available_tools()

        # All tools should be returned
        assert len(tools) == 2
