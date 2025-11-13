"""MCP tool schema conversion utilities.

This module provides utilities for converting MCP tool schemas to Agent Framework format.
"""
from dataclasses import dataclass
from typing import Any


@dataclass
class MCPToolSchema:
    """MCP tool schema representation.

    Attributes:
        name: Tool name
        description: Tool description
        input_schema: JSON Schema for tool input parameters
        server_name: Name of the MCP server providing this tool
        full_name: Fully qualified tool name (server_name.tool_name)
    """

    name: str
    description: str
    input_schema: dict[str, Any]
    server_name: str = ""
    full_name: str = ""


def mcp_to_agent_framework(tool: MCPToolSchema) -> dict[str, Any]:
    """Convert MCP tool schema to Agent Framework format.

    Transforms MCP JSON Schema format to Microsoft Agent Framework tool format.
    Maps JSON Schema types to Python types and preserves parameter metadata.

    Args:
        tool: MCP tool schema to convert

    Returns:
        Dictionary in Agent Framework tool format with:
        - name: Tool name (uses full_name if available)
        - description: Tool description
        - parameters: JSON Schema for parameters
    """
    # Use full_name if available, otherwise use name
    tool_name = tool.full_name if tool.full_name else tool.name

    # Convert input schema to Agent Framework format
    # MCP uses 'inputSchema', Agent Framework uses 'parameters'
    parameters = {
        "type": tool.input_schema.get("type", "object"),
        "properties": tool.input_schema.get("properties", {}),
    }

    # Include required fields if present
    if "required" in tool.input_schema:
        parameters["required"] = tool.input_schema["required"]

    # Preserve nested schema features like enum, default, items (for arrays), etc.
    # These are already in the correct format in the input_schema

    return {
        "name": tool_name,
        "description": tool.description,
        "parameters": parameters,
    }
