"""
Core MCP client for calling tools from generated code.

This module provides the low-level interface for calling MCP tools
from agent-generated code. Tools are organized in server directories
and can be discovered progressively.
"""

from typing import Dict, Any, TYPE_CHECKING

# Import actual tool implementations
if TYPE_CHECKING:
    from app.mcp_client.tools.weather_tool import WeatherTool
    from app.mcp_client.tools.rag_tool import RAGTool
    from app.mcp_client.tools.invoice_tool import InvoiceTool


class MCPToolClient:
    """
    MCP tool client for calling tools from generated code.
    
    This client is injected into the code execution environment
    and provides access to registered MCP tool servers.
    """
    
    _instance = None
    _tools = {}
    
    def __new__(cls):
        """Singleton pattern to ensure one instance per execution."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the MCP client."""
        if not self._tools:
            self._register_tools()
    
    def _register_tools(self):
        """Register all available MCP tools."""
        from app.mcp_client.tools.weather_tool import WeatherTool
        from app.mcp_client.tools.rag_tool import RAGTool
        from app.mcp_client.tools.invoice_tool import InvoiceTool
        from app.config import settings
        
        # Weather tools
        if settings.open_weather_api_key:
            weather_tool = WeatherTool(api_key=settings.open_weather_api_key)
            self._tools.update(weather_tool.get_tools())
        
        # RAG tools
        rag_tool = RAGTool()
        self._tools.update(rag_tool.get_tools())
        
        # Invoice tools
        invoice_tool = InvoiceTool()
        self._tools.update(invoice_tool.get_tools())
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call an MCP tool by name.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments dictionary for the tool
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool not found
        """
        if tool_name not in self._tools:
            available = ", ".join(self._tools.keys())
            raise ValueError(
                f"Tool '{tool_name}' not found. Available tools: {available}"
            )
        
        tool_func = self._tools[tool_name]["function"]
        return tool_func(**arguments)


# Global instance for code execution
mcp_client = MCPToolClient()
