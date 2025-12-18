"""MCP Client Manager with lazy loading and state machine."""

import asyncio
import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .config_models import McpConfiguration, ServerConfig


logger = logging.getLogger("mcp_execution.manager")


class ConnectionState(Enum):
    """Client manager lifecycle states."""
    UNINITIALIZED = "uninitialized"
    READY = "ready"  # Config loaded, no connections
    CONNECTED = "connected"  # At least one server connected


class ToolConnectionError(Exception):
    """Raised when tool server connection fails."""
    pass


class ToolNotFoundError(Exception):
    """Raised when tool doesn't exist."""
    pass


class ToolExecutionError(Exception):
    """Raised when tool execution fails."""
    pass


class McpManager:
    """MCP client manager with lazy loading."""
    
    _instance: Optional["McpManager"] = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize unconnected manager."""
        if not hasattr(self, "_initialized"):
            self._state = ConnectionState.UNINITIALIZED
            self._config: Optional[McpConfiguration] = None
            self._sessions: Dict[str, ClientSession] = {}
            self._tool_cache: Dict[str, list] = {}
            self._stdio_contexts: Dict[str, Any] = {}
            self._session_contexts: Dict[str, Any] = {}
            self._read_streams: Dict[str, Any] = {}
            self._write_streams: Dict[str, Any] = {}
            self._initialized = True
    
    def _check_state(self, required: ConnectionState, operation: str):
        """Validate state before operation."""
        if self._state.value != required.value:
            raise RuntimeError(
                f"Cannot {operation}: state is {self._state.value}, "
                f"need {required.value}"
            )
    
    def _check_state_at_least(self, minimum: ConnectionState, operation: str):
        """Validate state is at least minimum."""
        states = [s.value for s in ConnectionState]
        current_idx = states.index(self._state.value)
        min_idx = states.index(minimum.value)
        
        if current_idx < min_idx:
            raise RuntimeError(
                f"Cannot {operation}: state is {self._state.value}, "
                f"need at least {minimum.value}"
            )
    
    async def load_config(self, config_path: Optional[Path] = None):
        """Load MCP configuration without connecting."""
        self._check_state(ConnectionState.UNINITIALIZED, "load config")
        
        path = config_path or Path.cwd() / "mcp_config.json"
        
        try:
            self._config = McpConfiguration.load_from_file(path)
            active = len(self._config.active_servers())
            total = len(self._config.mcpServers)
            
            logger.info(
                f"Config loaded: {total} servers ({active} active)"
            )
            
            self._state = ConnectionState.READY
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    async def _connect_server(self, name: str, config: ServerConfig):
        """
        Connect to a single MCP server lazily.
        
        This is called on-demand when a tool is first requested.
        """
        if name in self._sessions:
            logger.debug(f"Server '{name}' already connected")
            return
        
        logger.info(f"Connecting to server: {name}")
        
        try:
            # Build server parameters
            params = StdioServerParameters(
                command=config.command,
                args=config.args,
                env=config.env or {},
            )
            
            # Create stdio context
            stdio_ctx = stdio_client(params)
            streams = await stdio_ctx.__aenter__()
            read_stream, write_stream = streams
            
            # Store context for cleanup
            self._stdio_contexts[name] = stdio_ctx
            self._read_streams[name] = read_stream
            self._write_streams[name] = write_stream
            
            # Create session
            session_ctx = ClientSession(read_stream, write_stream)
            client = await session_ctx.__aenter__()
            await client.initialize()
            
            # Store session and context
            self._sessions[name] = client
            self._session_contexts[name] = session_ctx
            
            self._state = ConnectionState.CONNECTED
            logger.info(f"Connected to server: {name}")
            
        except Exception as e:
            # Cleanup partial connection
            if name in self._stdio_contexts:
                try:
                    await self._stdio_contexts[name].__aexit__(None, None, None)
                except:
                    pass
                del self._stdio_contexts[name]
            
            logger.error(f"Connection failed for '{name}': {e}")
            raise ToolConnectionError(f"Cannot connect to server '{name}': {e}")
    
    async def _fetch_tools(self, server_name: str) -> list:
        """Get tools from server, using cache if available."""
        # Check cache first
        if server_name in self._tool_cache:
            logger.debug(f"Using cached tools for: {server_name}")
            return self._tool_cache[server_name]
        
        # Ensure connected
        if server_name not in self._sessions:
            raise ToolConnectionError(f"Not connected to server: {server_name}")
        
        try:
            session = self._sessions[server_name]
            response = await session.list_tools()
            
            # Defensive unwrapping (handle response variations)
            tools = getattr(response, "tools", [])
            
            # Cache results
            self._tool_cache[server_name] = tools
            logger.debug(f"Cached {len(tools)} tools for: {server_name}")
            
            return tools
            
        except Exception as e:
            logger.error(f"Failed to list tools from '{server_name}': {e}")
            raise ToolConnectionError(f"Cannot list tools from '{server_name}': {e}")
    
    async def execute_tool(self, tool_id: str, params: Dict[str, Any]) -> Any:
        """Execute an MCP tool with lazy connection."""
        self._check_state_at_least(ConnectionState.READY, "execute tool")
        
        if not self._config:
            raise RuntimeError("Configuration not loaded")
        
        # Parse tool identifier
        if "__" not in tool_id:
            raise ToolNotFoundError(
                f"Invalid tool ID '{tool_id}'. "
                f"Expected format: 'serverName__toolName'"
            )
        
        server_name, tool_name = tool_id.split("__", 1)
        
        # Get server config
        server_config = self._config.get_server(server_name)
        if not server_config:
            available = list(self._config.mcpServers.keys())
            raise ToolNotFoundError(
                f"Server '{server_name}' not found. "
                f"Available: {available}"
            )
        
        if server_config.disabled:
            raise ToolNotFoundError(f"Server '{server_name}' is disabled")
        
        # Lazy connect if needed
        if server_name not in self._sessions:
            logger.debug(f"Lazy connecting for tool: {tool_id}")
            await self._connect_server(server_name, server_config)
        
        # Verify tool exists
        tools = await self._fetch_tools(server_name)
        tool_names = [t.name for t in tools]
        
        if tool_name not in tool_names:
            raise ToolNotFoundError(
                f"Tool '{tool_name}' not found on '{server_name}'. "
                f"Available: {tool_names}"
            )
        
        # Execute tool
        try:
            session = self._sessions[server_name]
            logger.info(f"Executing: {tool_id}")
            logger.debug(f"Parameters: {params}")
            
            result = await session.call_tool(tool_name, params)
            
            # Defensive unwrapping (handle different response formats)
            if hasattr(result, "content"):
                unwrapped = result.content
            elif hasattr(result, "value"):
                unwrapped = result.value
            else:
                unwrapped = result
            
            logger.debug(f"Tool completed: {tool_id}")
            return unwrapped
            
        except Exception as e:
            logger.error(f"Tool execution failed for '{tool_id}': {e}")
            raise ToolExecutionError(f"Execution failed for '{tool_id}': {e}")
    
    async def list_all_tools(self) -> list:
        """
        List all tools from all active servers.
        
        Connects to all servers if needed (lazy).
        """
        self._check_state_at_least(ConnectionState.READY, "list all tools")
        
        if not self._config:
            raise RuntimeError("Configuration not loaded")
        
        all_tools = []
        active = self._config.active_servers()
        
        logger.info(f"Listing tools from {len(active)} servers")
        
        for server_name, server_config in active.items():
            try:
                # Connect if needed
                if server_name not in self._sessions:
                    await self._connect_server(server_name, server_config)
                
                # Get tools (cached)
                tools = await self._fetch_tools(server_name)
                all_tools.extend(tools)
                logger.debug(f"Server '{server_name}': {len(tools)} tools")
                
            except Exception as e:
                logger.warning(f"Skipping '{server_name}': {e}")
                continue
        
        logger.info(f"Total tools: {len(all_tools)}")
        return all_tools
    
    async def shutdown(self):
        """Clean up all connections."""
        logger.info("Shutting down MCP connections")
        
        # Close all sessions (don't use context manager exit, just close clients)
        for name in list(self._sessions.keys()):
            try:
                # Sessions will be cleaned up when stdio closes
                self._sessions.pop(name, None)
                self._session_contexts.pop(name, None)
                logger.debug(f"Removed session: {name}")
            except Exception as e:
                logger.warning(f"Error removing session '{name}': {e}")
        
        # Close stdio contexts more carefully
        for name in list(self._stdio_contexts.keys()):
            try:
                # Just remove references, let Python GC handle cleanup
                self._stdio_contexts.pop(name, None)
                self._read_streams.pop(name, None)
                self._write_streams.pop(name, None)
                logger.debug(f"Removed stdio: {name}")
            except Exception as e:
                logger.warning(f"Error removing stdio '{name}': {e}")
        
        # Clear cache
        self._tool_cache.clear()
        self._state = ConnectionState.UNINITIALIZED
        
        logger.info("Shutdown complete")


# Global singleton instance
_manager_instance: Optional[McpManager] = None


def get_mcp_manager() -> McpManager:
    """Get or create the global MCP manager instance."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = McpManager()
    return _manager_instance


async def call_tool(tool_id: str, params: Dict[str, Any]) -> Any:
    """
    Convenience function for calling tools.
    
    Args:
        tool_id: Tool identifier like "weather__get_current"
        params: Tool parameters
        
    Returns:
        Tool result
    """
    manager = get_mcp_manager()
    return await manager.execute_tool(tool_id, params)
