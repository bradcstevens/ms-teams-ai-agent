# MCP (Model Context Protocol) Integration

This module provides configuration and management for MCP servers in the Azure AI Agent Framework for Microsoft Teams.

## Overview

The MCP integration allows the agent to connect to external context providers and tools through the Model Context Protocol. This enables:

- File system access
- External API integrations (GitHub, Slack, etc.)
- Custom tool servers
- Database connections
- And more...

## Architecture

```
mcp/
├── __init__.py          # Public API exports
├── config.py            # Pydantic configuration models
├── loader.py            # Configuration file loader
└── README.md            # This file
```

## Configuration

### Configuration File

Create a `mcp_servers.json` file in your project root. See `mcp_servers.json.example` for a complete example.

### Basic Structure

```json
{
  "mcpServers": {
    "server-name": {
      "command": "executable",
      "args": ["arg1", "arg2"],
      "env": {
        "VAR_NAME": "${ENV_VAR}"
      },
      "enabled": true,
      "transport": "stdio",
      "description": "Server description"
    }
  }
}
```

### Configuration Fields

#### Required Fields

- **command** (string): Executable command to start the MCP server
  - Examples: `"npx"`, `"python"`, `"node"`, `"/path/to/binary"`

#### Optional Fields

- **args** (array of strings): Command-line arguments
  - Default: `[]`
  - Example: `["-y", "@modelcontextprotocol/server-filesystem", "/path"]`

- **env** (object): Environment variables for the server process
  - Default: `{}`
  - Supports `${VAR_NAME}` substitution from host environment
  - Example: `{"API_KEY": "${PRODUCTION_API_KEY}"}`

- **enabled** (boolean): Whether the server is active
  - Default: `true`
  - Set to `false` to disable without removing configuration

- **transport** (string): Communication protocol
  - Values: `"stdio"` (default) or `"sse"`
  - `"stdio"`: Standard input/output (process-based)
  - `"sse"`: Server-Sent Events over HTTP

- **description** (string): Human-readable server description
  - Default: `null`
  - Used for documentation and logging

### Environment Variable Substitution

Environment variables are substituted using `${VAR_NAME}` syntax:

```json
{
  "mcpServers": {
    "api-server": {
      "command": "python",
      "env": {
        "API_KEY": "${PROD_API_KEY}",
        "ENDPOINT": "https://${API_HOST}/v1"
      }
    }
  }
}
```

Required environment variables must be set before loading the configuration:

```bash
export PROD_API_KEY="your-secret-key"
export API_HOST="api.example.com"
```

## Usage

### Loading Configuration

```python
from app.mcp import load_mcp_config, MCPConfigError

try:
    # Load from default path (mcp_servers.json)
    config = load_mcp_config()

    # Or specify custom path
    config = load_mcp_config("config/custom_mcp.json")
except MCPConfigError as e:
    print(f"Configuration error: {e}")
```

### Accessing Server Configurations

```python
# Get all servers
all_servers = config.mcpServers

# Get specific server
github_server = config.mcpServers.get("github")
if github_server:
    print(f"Command: {github_server.command}")
    print(f"Enabled: {github_server.enabled}")
```

### Filtering Enabled Servers

```python
# Get only enabled servers
enabled_servers = {
    name: server
    for name, server in config.mcpServers.items()
    if server.enabled
}

print(f"Active servers: {len(enabled_servers)}")
```

### Server Properties

```python
server = config.mcpServers["github"]

# Access configuration
print(f"Command: {server.command}")
print(f"Args: {server.args}")
print(f"Transport: {server.transport}")  # TransportType enum
print(f"Environment: {server.env}")
print(f"Enabled: {server.enabled}")
print(f"Description: {server.description}")
```

## Transport Types

### STDIO Transport

Process-based communication using standard input/output:

```json
{
  "command": "npx",
  "args": ["-y", "mcp-server-package"],
  "transport": "stdio"
}
```

Best for:
- NPM packages
- Python modules
- Local executables
- Simple request/response patterns

### SSE Transport

HTTP-based communication using Server-Sent Events:

```json
{
  "command": "node",
  "args": ["server.js"],
  "transport": "sse",
  "env": {
    "PORT": "3000"
  }
}
```

