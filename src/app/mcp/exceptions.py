"""Custom exceptions for MCP client and connection management."""


class MCPConnectionError(Exception):
    """Raised when MCP client fails to establish or maintain a connection."""

    pass


class MCPTransportError(Exception):
    """Raised when there's an error with the transport layer (STDIO/SSE)."""

    pass


class MCPTimeoutError(Exception):
    """Raised when an MCP operation times out."""

    pass
