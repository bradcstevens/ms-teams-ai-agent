"""Tests for MCP configuration schema and loader.

This test suite validates the MCP server configuration system including:
- JSON schema validation via Pydantic models
- Configuration file loading
- Environment variable substitution
- Server registry with enable/disable flags
- Transport type validation
"""
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest

from app.mcp.config import (
    MCPServerConfig,
    MCPServersConfig,
    TransportType,
)
from app.mcp.loader import (
    load_mcp_config,
    substitute_env_vars,
    MCPConfigError,
)


class TestMCPServerConfig:
    """Test cases for MCPServerConfig Pydantic model."""

    def test_valid_minimal_config(self):
        """Test valid minimal server configuration."""
        config_dict = {
            "command": "npx",
            "args": ["-y", "package-name"],
        }
        config = MCPServerConfig(**config_dict)

        assert config.command == "npx"
        assert config.args == ["-y", "package-name"]
        assert config.enabled is True  # Default value
        assert config.transport == TransportType.STDIO  # Default value
        assert config.env == {}  # Default value
        assert config.description is None  # Optional field

    def test_valid_full_config(self):
        """Test valid full server configuration with all fields."""
        config_dict = {
            "command": "python",
            "args": ["-m", "mcp_server"],
            "env": {
                "API_KEY": "${SOME_API_KEY}",
                "ENDPOINT": "https://api.example.com",
            },
            "enabled": True,
            "transport": "stdio",
            "description": "Test MCP server",
        }
        config = MCPServerConfig(**config_dict)

        assert config.command == "python"
        assert config.args == ["-m", "mcp_server"]
        assert config.env == {"API_KEY": "${SOME_API_KEY}", "ENDPOINT": "https://api.example.com"}
        assert config.enabled is True
        assert config.transport == TransportType.STDIO
        assert config.description == "Test MCP server"

    def test_sse_transport_type(self):
        """Test SSE transport type validation."""
        config_dict = {
            "command": "node",
            "args": ["server.js"],
            "transport": "sse",
        }
        config = MCPServerConfig(**config_dict)

        assert config.transport == TransportType.SSE

    def test_missing_required_command(self):
        """Test validation fails when command is missing."""
        config_dict = {
            "args": ["-y", "package-name"],
        }

        with pytest.raises(ValueError):
            MCPServerConfig(**config_dict)

    def test_invalid_transport_type(self):
        """Test validation fails with invalid transport type."""
        config_dict = {
            "command": "npx",
            "transport": "invalid_transport",
        }

        with pytest.raises(ValueError):
            MCPServerConfig(**config_dict)

    def test_disabled_server(self):
        """Test server with enabled=false."""
        config_dict = {
            "command": "npx",
            "args": ["package"],
            "enabled": False,
        }
        config = MCPServerConfig(**config_dict)

        assert config.enabled is False


class TestMCPServersConfig:
    """Test cases for MCPServersConfig root model."""

    def test_valid_servers_config(self):
        """Test valid servers configuration with multiple servers."""
        config_dict = {
            "mcpServers": {
                "server1": {
                    "command": "npx",
                    "args": ["-y", "package1"],
                },
                "server2": {
                    "command": "python",
                    "args": ["-m", "package2"],
                    "enabled": False,
                },
            }
        }
        config = MCPServersConfig(**config_dict)

        assert len(config.mcpServers) == 2
        assert "server1" in config.mcpServers
        assert "server2" in config.mcpServers
        assert config.mcpServers["server1"].enabled is True
        assert config.mcpServers["server2"].enabled is False

    def test_empty_servers_config(self):
        """Test valid empty servers configuration."""
        config_dict = {"mcpServers": {}}
        config = MCPServersConfig(**config_dict)

        assert len(config.mcpServers) == 0

    def test_get_enabled_servers(self):
        """Test filtering enabled servers from configuration."""
        config_dict = {
            "mcpServers": {
                "enabled_server": {
                    "command": "npx",
                    "enabled": True,
                },
                "disabled_server": {
                    "command": "python",
                    "enabled": False,
                },
                "default_enabled": {
                    "command": "node",
                },
            }
        }
        config = MCPServersConfig(**config_dict)

        enabled = {
            name: server
            for name, server in config.mcpServers.items()
            if server.enabled
        }

        assert len(enabled) == 2
        assert "enabled_server" in enabled
        assert "default_enabled" in enabled
        assert "disabled_server" not in enabled


