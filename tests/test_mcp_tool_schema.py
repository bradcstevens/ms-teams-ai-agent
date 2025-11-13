"""Tests for MCP tool schema conversion utilities.

Test JSON Schema to Agent Framework conversion including:
- Parameter type mapping
- Required vs optional parameters
- Nested objects
- Array parameters
"""
import pytest

from app.mcp.tool_schema import MCPToolSchema, mcp_to_agent_framework


class TestMCPToolSchema:
    """Tests for MCPToolSchema dataclass."""

    def test_create_tool_schema(self):
        """Test creating a basic tool schema."""
        schema = MCPToolSchema(
            name="read_file",
            description="Read a file",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"}
                },
                "required": ["path"],
            },
        )

        assert schema.name == "read_file"
        assert schema.description == "Read a file"
        assert schema.server_name == ""
        assert schema.full_name == ""

    def test_tool_schema_with_server_name(self):
        """Test tool schema with server name set."""
        schema = MCPToolSchema(
            name="read_file",
            description="Read a file",
            input_schema={},
            server_name="filesystem",
        )

        assert schema.server_name == "filesystem"

    def test_tool_schema_with_full_name(self):
        """Test tool schema with full name set."""
        schema = MCPToolSchema(
            name="read_file",
            description="Read a file",
            input_schema={},
            full_name="filesystem.read_file",
        )

        assert schema.full_name == "filesystem.read_file"


