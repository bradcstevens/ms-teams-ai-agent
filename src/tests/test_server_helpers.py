"""Tests for MCP server helper utilities.

This test suite validates the filesystem and web search server configuration helpers.
"""
import pytest

from app.mcp.config import TransportType
from app.mcp.servers.filesystem import FilesystemServerHelper
from app.mcp.servers.web_search import WebSearchServerHelper


class TestFilesystemServerHelper:
    """Test cases for FilesystemServerHelper."""

    def test_create_filesystem_config(self):
        """Test creating filesystem server configuration."""
        config = FilesystemServerHelper.create_config("/home/user/documents")

        assert config.command == "npx"
        assert "-y" in config.args
        assert "@modelcontextprotocol/server-filesystem" in config.args
        assert "/home/user/documents" in config.args
        assert config.transport == TransportType.STDIO
        assert config.enabled is True

    def test_create_filesystem_config_with_options(self):
        """Test creating filesystem config with custom options."""
        config = FilesystemServerHelper.create_config(
            "/data",
            enabled=False,
            description="Custom filesystem server",
        )

        assert "/data" in config.args
        assert config.enabled is False
        assert config.description == "Custom filesystem server"

    def test_create_filesystem_config_rejects_relative_path(self):
        """Test that relative paths are rejected."""
        with pytest.raises(ValueError, match="absolute path"):
            FilesystemServerHelper.create_config("relative/path")

    def test_validate_directory_absolute_path(self):
        """Test directory validation for absolute paths."""
        is_valid, message = FilesystemServerHelper.validate_directory("/home/user/docs")
        # May not exist, but should be valid format
        assert is_valid
        assert "absolute" not in message.lower() or "valid" in message.lower()

    def test_validate_directory_rejects_relative_path(self):
        """Test directory validation rejects relative paths."""
        is_valid, message = FilesystemServerHelper.validate_directory("relative/path")

        assert not is_valid
        assert "absolute" in message.lower()

    def test_validate_directory_rejects_system_directories(self):
        """Test directory validation rejects system directories."""
        dangerous_paths = ["/", "/etc", "/usr", "/bin", "/sys"]

        for path in dangerous_paths:
            is_valid, message = FilesystemServerHelper.validate_directory(path)
            assert not is_valid
            assert "system directory" in message.lower()

    def test_validate_directory_rejects_system_subdirectories(self):
        """Test validation rejects subdirectories of system paths."""
        is_valid, message = FilesystemServerHelper.validate_directory("/etc/nginx")

        assert not is_valid
        assert "system directory" in message.lower()

    def test_get_available_tools(self):
        """Test getting list of filesystem tools."""
        tools = FilesystemServerHelper.get_available_tools()

        assert isinstance(tools, list)
        assert "read_file" in tools
        assert "write_file" in tools
        assert "list_directory" in tools

    def test_get_security_recommendations(self):
        """Test getting security recommendations."""
        recommendations = FilesystemServerHelper.get_security_recommendations()

        assert isinstance(recommendations, dict)
        assert "directory_permissions" in recommendations
        assert "path_configuration" in recommendations
        assert "monitoring" in recommendations

        # Check recommendations are non-empty lists
        for category, items in recommendations.items():
            assert isinstance(items, list)
            assert len(items) > 0


class TestWebSearchServerHelper:
    """Test cases for WebSearchServerHelper."""

    def test_create_brave_search_config(self):
        """Test creating Brave Search configuration."""
        config = WebSearchServerHelper.create_brave_search_config()

        assert config.command == "npx"
        assert "-y" in config.args
        assert "@modelcontextprotocol/server-brave-search" in config.args
        assert config.transport == TransportType.STDIO
        assert "BRAVE_API_KEY" in config.env
        assert config.enabled is True

    def test_create_brave_search_config_custom_env_var(self):
        """Test Brave Search config with custom environment variable."""
        config = WebSearchServerHelper.create_brave_search_config(
            api_key_env_var="CUSTOM_BRAVE_KEY"
        )

        assert "${CUSTOM_BRAVE_KEY}" in config.env["BRAVE_API_KEY"]

    def test_create_google_search_config(self):
        """Test creating Google Custom Search configuration."""
        config = WebSearchServerHelper.create_google_search_config()

        assert config.command == "npx"
        assert "@modelcontextprotocol/server-google-search" in config.args
        assert config.transport == TransportType.STDIO
        assert "GOOGLE_API_KEY" in config.env
        assert "GOOGLE_SEARCH_ENGINE_ID" in config.env

    def test_create_sse_search_config(self):
        """Test creating SSE-based search configuration."""
        config = WebSearchServerHelper.create_sse_search_config(
            "https://api.search.example.com"
        )

        assert config.command == "https://api.search.example.com"
        assert config.transport == TransportType.SSE
        assert "Authorization" in config.env
        assert "Bearer" in config.env["Authorization"]

    def test_create_sse_search_config_custom_token(self):
        """Test SSE search config with custom token variable."""
        config = WebSearchServerHelper.create_sse_search_config(
            "https://api.example.com",
            auth_token_env_var="CUSTOM_TOKEN",
        )

        assert "${CUSTOM_TOKEN}" in config.env["Authorization"]

    def test_get_available_tools(self):
        """Test getting available search tools."""
        tools = WebSearchServerHelper.get_available_tools()

        assert isinstance(tools, dict)
        assert "brave_search" in tools
        assert "google_search" in tools
        assert "generic" in tools

        # Check tool lists are non-empty
        for server_type, tool_list in tools.items():
            assert isinstance(tool_list, list)
            assert len(tool_list) > 0

    def test_get_rate_limit_recommendations(self):
        """Test getting rate limit recommendations."""
        recommendations = WebSearchServerHelper.get_rate_limit_recommendations()

        assert isinstance(recommendations, dict)
        assert "brave_search_free" in recommendations
        assert "google_custom_search_free" in recommendations
        assert "implementation" in recommendations

    def test_get_security_recommendations(self):
        """Test getting security recommendations."""
        recommendations = WebSearchServerHelper.get_security_recommendations()

        assert isinstance(recommendations, dict)
        assert "api_keys" in recommendations
        assert "query_validation" in recommendations
        assert "result_handling" in recommendations
        assert "cost_control" in recommendations

        # Check recommendations are non-empty lists
        for category, items in recommendations.items():
            assert isinstance(items, list)
            assert len(items) > 0

    def test_get_deployment_checklist(self):
        """Test getting deployment checklist."""
        checklist = WebSearchServerHelper.get_deployment_checklist()

        assert isinstance(checklist, dict)
        assert "pre_deployment" in checklist
        assert "deployment" in checklist
        assert "post_deployment" in checklist
        assert "ongoing_maintenance" in checklist

        # Check all phases have tasks
        for phase, tasks in checklist.items():
            assert isinstance(tasks, list)
            assert len(tasks) > 0
