"""
Custom exceptions for MCP Code Execution system.

Following the fail-fast principle, we define specific exceptions
that propagate errors clearly instead of silently catching them.
"""


class MCPError(Exception):
    """Base exception for all MCP-related errors."""
    pass


class ToolNotFoundError(MCPError):
    """Raised when a requested tool is not found."""
    pass


class ToolExecutionError(MCPError):
    """Raised when tool execution fails."""
    pass


class ServerNotFoundError(MCPError):
    """Raised when a requested server is not found."""
    pass


class CodeExecutionError(MCPError):
    """Raised when generated code fails to execute."""
    pass


class CodeValidationError(MCPError):
    """Raised when generated code fails validation."""
    pass


class ToolDiscoveryError(MCPError):
    """Raised when tool discovery fails."""
    pass


class APIError(MCPError):
    """Raised when external API calls fail."""
    pass


class WeatherAPIError(APIError):
    """Raised when Weather API calls fail."""
    pass


class RAGError(MCPError):
    """Raised when RAG operations fail."""
    pass


class ConfigurationError(MCPError):
    """Raised when configuration is invalid or missing."""
    pass