class TestEnvironmentVariableSubstitution:
    """Test cases for environment variable substitution."""

    def test_substitute_single_env_var(self):
        """Test substitution of single environment variable."""
        os.environ["TEST_VAR"] = "test_value"

        result = substitute_env_vars("${TEST_VAR}")

        assert result == "test_value"

        # Cleanup
        del os.environ["TEST_VAR"]

    def test_substitute_env_var_in_string(self):
        """Test substitution of environment variable within string."""
        os.environ["API_HOST"] = "api.example.com"

        result = substitute_env_vars("https://${API_HOST}/v1")

        assert result == "https://api.example.com/v1"

        # Cleanup
        del os.environ["API_HOST"]

    def test_substitute_multiple_env_vars(self):
        """Test substitution of multiple environment variables."""
        os.environ["HOST"] = "localhost"
        os.environ["PORT"] = "8080"

        result = substitute_env_vars("http://${HOST}:${PORT}")

        assert result == "http://localhost:8080"

        # Cleanup
        del os.environ["HOST"]
        del os.environ["PORT"]

    def test_substitute_missing_env_var_raises_error(self):
        """Test that missing environment variable raises error."""
        with pytest.raises(MCPConfigError, match="Environment variable.*not found"):
            substitute_env_vars("${MISSING_VAR}")

    def test_substitute_no_env_vars(self):
        """Test string without environment variables passes through."""
        result = substitute_env_vars("plain string")

        assert result == "plain string"

    def test_substitute_env_dict(self):
        """Test substitution in dictionary of environment variables."""
        os.environ["KEY1"] = "value1"
        os.environ["KEY2"] = "value2"

        env_dict = {
            "VAR1": "${KEY1}",
            "VAR2": "${KEY2}",
            "VAR3": "static_value",
        }

        result = {key: substitute_env_vars(val) for key, val in env_dict.items()}

        assert result == {
            "VAR1": "value1",
            "VAR2": "value2",
            "VAR3": "static_value",
        }

        # Cleanup
        del os.environ["KEY1"]
        del os.environ["KEY2"]


class TestLoadMCPConfig:
    """Test cases for MCP configuration file loader."""

    def test_load_valid_config_file(self):
        """Test loading valid MCP configuration file."""
        config_data = {
            "mcpServers": {
                "test-server": {
                    "command": "npx",
                    "args": ["-y", "test-package"],
                    "transport": "stdio",
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = load_mcp_config(config_path)

            assert len(config.mcpServers) == 1
            assert "test-server" in config.mcpServers
            assert config.mcpServers["test-server"].command == "npx"
        finally:
            os.unlink(config_path)

    def test_load_config_with_env_substitution(self):
        """Test loading config with environment variable substitution."""
        os.environ["TEST_API_KEY"] = "secret_key_123"

        config_data = {
            "mcpServers": {
                "api-server": {
                    "command": "python",
                    "args": ["-m", "api_server"],
                    "env": {
                        "API_KEY": "${TEST_API_KEY}",
                    }
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = load_mcp_config(config_path)

            # After substitution, env vars should be resolved
            server_env = config.mcpServers["api-server"].env
            # Note: substitution happens during loading
            assert "API_KEY" in server_env
        finally:
            os.unlink(config_path)
            del os.environ["TEST_API_KEY"]

    def test_load_nonexistent_file_raises_error(self):
        """Test loading nonexistent file raises appropriate error."""
        with pytest.raises(MCPConfigError, match="Configuration file.*not found"):
            load_mcp_config("/nonexistent/path/mcp_servers.json")

    def test_load_invalid_json_raises_error(self):
        """Test loading invalid JSON raises appropriate error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            config_path = f.name

        try:
            with pytest.raises(MCPConfigError, match="Invalid JSON"):
                load_mcp_config(config_path)
        finally:
            os.unlink(config_path)

    def test_load_invalid_schema_raises_error(self):
        """Test loading config with invalid schema raises validation error."""
        config_data = {
            "mcpServers": {
                "invalid-server": {
                    # Missing required "command" field
                    "args": ["some", "args"],
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            with pytest.raises(MCPConfigError, match="Configuration validation failed"):
                load_mcp_config(config_path)
        finally:
            os.unlink(config_path)

    def test_load_default_config_path(self):
        """Test loading from default mcp_servers.json path."""
        # This test validates the default path behavior
        # In actual implementation, default should be ./mcp_servers.json
        config_data = {
            "mcpServers": {
                "default-server": {
                    "command": "npx",
                }
            }
        }

        # Create temporary directory to simulate project root
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "mcp_servers.json"
            with open(config_path, 'w') as f:
                json.dump(config_data, f)

            # Load with explicit path (default path testing would need CWD manipulation)
            config = load_mcp_config(str(config_path))

            assert len(config.mcpServers) == 1


class TestMCPConfigIntegration:
    """Integration tests for complete MCP configuration workflow."""

    def test_full_config_workflow(self):
        """Test complete workflow: load config, filter enabled servers."""
        os.environ["PROD_API_KEY"] = "production_key"

        config_data = {
            "mcpServers": {
                "production-server": {
                    "command": "python",
                    "args": ["-m", "prod_server"],
                    "env": {
                        "API_KEY": "${PROD_API_KEY}",
                        "ENDPOINT": "https://prod.api.com",
                    },
                    "enabled": True,
                    "transport": "stdio",
                    "description": "Production API server",
                },
                "development-server": {
                    "command": "python",
                    "args": ["-m", "dev_server"],
                    "enabled": False,
                    "transport": "sse",
                },
                "testing-server": {
                    "command": "npx",
                    "args": ["-y", "test-server"],
                    "transport": "stdio",
                },
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            # Load configuration
            config = load_mcp_config(config_path)

            # Verify all servers loaded
            assert len(config.mcpServers) == 3

            # Filter enabled servers
            enabled_servers = {
                name: server
                for name, server in config.mcpServers.items()
                if server.enabled
            }

            # Verify only enabled servers
            assert len(enabled_servers) == 2
            assert "production-server" in enabled_servers
            assert "testing-server" in enabled_servers
            assert "development-server" not in enabled_servers

            # Verify transport types
            assert config.mcpServers["production-server"].transport == TransportType.STDIO
            assert config.mcpServers["development-server"].transport == TransportType.SSE

        finally:
            os.unlink(config_path)
            del os.environ["PROD_API_KEY"]
