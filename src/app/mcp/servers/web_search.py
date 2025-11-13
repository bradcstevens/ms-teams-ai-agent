"""Web search MCP server integration helper.

This module provides utilities for configuring and validating
web search MCP servers (both STDIO and SSE transports).

Web search servers allow agents to perform internet searches
and retrieve current information beyond their training data.
"""
import logging
from typing import Optional

from app.mcp.config import MCPServerConfig, TransportType

logger = logging.getLogger(__name__)


class WebSearchServerHelper:
    """Helper for web search MCP server configuration.

    Supports both STDIO and SSE-based web search MCP servers.
    Common implementations include:
    - Brave Search MCP server
    - Google Custom Search MCP server
    - DuckDuckGo MCP server
    - Perplexity MCP server (if available)

    Configuration example for STDIO transport:
    ```json
    {
      "mcpServers": {
        "web-search": {
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-brave-search"],
          "env": {
            "BRAVE_API_KEY": "${BRAVE_API_KEY}"
          },
          "transport": "stdio",
          "enabled": true
        }
      }
    }
    ```

    Configuration example for SSE transport:
    ```json
    {
      "mcpServers": {
        "web-search-api": {
          "command": "https://search-api.example.com",
          "env": {
            "Authorization": "Bearer ${API_TOKEN}"
          },
          "transport": "sse",
          "enabled": true
        }
      }
    }
    ```
    """

    # Common web search MCP server packages
    BRAVE_SEARCH_PACKAGE = "@modelcontextprotocol/server-brave-search"
    GOOGLE_SEARCH_PACKAGE = "@modelcontextprotocol/server-google-search"

    @staticmethod
    def create_brave_search_config(
        api_key_env_var: str = "BRAVE_API_KEY",
        enabled: bool = True,
        description: Optional[str] = None,
    ) -> MCPServerConfig:
        """Create Brave Search MCP server configuration.

        Brave Search provides privacy-focused web search with generous free tier.
        Requires Brave Search API key from https://brave.com/search/api/

        Args:
            api_key_env_var: Environment variable name containing API key
            enabled: Whether the server should be enabled
            description: Optional description for the server

        Returns:
            MCPServerConfig configured for Brave Search

        Examples:
            >>> config = WebSearchServerHelper.create_brave_search_config()
            >>> config.command
            'npx'
            >>> config.env
            {'BRAVE_API_KEY': '${BRAVE_API_KEY}'}
        """
        return MCPServerConfig(
            command="npx",
            args=["-y", WebSearchServerHelper.BRAVE_SEARCH_PACKAGE],
            env={
                "BRAVE_API_KEY": f"${{{api_key_env_var}}}",
            },
            transport=TransportType.STDIO,
            enabled=enabled,
            description=description or "Brave Search web search integration",
        )

    @staticmethod
    def create_google_search_config(
        api_key_env_var: str = "GOOGLE_API_KEY",
        search_engine_id_env_var: str = "GOOGLE_SEARCH_ENGINE_ID",
        enabled: bool = True,
        description: Optional[str] = None,
    ) -> MCPServerConfig:
        """Create Google Custom Search MCP server configuration.

        Google Custom Search requires:
        1. API key from Google Cloud Console
        2. Custom Search Engine ID from https://cse.google.com/

        Args:
            api_key_env_var: Environment variable name for API key
            search_engine_id_env_var: Environment variable name for search engine ID
            enabled: Whether the server should be enabled
            description: Optional description for the server

        Returns:
            MCPServerConfig configured for Google Custom Search
        """
        return MCPServerConfig(
            command="npx",
            args=["-y", WebSearchServerHelper.GOOGLE_SEARCH_PACKAGE],
            env={
                "GOOGLE_API_KEY": f"${{{api_key_env_var}}}",
                "GOOGLE_SEARCH_ENGINE_ID": f"${{{search_engine_id_env_var}}}",
            },
            transport=TransportType.STDIO,
            enabled=enabled,
            description=description or "Google Custom Search web search integration",
        )

    @staticmethod
    def create_sse_search_config(
        endpoint_url: str,
        auth_token_env_var: str = "SEARCH_API_TOKEN",
        enabled: bool = True,
        description: Optional[str] = None,
    ) -> MCPServerConfig:
        """Create SSE-based web search server configuration.

        For HTTP/SSE based search APIs that implement MCP protocol.

        Args:
            endpoint_url: Base URL for the search API endpoint
            auth_token_env_var: Environment variable name for auth token
            enabled: Whether the server should be enabled
            description: Optional description for the server

        Returns:
            MCPServerConfig configured for SSE transport

        Examples:
            >>> config = WebSearchServerHelper.create_sse_search_config(
            ...     "https://api.search.example.com"
            ... )
            >>> config.transport.value
            'sse'
        """
        return MCPServerConfig(
            command=endpoint_url,  # URL is stored in command for SSE transport
            args=[],
            env={
                "Authorization": f"Bearer ${{{auth_token_env_var}}}",
            },
            transport=TransportType.SSE,
            enabled=enabled,
            description=description or f"Web search API at {endpoint_url}",
        )

    @staticmethod
    def get_available_tools() -> dict[str, list[str]]:
        """Get typical tools provided by web search servers.

        Returns:
            Dictionary mapping server types to their typical tool lists

        Note:
            Actual tool schemas should be discovered via tools/list JSON-RPC call.
            This is a static reference for documentation purposes.
        """
        return {
            "brave_search": [
                "web_search",      # General web search
                "news_search",     # News-specific search
            ],
            "google_search": [
                "search",          # Custom search query
                "image_search",    # Image search (if enabled)
            ],
            "generic": [
                "search",          # Generic search tool name
            ],
        }

    @staticmethod
    def get_rate_limit_recommendations() -> dict[str, str]:
        """Get rate limiting recommendations for web search APIs.

        Returns:
            Dictionary of rate limiting best practices
        """
        return {
            "brave_search_free": "15,000 queries/month (500/day) on free tier",
            "google_custom_search_free": "100 queries/day on free tier",
            "implementation": "Implement client-side rate limiting with exponential backoff",
            "caching": "Cache search results for common queries (5-15 minutes TTL)",
            "monitoring": "Track query counts and costs via Application Insights",
            "fallback": "Configure fallback search provider if primary quota exceeded",
        }

    @staticmethod
    def get_security_recommendations() -> dict[str, list[str]]:
        """Get security recommendations for web search server deployment.

        Returns:
            Dictionary of security best practices organized by category
        """
        return {
            "api_keys": [
                "Store API keys in Azure Key Vault, not in code",
                "Use environment variables for configuration",
                "Rotate API keys regularly (90 days recommended)",
                "Monitor API key usage for anomalies",
            ],
            "query_validation": [
                "Sanitize user queries before sending to search API",
                "Implement query length limits",
                "Filter sensitive keywords from queries",
                "Log all search queries for audit purposes",
            ],
            "result_handling": [
                "Validate search results before returning to user",
                "Strip tracking parameters from URLs",
                "Implement content filtering for inappropriate results",
                "Cache results to minimize API calls",
            ],
            "cost_control": [
                "Set daily/monthly query quotas",
                "Implement alerts for quota threshold (80%)",
                "Use free tiers where possible",
                "Monitor cost per query in Application Insights",
            ],
        }

    @staticmethod
    def get_deployment_checklist() -> dict[str, list[str]]:
        """Get deployment checklist for web search integration.

        Returns:
            Dictionary of deployment tasks organized by phase
        """
        return {
            "pre_deployment": [
                "Obtain and validate API keys",
                "Configure environment variables in Key Vault",
                "Test search functionality locally",
                "Document rate limits and quotas",
            ],
            "deployment": [
                "Add search server to mcp_servers.json",
                "Enable server in configuration (enabled: true)",
                "Deploy updated container with npm dependencies",
                "Verify server connects successfully",
            ],
            "post_deployment": [
                "Test search queries through agent",
                "Monitor query success rate",
                "Validate result formatting",
                "Set up cost and quota alerts",
            ],
            "ongoing_maintenance": [
                "Review search query logs weekly",
                "Monitor API costs and quotas",
                "Update server packages monthly",
                "Audit and rotate API keys quarterly",
            ],
        }
