"""Tests for MCP tool discovery.

Test tool discovery from MCP servers including:
- JSON-RPC tools/list request/response
- Tool schema parsing
- Multiple server discovery
- Error handling
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.mcp.client import MCPClient
from app.mcp.discovery import discover_tools, discover_tools_from_manager
from app.mcp.exceptions import MCPConnectionError, MCPTimeoutError, MCPTransportError
from app.mcp.tool_schema import MCPToolSchema


class TestDiscoverTools:
    """Tests for discover_tools function."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock MCP client."""
        client = AsyncMock(spec=MCPClient)
        client._connected = True
        return client

    @pytest.mark.asyncio
    async def test_discover_tools_success(self, mock_client):
        """Test successful tool discovery."""
        # Mock response with tools
        mock_client.send_request.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [
                    {
                        "name": "read_file",
                        "description": "Read contents of a file",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string", "description": "File path"}
                            },
                            "required": ["path"],
                        },
                    }
                ]
            },
        }

        tools = await discover_tools(mock_client)

        assert len(tools) == 1
        assert isinstance(tools[0], MCPToolSchema)
        assert tools[0].name == "read_file"
        assert tools[0].description == "Read contents of a file"
        assert "path" in tools[0].input_schema["properties"]

    @pytest.mark.asyncio
    async def test_discover_tools_sends_correct_request(self, mock_client):
        """Test that correct JSON-RPC request is sent."""
        mock_client.send_request.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"tools": []},
        }

        await discover_tools(mock_client)

        # Verify the request format
        call_args = mock_client.send_request.call_args
        request = call_args[0][0]

        assert request["jsonrpc"] == "2.0"
        assert request["method"] == "tools/list"
        assert "id" in request

    @pytest.mark.asyncio
    async def test_discover_multiple_tools(self, mock_client):
        """Test discovering multiple tools."""
        mock_client.send_request.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [
                    {
                        "name": "read_file",
                        "description": "Read a file",
                        "inputSchema": {"type": "object", "properties": {}},
                    },
                    {
                        "name": "write_file",
                        "description": "Write a file",
                        "inputSchema": {"type": "object", "properties": {}},
                    },
                    {
                        "name": "delete_file",
                        "description": "Delete a file",
                        "inputSchema": {"type": "object", "properties": {}},
                    },
                ]
            },
        }

        tools = await discover_tools(mock_client)

        assert len(tools) == 3
        names = [t.name for t in tools]
        assert "read_file" in names
        assert "write_file" in names
        assert "delete_file" in names

    @pytest.mark.asyncio
    async def test_discover_tools_empty_result(self, mock_client):
        """Test discovering when server returns no tools."""
        mock_client.send_request.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"tools": []},
        }

        tools = await discover_tools(mock_client)

        assert tools == []

    @pytest.mark.asyncio
    async def test_discover_tools_connection_error(self, mock_client):
        """Test handling connection errors during discovery."""
        mock_client.send_request.side_effect = MCPConnectionError("Not connected")

        with pytest.raises(MCPConnectionError, match="Not connected"):
            await discover_tools(mock_client)

    @pytest.mark.asyncio
    async def test_discover_tools_timeout_error(self, mock_client):
        """Test handling timeout errors during discovery."""
        mock_client.send_request.side_effect = MCPTimeoutError("Request timed out")

        with pytest.raises(MCPTimeoutError, match="Request timed out"):
            await discover_tools(mock_client)

    @pytest.mark.asyncio
    async def test_discover_tools_transport_error(self, mock_client):
        """Test handling transport errors during discovery."""
        mock_client.send_request.side_effect = MCPTransportError("Transport error")

        with pytest.raises(MCPTransportError, match="Transport error"):
            await discover_tools(mock_client)

    @pytest.mark.asyncio
    async def test_discover_tools_malformed_response_no_result(self, mock_client):
        """Test handling malformed response missing 'result' field."""
        mock_client.send_request.return_value = {"jsonrpc": "2.0", "id": 1}

        # Should handle gracefully and return empty list or raise appropriate error
        tools = await discover_tools(mock_client)
        assert tools == []

    @pytest.mark.asyncio
    async def test_discover_tools_malformed_response_no_tools(self, mock_client):
        """Test handling malformed response missing 'tools' field."""
        mock_client.send_request.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {},
        }

        tools = await discover_tools(mock_client)
        assert tools == []

    @pytest.mark.asyncio
    async def test_discover_tools_invalid_tool_schema(self, mock_client):
        """Test handling invalid tool schema in response."""
        mock_client.send_request.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [
                    # Missing required 'name' field
                    {
                        "description": "Invalid tool",
                        "inputSchema": {"type": "object"},
                    }
                ]
            },
        }

        # Should skip invalid tools or raise validation error
        with pytest.raises((ValueError, KeyError)):
            await discover_tools(mock_client)

    @pytest.mark.asyncio
    async def test_discover_tools_partial_invalid_schemas(self, mock_client):
        """Test discovering tools when some schemas are invalid."""
        mock_client.send_request.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [
                    {
                        "name": "valid_tool",
                        "description": "Valid",
                        "inputSchema": {"type": "object", "properties": {}},
                    },
                    {
                        # Missing 'name'
                        "description": "Invalid",
                        "inputSchema": {"type": "object"},
                    },
                ]
            },
        }

        # Should either skip invalid or fail appropriately
        with pytest.raises((ValueError, KeyError)):
            await discover_tools(mock_client)

    @pytest.mark.asyncio
    async def test_discover_tools_complex_schema(self, mock_client):
        """Test discovering tool with complex input schema."""
        mock_client.send_request.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [
                    {
                        "name": "create_user",
                        "description": "Create a new user",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "email": {"type": "string"},
                                "age": {"type": "integer"},
                                "address": {
                                    "type": "object",
                                    "properties": {
                                        "street": {"type": "string"},
                                        "city": {"type": "string"},
                                    },
                                },
                                "tags": {"type": "array", "items": {"type": "string"}},
                            },
                            "required": ["name", "email"],
                        },
                    }
                ]
            },
        }

        tools = await discover_tools(mock_client)

        assert len(tools) == 1
        tool = tools[0]
        assert tool.name == "create_user"
        assert "address" in tool.input_schema["properties"]
        assert "tags" in tool.input_schema["properties"]
        assert tool.input_schema["required"] == ["name", "email"]


