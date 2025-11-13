"""MCP server integration examples.

This module provides example integrations for common MCP servers:
- Filesystem server for file operations
- Web search server for internet search capabilities
"""
from app.mcp.servers.filesystem import FilesystemServerHelper
from app.mcp.servers.web_search import WebSearchServerHelper

__all__ = [
    "FilesystemServerHelper",
    "WebSearchServerHelper",
]
