"""Tool Discovery Module - Public API

Provides progressive disclosure for MCP tools.
This module exposes a simple tool_discovery interface for agents to explore available
servers and tools on-demand.

Usage in generated code:
    from servers.discovery import tool_discovery
    
    # List available servers
    servers = tool_discovery.list_servers()  # ['invoice', 'postgres_mcp', 'rag', 'weather']
    
    # List tools for a specific server
    tools = tool_discovery.list_tools('weather')
    
    # Get tool definition
    tool_def = tool_discovery.get_tool_definition('weather', 'get_current_weather')
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import importlib
import ast


class ToolDiscovery:
    """Progressive disclosure tool discovery.
    
    Enables agents to discover MCP tools on-demand by exploring
    the servers/ directory structure.
    """
    
    def __init__(self, servers_dir: str = None):
        """Initialize tool discovery.
        
        Args:
            servers_dir: Path to servers directory. Auto-detected if None.
        """
        if servers_dir:
            self.servers_dir = Path(servers_dir)
        else:
            # Auto-detect: relative to this file
            self.servers_dir = Path(__file__).parent
        
        self._tool_cache: Dict[str, Dict[str, Any]] = {}
    
    def list_servers(self) -> List[str]:
        """List all available MCP servers.
        
        Returns:
            List of server names that agents can explore.
            
        Example:
            >>> tool_discovery.list_servers()
            ['invoice', 'postgres_mcp', 'rag', 'weather']
        """
        servers = []
        
        for item in self.servers_dir.iterdir():
            # Skip private directories and files
            if item.name.startswith("_") or item.name.startswith("."):
                continue
            
            # Skip non-directories
            if not item.is_dir():
                continue
            
            # Skip __pycache__
            if item.name == "__pycache__":
                continue
            
            # Only include directories with __init__.py (valid Python packages)
            if (item / "__init__.py").exists():
                servers.append(item.name)
        
        return sorted(servers)
    
    def list_tools(self, server: str = None) -> List[Dict[str, str]]:
        """List tools for a server or all servers.
        
        Args:
            server: Server name to list tools for. None for all servers.
            
        Returns:
            List of tool metadata dicts with 'server', 'name', 'description'.
            
        Example:
            >>> tool_discovery.list_tools('weather')
            [{'server': 'weather', 'name': 'get_current_weather', 'description': '...'}]
        """
        servers = [server] if server else self.list_servers()
        tools = []
        
        for srv_name in servers:
            srv_dir = self.servers_dir / srv_name
            
            if not srv_dir.exists():
                continue
            
            for py_file in srv_dir.glob("*.py"):
                # Skip __init__.py
                if py_file.name == "__init__.py":
                    continue
                
                tool_name = py_file.stem
                description = self._extract_docstring(py_file)
                
                tools.append({
                    "server": srv_name,
                    "name": tool_name,
                    "description": description or f"Tool: {tool_name}",
                    "path": f"servers/{srv_name}/{py_file.name}"
                })
        
        return tools
    
    def get_tool_definition(self, server: str, tool: str) -> Optional[str]:
        """Get the full definition of a specific tool.
        
        Args:
            server: Server name (e.g., 'weather')
            tool: Tool name (e.g., 'get_current_weather')
            
        Returns:
            Tool source code, or None if not found.
            
        Example:
            >>> source = tool_discovery.get_tool_definition('weather', 'get_current_weather')
            >>> print(source)  # Full Python source with function signature
        """
        tool_path = self.servers_dir / server / f"{tool}.py"
        
        if not tool_path.exists():
            return None
        
        return tool_path.read_text()
    
    def search_tools(self, query: str, detail_level: str = "summary") -> List[Dict[str, Any]]:
        """Search for tools matching a query.
        
        Args:
            query: Search query (matches tool name or description)
            detail_level: 'name_only', 'summary', or 'full'
            
        Returns:
            List of matching tools with requested detail level.
        """
        query_lower = query.lower()
        results = []
        
        for tool in self.list_tools():
            # Check if query matches name or description
            if (query_lower in tool["name"].lower() or 
                query_lower in tool["description"].lower() or
                query_lower in tool["server"].lower()):
                
                if detail_level == "name_only":
                    results.append({
                        "server": tool["server"],
                        "name": tool["name"]
                    })
                elif detail_level == "summary":
                    results.append(tool)
                else:  # full
                    tool_def = self.get_tool_definition(tool["server"], tool["name"])
                    results.append({**tool, "source": tool_def})
        
        return results
    
    def _extract_docstring(self, file_path: Path) -> Optional[str]:
        """Extract module docstring from a Python file."""
        try:
            source = file_path.read_text()
            tree = ast.parse(source)
            docstring = ast.get_docstring(tree)
            
            # If no module docstring, try to get first function's docstring
            if not docstring:
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        docstring = ast.get_docstring(node)
                        if docstring:
                            break
            
            return docstring
        except Exception:
            return None


# Singleton instance for convenient import
tool_discovery = ToolDiscovery()


# Also export the class for advanced usage
__all__ = ['tool_discovery', 'ToolDiscovery']
