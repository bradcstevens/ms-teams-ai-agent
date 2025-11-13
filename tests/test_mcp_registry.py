"""Tests for MCP tool registry.

Test tool registration and management including:
- Tool registration
- Name conflict resolution (prefixing)
- Tool retrieval
- Tool listing
- Thread safety
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.mcp.registry import MCPToolRegistry
from app.mcp.tool_schema import MCPToolSchema


class TestMCPToolRegistry:
    """Tests for MCPToolRegistry."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry for each test."""
        return MCPToolRegistry()

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
        )

    def test_register_tool(self, registry, sample_tool):
        """Test registering a tool."""
        full_name = registry.register_tool("filesystem", sample_tool)

        assert full_name == "filesystem.read_file"
        assert registry.get_tool_count() == 1

    def test_register_tool_sets_metadata(self, registry, sample_tool):
        """Test that registration sets server_name and full_name."""
        full_name = registry.register_tool("filesystem", sample_tool)

        tool = registry.get_tool(full_name)
        assert tool is not None
        assert tool.server_name == "filesystem"
        assert tool.full_name == "filesystem.read_file"

    def test_get_tool(self, registry, sample_tool):
        """Test retrieving a registered tool."""
        full_name = registry.register_tool("filesystem", sample_tool)

        retrieved = registry.get_tool(full_name)

        assert retrieved is not None
        assert retrieved.name == "read_file"
        assert retrieved.description == "Read a file"

    def test_get_nonexistent_tool(self, registry):
        """Test retrieving a tool that doesn't exist."""
        result = registry.get_tool("nonexistent.tool")

        assert result is None

    def test_list_all_tools(self, registry, sample_tool):
        """Test listing all tools across all servers."""
        tool2 = MCPToolSchema(
            name="write_file",
            description="Write a file",
            input_schema={},
        )

        registry.register_tool("filesystem", sample_tool)
        registry.register_tool("filesystem", tool2)

        tools = registry.list_tools()

        assert len(tools) == 2
        assert any(t.name == "read_file" for t in tools)
        assert any(t.name == "write_file" for t in tools)

    def test_list_tools_by_server(self, registry, sample_tool):
        """Test listing tools filtered by server name."""
        tool2 = MCPToolSchema(
            name="search_web",
            description="Search the web",
            input_schema={},
        )

        registry.register_tool("filesystem", sample_tool)
        registry.register_tool("web", tool2)

        filesystem_tools = registry.list_tools(server_name="filesystem")
        web_tools = registry.list_tools(server_name="web")

        assert len(filesystem_tools) == 1
        assert len(web_tools) == 1
        assert filesystem_tools[0].name == "read_file"
        assert web_tools[0].name == "search_web"

    def test_list_tools_empty_server(self, registry):
        """Test listing tools for server with no tools."""
        tools = registry.list_tools(server_name="nonexistent")

        assert tools == []

    def test_name_conflict_resolution(self, registry):
        """Test that tools with same name from different servers are prefixed."""
        tool1 = MCPToolSchema(
            name="read_file",
            description="Read from filesystem",
            input_schema={},
        )
        tool2 = MCPToolSchema(
            name="read_file",
            description="Read from cloud",
            input_schema={},
        )

        full_name1 = registry.register_tool("filesystem", tool1)
        full_name2 = registry.register_tool("cloud", tool2)

        assert full_name1 == "filesystem.read_file"
        assert full_name2 == "cloud.read_file"
        assert registry.get_tool_count() == 2

    def test_remove_tool(self, registry, sample_tool):
        """Test removing a registered tool."""
        full_name = registry.register_tool("filesystem", sample_tool)

        removed = registry.remove_tool(full_name)

        assert removed is True
        assert registry.get_tool_count() == 0
        assert registry.get_tool(full_name) is None

    def test_remove_nonexistent_tool(self, registry):
        """Test removing a tool that doesn't exist."""
        removed = registry.remove_tool("nonexistent.tool")

        assert removed is False

    def test_clear_registry(self, registry, sample_tool):
        """Test clearing all tools from registry."""
        tool2 = MCPToolSchema(
            name="write_file",
            description="Write a file",
            input_schema={},
        )

        registry.register_tool("filesystem", sample_tool)
        registry.register_tool("filesystem", tool2)

        registry.clear()

        assert registry.get_tool_count() == 0
        assert registry.list_tools() == []

    def test_get_tool_count_empty(self, registry):
        """Test getting count of empty registry."""
        assert registry.get_tool_count() == 0

    def test_get_tool_count_multiple(self, registry, sample_tool):
        """Test getting count with multiple tools."""
        tool2 = MCPToolSchema(name="write_file", description="Write", input_schema={})
        tool3 = MCPToolSchema(name="delete_file", description="Delete", input_schema={})

        registry.register_tool("filesystem", sample_tool)
        registry.register_tool("filesystem", tool2)
        registry.register_tool("cloud", tool3)

        assert registry.get_tool_count() == 3

    def test_register_same_tool_twice_same_server(self, registry, sample_tool):
        """Test registering the same tool twice on same server (should update)."""
        full_name1 = registry.register_tool("filesystem", sample_tool)
        full_name2 = registry.register_tool("filesystem", sample_tool)

        assert full_name1 == full_name2
        # Should only have one instance
        assert registry.get_tool_count() == 1

    def test_thread_safety_concurrent_registration(self, registry):
        """Test concurrent tool registration is thread-safe."""

        def register_tools(server_name, count):
            for i in range(count):
                tool = MCPToolSchema(
                    name=f"tool_{i}",
                    description=f"Tool {i}",
                    input_schema={},
                )
                registry.register_tool(server_name, tool)

        with ThreadPoolExecutor(max_workers=5) as executor:
            # Register 20 tools concurrently from 5 threads
            futures = [executor.submit(register_tools, f"server_{i}", 4) for i in range(5)]
            for future in futures:
                future.result()

        # Should have 5 servers * 4 tools = 20 tools
        assert registry.get_tool_count() == 20

    def test_thread_safety_concurrent_reads(self, registry, sample_tool):
        """Test concurrent tool retrieval is thread-safe."""
        full_name = registry.register_tool("filesystem", sample_tool)

        def read_tool():
            tool = registry.get_tool(full_name)
            assert tool is not None
            assert tool.name == "read_file"

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(read_tool) for _ in range(100)]
            for future in futures:
                future.result()

    def test_thread_safety_mixed_operations(self, registry):
        """Test mixed concurrent operations are thread-safe."""

        def write_operations():
            for i in range(10):
                tool = MCPToolSchema(
                    name=f"tool_{i}",
                    description=f"Tool {i}",
                    input_schema={},
                )
                registry.register_tool("server1", tool)

        def read_operations():
            for _ in range(10):
                tools = registry.list_tools()
                count = registry.get_tool_count()

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            futures.append(executor.submit(write_operations))
            futures.append(executor.submit(write_operations))
            futures.append(executor.submit(read_operations))
            futures.append(executor.submit(read_operations))

            for future in futures:
                future.result()

        # Both write threads register the same 10 tools (tool_0 to tool_9)
        # so they overwrite each other, resulting in 10 unique tools
        assert registry.get_tool_count() == 10

    def test_list_tools_returns_copy(self, registry, sample_tool):
        """Test that list_tools returns independent copies."""
        registry.register_tool("filesystem", sample_tool)

        tools1 = registry.list_tools()
        tools2 = registry.list_tools()

        # Should be different list instances
        assert tools1 is not tools2
        # But same content
        assert len(tools1) == len(tools2)

    def test_register_multiple_servers(self, registry):
        """Test registering tools across multiple servers."""
        servers = ["filesystem", "web", "database", "api"]

        for server in servers:
            for i in range(3):
                tool = MCPToolSchema(
                    name=f"tool_{i}",
                    description=f"Tool {i} for {server}",
                    input_schema={},
                )
                registry.register_tool(server, tool)

        # 4 servers * 3 tools = 12 total
        assert registry.get_tool_count() == 12

        # Each server should have 3 tools
        for server in servers:
            assert len(registry.list_tools(server_name=server)) == 3
