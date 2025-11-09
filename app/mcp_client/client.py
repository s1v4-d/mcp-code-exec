"""MCP Client wrapper for tool interactions."""

from typing import Dict, Any, List
import json


class MCPClient:
    """
    Wrapper for MCP tool interactions.
    
    In a production system, this would connect to actual MCP servers.
    For the PoC, we simulate MCP tool calls with mock implementations.
    """
    
    def __init__(self):
        """Initialize the MCP client."""
        self.tools = {}
        self._register_tools()
    
    def _register_tools(self):
        """Register available tools."""
        # Import tools dynamically
        from app.mcp_client.tools.invoice_tool import InvoiceTool
        from app.mcp_client.tools.weather_tool import WeatherTool
        from app.mcp_client.tools.rag_tool import RAGTool
        from app.mcp_client.tools.postgres_tool import PostgresTool
        from app.config import settings
        
        # Register invoice tool
        invoice_tool = InvoiceTool()
        self.tools.update(invoice_tool.get_tools())
        
        # Register weather tool
        try:
            if settings.open_weather_api_key:
                weather_tool = WeatherTool(api_key=settings.open_weather_api_key)
                self.tools.update(weather_tool.get_tools())
                print("[MCP Client] Weather tool registered")
            else:
                print("[MCP Client] Weather tool skipped (no API key)")
        except Exception as e:
            print(f"[MCP Client] Warning: Could not register weather tool: {e}")
        
        # Register RAG tool
        try:
            rag_tool = RAGTool()
            self.tools.update(rag_tool.get_tools())
            print("[MCP Client] RAG tool registered")
        except Exception as e:
            print(f"[MCP Client] Warning: Could not register RAG tool: {e}")
        
        # Register PostgreSQL tool
        try:
            postgres_tool = PostgresTool()
            self.tools.update(postgres_tool.get_tools())
            print("[MCP Client] PostgreSQL tool registered")
        except Exception as e:
            print(f"[MCP Client] Warning: Could not register PostgreSQL tool: {e}")
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools with their definitions.
        
        Returns:
            List of tool definitions
        """
        tool_definitions = []
        for name, tool_info in self.tools.items():
            tool_definitions.append({
                "name": name,
                "description": tool_info["description"],
                "parameters": tool_info["parameters"]
            })
        return tool_definitions
    
    def get_tool_definitions_text(self) -> str:
        """
        Get tool definitions as formatted text for LLM.
        
        Returns:
            Formatted tool definitions
        """
        tools = self.list_tools()
        definitions = []
        
        for tool in tools:
            params = json.dumps(tool["parameters"], indent=2)
            definitions.append(
                f"Tool: {tool['name']}\n"
                f"Description: {tool['description']}\n"
                f"Parameters: {params}\n"
            )
        
        return "\n".join(definitions)
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call an MCP tool (supports both sync and async functions).
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments for the tool
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool not found
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}")
        
        tool_func = self.tools[tool_name]["function"]
        
        # Check if function is async
        import inspect
        if inspect.iscoroutinefunction(tool_func):
            return await tool_func(**arguments)
        else:
            return tool_func(**arguments)


# Global instance for use in generated code
mcp_client = MCPClient()