class TestMCPToAgentFramework:
    """Tests for MCP to Agent Framework schema conversion."""

    def test_convert_simple_string_parameter(self):
        """Test converting a simple string parameter."""
        tool = MCPToolSchema(
            name="read_file",
            description="Read a file",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"}
                },
                "required": ["path"],
            },
        )

        result = mcp_to_agent_framework(tool)

        assert result["name"] == "read_file"
        assert result["description"] == "Read a file"
        assert "parameters" in result
        assert result["parameters"]["type"] == "object"
        assert "path" in result["parameters"]["properties"]
        assert result["parameters"]["properties"]["path"]["type"] == "string"
        assert result["parameters"]["required"] == ["path"]

    def test_convert_multiple_parameters(self):
        """Test converting multiple parameters of different types."""
        tool = MCPToolSchema(
            name="search",
            description="Search for items",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "number", "description": "Max results"},
                    "include_metadata": {
                        "type": "boolean",
                        "description": "Include metadata",
                    },
                },
                "required": ["query"],
            },
        )

        result = mcp_to_agent_framework(tool)

        props = result["parameters"]["properties"]
        assert "query" in props
        assert "limit" in props
        assert "include_metadata" in props
        assert props["query"]["type"] == "string"
        assert props["limit"]["type"] == "number"
        assert props["include_metadata"]["type"] == "boolean"
        assert result["parameters"]["required"] == ["query"]

    def test_convert_optional_parameters(self):
        """Test converting schema with optional parameters."""
        tool = MCPToolSchema(
            name="create_file",
            description="Create a file",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                    "overwrite": {"type": "boolean"},
                },
                "required": ["path"],
            },
        )

        result = mcp_to_agent_framework(tool)

        # Only 'path' should be required
        assert result["parameters"]["required"] == ["path"]
        # All properties should be present
        assert len(result["parameters"]["properties"]) == 3

    def test_convert_no_required_parameters(self):
        """Test converting schema with no required parameters."""
        tool = MCPToolSchema(
            name="list_files",
            description="List files",
            input_schema={
                "type": "object",
                "properties": {
                    "directory": {"type": "string"},
                    "pattern": {"type": "string"},
                },
            },
        )

        result = mcp_to_agent_framework(tool)

        # Should have empty required list or no required key
        assert result["parameters"].get("required", []) == []

    def test_convert_nested_object(self):
        """Test converting schema with nested object properties."""
        tool = MCPToolSchema(
            name="create_user",
            description="Create a user",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "address": {
                        "type": "object",
                        "properties": {
                            "street": {"type": "string"},
                            "city": {"type": "string"},
                            "zip": {"type": "string"},
                        },
                        "required": ["city"],
                    },
                },
                "required": ["name"],
            },
        )

        result = mcp_to_agent_framework(tool)

        assert "address" in result["parameters"]["properties"]
        address = result["parameters"]["properties"]["address"]
        assert address["type"] == "object"
        assert "properties" in address
        assert "street" in address["properties"]
        assert "city" in address["properties"]
        assert address["required"] == ["city"]

    def test_convert_array_parameter(self):
        """Test converting schema with array parameters."""
        tool = MCPToolSchema(
            name="bulk_delete",
            description="Delete multiple files",
            input_schema={
                "type": "object",
                "properties": {
                    "paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "File paths to delete",
                    }
                },
                "required": ["paths"],
            },
        )

        result = mcp_to_agent_framework(tool)

        assert "paths" in result["parameters"]["properties"]
        paths = result["parameters"]["properties"]["paths"]
        assert paths["type"] == "array"
        assert "items" in paths
        assert paths["items"]["type"] == "string"

    def test_convert_preserves_descriptions(self):
        """Test that parameter descriptions are preserved."""
        tool = MCPToolSchema(
            name="read_file",
            description="Read file contents",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the file",
                    },
                    "encoding": {
                        "type": "string",
                        "description": "File encoding (default: utf-8)",
                    },
                },
                "required": ["path"],
            },
        )

        result = mcp_to_agent_framework(tool)

        props = result["parameters"]["properties"]
        assert props["path"]["description"] == "Absolute path to the file"
        assert props["encoding"]["description"] == "File encoding (default: utf-8)"

    def test_convert_empty_schema(self):
        """Test converting tool with no parameters."""
        tool = MCPToolSchema(
            name="get_status",
            description="Get system status",
            input_schema={"type": "object", "properties": {}},
        )

        result = mcp_to_agent_framework(tool)

        assert result["name"] == "get_status"
        assert result["description"] == "Get system status"
        assert result["parameters"]["type"] == "object"
        assert result["parameters"]["properties"] == {}

    def test_convert_with_full_name(self):
        """Test that full_name is included in conversion if set."""
        tool = MCPToolSchema(
            name="read_file",
            description="Read a file",
            input_schema={"type": "object", "properties": {}},
            full_name="filesystem.read_file",
        )

        result = mcp_to_agent_framework(tool)

        # The converter should use full_name if available
        assert result.get("name") == "filesystem.read_file" or result.get(
            "full_name"
        ) == "filesystem.read_file"

    def test_convert_integer_type(self):
        """Test converting integer type parameters."""
        tool = MCPToolSchema(
            name="repeat",
            description="Repeat an action",
            input_schema={
                "type": "object",
                "properties": {
                    "count": {"type": "integer", "description": "Number of times"}
                },
                "required": ["count"],
            },
        )

        result = mcp_to_agent_framework(tool)

        assert result["parameters"]["properties"]["count"]["type"] == "integer"

    def test_convert_with_enum(self):
        """Test converting parameter with enum values."""
        tool = MCPToolSchema(
            name="set_mode",
            description="Set operation mode",
            input_schema={
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["read", "write", "execute"],
                        "description": "Operation mode",
                    }
                },
                "required": ["mode"],
            },
        )

        result = mcp_to_agent_framework(tool)

        mode = result["parameters"]["properties"]["mode"]
        assert mode["type"] == "string"
        assert mode["enum"] == ["read", "write", "execute"]

    def test_convert_with_default_value(self):
        """Test converting parameter with default value."""
        tool = MCPToolSchema(
            name="read_file",
            description="Read a file",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "encoding": {"type": "string", "default": "utf-8"},
                },
                "required": ["path"],
            },
        )

        result = mcp_to_agent_framework(tool)

        encoding = result["parameters"]["properties"]["encoding"]
        assert encoding["default"] == "utf-8"