class TestDiscoverToolsFromManager:
    """Tests for discover_tools_from_manager function."""

    @pytest.mark.asyncio
    async def test_discover_from_single_server(self):
        """Test discovering tools from single server via manager."""
        # Mock manager with one server
        mock_manager = MagicMock()
        mock_client = AsyncMock(spec=MCPClient)
        mock_client._connected = True
        mock_client.send_request.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [
                    {
                        "name": "read_file",
                        "description": "Read file",
                        "inputSchema": {"type": "object", "properties": {}},
                    }
                ]
            },
        }

        mock_manager.get_client.return_value = mock_client
        mock_manager.list_servers.return_value = ["filesystem"]

        result = await discover_tools_from_manager(mock_manager)

        assert "filesystem" in result
        assert len(result["filesystem"]) == 1
        assert result["filesystem"][0].name == "read_file"

    @pytest.mark.asyncio
    async def test_discover_from_multiple_servers(self):
        """Test discovering tools from multiple servers."""
        mock_manager = MagicMock()

        # Create different responses for different servers
        def get_client_side_effect(server_name):
            client = AsyncMock(spec=MCPClient)
            client._connected = True

            if server_name == "filesystem":
                client.send_request.return_value = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": {
                        "tools": [
                            {
                                "name": "read_file",
                                "description": "Read",
                                "inputSchema": {"type": "object", "properties": {}},
                            }
                        ]
                    },
                }
            elif server_name == "web":
                client.send_request.return_value = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": {
                        "tools": [
                            {
                                "name": "search",
                                "description": "Search web",
                                "inputSchema": {"type": "object", "properties": {}},
                            }
                        ]
                    },
                }

            return client

        mock_manager.get_client.side_effect = get_client_side_effect
        mock_manager.list_servers.return_value = ["filesystem", "web"]

        result = await discover_tools_from_manager(mock_manager)

        assert "filesystem" in result
        assert "web" in result
        assert len(result["filesystem"]) == 1
        assert len(result["web"]) == 1
        assert result["filesystem"][0].name == "read_file"
        assert result["web"][0].name == "search"

    @pytest.mark.asyncio
    async def test_discover_from_manager_no_servers(self):
        """Test discovering when manager has no servers."""
        mock_manager = MagicMock()
        mock_manager.list_servers.return_value = []

        result = await discover_tools_from_manager(mock_manager)

        assert result == {}

    @pytest.mark.asyncio
    async def test_discover_from_manager_server_error(self):
        """Test handling errors from one server while others succeed."""
        mock_manager = MagicMock()

        def get_client_side_effect(server_name):
            client = AsyncMock(spec=MCPClient)
            client._connected = True

            if server_name == "filesystem":
                client.send_request.return_value = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": {
                        "tools": [
                            {
                                "name": "read_file",
                                "description": "Read",
                                "inputSchema": {"type": "object", "properties": {}},
                            }
                        ]
                    },
                }
            elif server_name == "web":
                client.send_request.side_effect = MCPConnectionError("Server down")

            return client

        mock_manager.get_client.side_effect = get_client_side_effect
        mock_manager.list_servers.return_value = ["filesystem", "web"]

        result = await discover_tools_from_manager(mock_manager)

        # Should have filesystem tools, web should be empty or missing
        assert "filesystem" in result
        assert len(result["filesystem"]) == 1
        # web might be missing or have empty list depending on implementation
        assert "web" not in result or result["web"] == []

    @pytest.mark.asyncio
    async def test_discover_from_manager_no_client(self):
        """Test handling when manager cannot provide client."""
        mock_manager = MagicMock()
        mock_manager.list_servers.return_value = ["filesystem"]
        mock_manager.get_client.return_value = None

        result = await discover_tools_from_manager(mock_manager)

        # Should handle gracefully
        assert "filesystem" not in result or result["filesystem"] == []