Best for:
- Remote servers
- Streaming responses
- Web-based integrations
- Scalable deployments

## Common Patterns

### NPM Package Server

```json
{
  "filesystem": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
    "transport": "stdio"
  }
}
```

### Python Module Server

```json
{
  "custom-tools": {
    "command": "python",
    "args": ["-m", "my_mcp_server"],
    "transport": "stdio"
  }
}
```

### Authenticated API Server

```json
{
  "github": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {
      "GITHUB_TOKEN": "${GITHUB_TOKEN}"
    },
    "transport": "stdio"
  }
}
```

### Development vs Production

```json
{
  "mcpServers": {
    "production-db": {
      "command": "python",
      "env": {
        "DB_CONNECTION": "${PROD_DB_URL}"
      },
      "enabled": true
    },
    "staging-db": {
      "command": "python",
      "env": {
        "DB_CONNECTION": "${STAGING_DB_URL}"
      },
      "enabled": false
    }
  }
}
```

## Error Handling

The loader provides detailed error messages for common issues:

### Missing Configuration File

```python
MCPConfigError: Configuration file 'mcp_servers.json' not found.
Please create a configuration file or check the path.
```

### Invalid JSON

```python
MCPConfigError: Invalid JSON in configuration file 'mcp_servers.json':
Expecting property name enclosed in double quotes: line 5 column 3 (char 78)
```

### Missing Environment Variable

```python
MCPConfigError: Environment variable 'GITHUB_TOKEN' not found.
Please set it before loading the configuration.
```

### Schema Validation Errors

```python
MCPConfigError: Configuration validation failed for 'mcp_servers.json':
  - mcpServers -> github -> command: Field required
  - mcpServers -> slack -> transport: Input should be 'stdio' or 'sse'
```

## Validation

The configuration system validates:

- Required fields are present
- Transport types are valid (`stdio` or `sse`)
- Server names use valid characters (alphanumeric, hyphens, underscores)
- Command is not empty
- Environment variables are properly formatted
- JSON structure matches schema

## Best Practices

### Security

1. Never commit secrets to configuration files
2. Use environment variable substitution for all credentials
3. Store secrets in Azure Key Vault or similar
4. Disable unused servers instead of removing them

### Organization

1. Group related servers together
2. Use descriptive server names
3. Add descriptions to all servers
4. Document required environment variables

### Performance

1. Only enable servers that are actively used
2. Use STDIO transport for local servers
3. Use SSE transport for remote/distributed servers
4. Monitor server startup times

### Testing

1. Create separate test configurations
2. Use different environment variables for test/prod
3. Validate configuration in CI/CD pipelines
4. Test with servers disabled

## Integration with Agent Framework

The MCP configuration will be used by the agent runtime to:

1. Initialize MCP server connections at startup
2. Route tool calls to appropriate servers
3. Manage server lifecycle (start, stop, restart)
4. Handle server failures and retries
5. Log server interactions for debugging

Example integration (future implementation):

```python
from app.mcp import load_mcp_config
from app.agent import AIAgent

# Load MCP configuration
mcp_config = load_mcp_config()

# Initialize agent with MCP servers
agent = AIAgent(
    mcp_servers=mcp_config.mcpServers,
    # ... other configuration
)

# Agent automatically connects to enabled MCP servers
await agent.initialize()
```

## Troubleshooting

### Server Won't Start

1. Check command exists in PATH
2. Verify environment variables are set
3. Check server logs for errors
4. Test command manually in terminal

### Environment Variable Not Found

1. Export required variables before running
2. Check `.env` file configuration
3. Verify variable names match exactly (case-sensitive)

### Invalid Transport Type

1. Use only `"stdio"` or `"sse"`
2. Check for typos in configuration
3. Verify JSON syntax is correct

### Configuration Not Loading

1. Check file path is correct
2. Verify JSON is valid (use JSON linter)
3. Check file permissions
4. Review error messages carefully

## Related Documentation

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Azure AI Agent Framework](../README.md)
- [Environment Configuration](../config/README.md)
- [Testing Guide](../../tests/README.md)

## Support

For issues or questions:

1. Check error messages for specific guidance
2. Review example configurations
3. Validate JSON syntax
4. Check environment variable setup
5. Review MCP server documentation
