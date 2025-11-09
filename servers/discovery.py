"""
Tool Discovery System for Progressive Disclosure (Async Version)

This module implements the filesystem-based tool discovery approach
described in the Anthropic MCP paper, enabling agents to:

1. List available MCP servers
2. List tools within a server
3. Read tool definitions on-demand
4. Search for relevant tools semantically

This dramatically reduces token consumption by loading only the tools
needed for a specific request.

PRINCIPLES:
- Fully async for all I/O operations
- Fail-fast: errors propagate with specific exception types
- No silent exception handling
- Uses aiofiles for async file I/O
- Uses AsyncOpenAI for async embeddings
"""

import asyncio
import json
import os
import pickle
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal

import aiofiles
import numpy as np

from app.exceptions import ToolDiscoveryError, ToolNotFoundError, ServerNotFoundError, ConfigurationError


class ToolDiscovery:
    """
    Async filesystem-based tool discovery for progressive disclosure.
    
    Tools are organized as:
    servers/
        <server_name>/
            __init__.py
            <tool_name>.py  # Each tool is a separate file
    """
    
    def __init__(self, servers_path: Path = None):
        """
        Initialize tool discovery.
        
        Args:
            servers_path: Path to servers directory (defaults to ./servers)
        """
        if servers_path is None:
            servers_path = Path(__file__).parent
        self.servers_path = Path(servers_path)
        self.embeddings_cache_file = self.servers_path / '.tool_embeddings_cache.pkl'
        self.embeddings_cache: Dict[str, np.ndarray] = {}
        self._openai_client = None
        self._cache_loaded = False
    
    def _get_openai_client(self):
        """
        Lazy load async OpenAI client.
        
        Raises:
            ConfigurationError: If OpenAI API key is not configured
        """
        if self._openai_client is None:
            from openai import AsyncOpenAI
            from app.config import settings
            
            if not settings.openai_api_key or settings.openai_api_key == "your-api-key-here":
                raise ConfigurationError(
                    "OpenAI API key not configured for embeddings. Set OPENAI_API_KEY environment variable."
                )
            
            self._openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        return self._openai_client
    
    async def _load_embeddings_cache(self):
        """
        Load cached tool embeddings asynchronously.
        
        Raises:
            ToolDiscoveryError: If cache file is corrupted
        """
        if self._cache_loaded:
            return
        
        if not self.embeddings_cache_file.exists():
            self.embeddings_cache = {}
            self._cache_loaded = True
            return
        
        async with aiofiles.open(self.embeddings_cache_file, 'rb') as f:
            content = await f.read()
            self.embeddings_cache = pickle.loads(content)
        
        self._cache_loaded = True
    
    async def _save_embeddings_cache(self):
        """
        Save tool embeddings cache asynchronously.
        
        Raises:
            ToolDiscoveryError: If save fails
        """
        async with aiofiles.open(self.embeddings_cache_file, 'wb') as f:
            await f.write(pickle.dumps(self.embeddings_cache))
    
    async def _get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding for text using OpenAI asynchronously.
        
        Args:
            text: Text to embed
            
        Returns:
            Numpy array of embedding
            
        Raises:
            ConfigurationError: If OpenAI client is not configured
            ToolDiscoveryError: If embedding generation fails
        """
        client = self._get_openai_client()
        
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return np.array(response.data[0].embedding, dtype=np.float32)
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    def list_servers(self) -> List[str]:
        """
        List all available MCP servers.
        
        Returns:
            List of server names
            
        Example:
            >>> discovery = ToolDiscovery()
            >>> servers = discovery.list_servers()
            >>> print(servers)
            ['weather', 'rag', 'invoice']
        """
        if not self.servers_path.exists():
            return []
        
        servers = []
        for item in self.servers_path.iterdir():
            if item.is_dir() and not item.name.startswith('_') and not item.name.startswith('.'):
                # Check if it has __init__.py (valid Python package)
                if (item / '__init__.py').exists():
                    servers.append(item.name)
        
        return sorted(servers)
    
    def list_tools(self, server_name: str) -> List[str]:
        """
        List all tools in a specific server.
        
        Args:
            server_name: Name of the server
            
        Returns:
            List of tool names (without .py extension)
            
        Raises:
            ServerNotFoundError: If server doesn't exist
            
        Example:
            >>> discovery = ToolDiscovery()
            >>> tools = discovery.list_tools('weather')
            >>> print(tools)
            ['get_current_weather', 'get_forecast', 'get_geo_data']
        """
        server_path = self.servers_path / server_name
        if not server_path.exists():
            raise ServerNotFoundError(f"Server '{server_name}' not found")
        
        tools = []
        for item in server_path.iterdir():
            if item.is_file() and item.suffix == '.py' and item.stem != '__init__':
                tools.append(item.stem)
        
        return sorted(tools)
    
    async def get_tool_summary(self, server_name: str, tool_name: str) -> Dict[str, str]:
        """
        Get a brief summary of a tool (name and description only).
        
        Args:
            server_name: Server name
            tool_name: Tool name
            
        Returns:
            Dictionary with 'name', 'server', and 'description'
            
        Raises:
            ToolNotFoundError: If tool doesn't exist
            
        Example:
            >>> discovery = ToolDiscovery()
            >>> summary = await discovery.get_tool_summary('weather', 'get_current_weather')
            >>> print(summary['description'])
            'Get current weather for a location.'
        """
        tool_path = self.servers_path / server_name / f"{tool_name}.py"
        if not tool_path.exists():
            raise ToolNotFoundError(f"Tool '{tool_name}' not found in server '{server_name}'")
        
        # Read first few lines for module docstring
        async with aiofiles.open(tool_path, 'r') as f:
            content = await f.read(500)  # Read first 500 chars
        
        # Extract first line of docstring
        match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if match:
            docstring = match.group(1).strip()
            # Get first non-empty line
            description = next((line.strip() for line in docstring.split('\n') if line.strip()), '')
        else:
            description = tool_name.replace('_', ' ').title()
        
        return {
            'name': tool_name,
            'server': server_name,
            'description': description
        }
    
    async def get_tool_definition(self, server_name: str, tool_name: str) -> str:
        """
        Get the full tool definition (source code).
        
        This is loaded on-demand only when the agent needs the complete
        interface and documentation.
        
        Args:
            server_name: Server name
            tool_name: Tool name
            
        Returns:
            Tool source code as string
            
        Raises:
            ToolNotFoundError: If tool doesn't exist
            
        Example:
            >>> discovery = ToolDiscovery()
            >>> definition = await discovery.get_tool_definition('weather', 'get_current_weather')
            >>> print(definition[:200])
        """
        tool_path = self.servers_path / server_name / f"{tool_name}.py"
        if not tool_path.exists():
            raise ToolNotFoundError(f"Tool '{tool_name}' not found in server '{server_name}'")
        
        async with aiofiles.open(tool_path, 'r') as f:
            return await f.read()
    
    async def read_file(self, file_path: str) -> str:
        """
        Read any file in the servers directory.
        
        Allows agents to explore the filesystem as shown in the paper.
        
        Args:
            file_path: Relative path from servers directory
            
        Returns:
            File contents as string
            
        Raises:
            ToolDiscoveryError: If path is outside servers directory or file doesn't exist
            
        Example:
            >>> discovery = ToolDiscovery()
            >>> content = await discovery.read_file('weather/get_current_weather.py')
        """
        full_path = self.servers_path / file_path
        
        # Security: ensure path is within servers directory
        full_path = full_path.resolve()
        if not str(full_path).startswith(str(self.servers_path.resolve())):
            raise ToolDiscoveryError(f"Path '{file_path}' is outside servers directory")
        
        if not full_path.exists():
            raise ToolDiscoveryError(f"File '{file_path}' not found")
        
        if not full_path.is_file():
            raise ToolDiscoveryError(f"Path '{file_path}' is not a file")
        
        async with aiofiles.open(full_path, 'r') as f:
            return await f.read()
    
    def list_directory(self, dir_path: str = "") -> List[str]:
        """
        List contents of a directory.
        
        Allows agents to explore the filesystem as shown in the paper.
        
        Args:
            dir_path: Relative path from servers directory (empty for root)
            
        Returns:
            List of filenames/directories
            
        Raises:
            ToolDiscoveryError: If path is outside servers directory or not a directory
            
        Example:
            >>> discovery = ToolDiscovery()
            >>> servers = discovery.list_directory()  # ['weather/', 'rag/', 'invoice/']
            >>> tools = discovery.list_directory('weather')  # ['get_current_weather.py', ...]
        """
        full_path = self.servers_path / dir_path if dir_path else self.servers_path
        
        # Security: ensure path is within servers directory
        full_path = full_path.resolve()
        if not str(full_path).startswith(str(self.servers_path.resolve())):
            raise ToolDiscoveryError(f"Path '{dir_path}' is outside servers directory")
        
        if not full_path.exists():
            raise ToolDiscoveryError(f"Directory '{dir_path}' not found")
        
        if not full_path.is_dir():
            raise ToolDiscoveryError(f"Path '{dir_path}' is not a directory")
        
        items = []
        for item in sorted(full_path.iterdir()):
            if item.name.startswith('.') or item.name.startswith('__'):
                continue
            if item.is_dir():
                items.append(f"{item.name}/")
            else:
                items.append(item.name)
        
        return items
    
    async def search_tools(
        self, 
        query: str, 
        top_k: int = 5,
        detail_level: Literal["name", "summary", "full"] = "summary",
        use_semantic: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for tools relevant to a query.
        
        Implements detail level parameter as described in the Anthropic paper:
        - "name": Only tool and server names
        - "summary": Names + brief descriptions  
        - "full": Complete tool definitions with schemas
        
        Args:
            query: Search query
            top_k: Number of results to return
            detail_level: Level of detail ("name" | "summary" | "full")
            use_semantic: Use semantic search (embeddings) if True, else keyword matching
            
        Returns:
            List of tool information dictionaries sorted by relevance
            
        Example:
            >>> discovery = ToolDiscovery()
            >>> # Just names for quick overview
            >>> results = await discovery.search_tools("weather", top_k=3, detail_level="name")
            >>> # [{"name": "get_current_weather", "server": "weather"}]
            >>> 
            >>> # With descriptions
            >>> results = await discovery.search_tools("weather", detail_level="summary")
            >>> # [{"name": "get_current_weather", "server": "weather", 
            >>> #   "description": "Get current weather..."}]
            >>>
            >>> # Full definitions
            >>> results = await discovery.search_tools("weather", detail_level="full")
            >>> # Returns complete source code with docstrings
        """
        # Try semantic search first if enabled
        if use_semantic:
            try:
                results = await self._semantic_search(query, top_k, detail_level)
                if results:
                    return results
            except ConfigurationError:
                # Fall back to keyword search if OpenAI not configured
                pass
        
        # Fallback to keyword search
        return await self._keyword_search(query, top_k, detail_level)
    
    async def _semantic_search(
        self, 
        query: str, 
        top_k: int,
        detail_level: str
    ) -> List[Dict[str, Any]]:
        """
        Semantic search using embeddings.
        
        Raises:
            ConfigurationError: If OpenAI is not configured
        """
        # Load cache first
        await self._load_embeddings_cache()
        
        query_embedding = await self._get_embedding(query)
        
        all_tools = []
        
        # Collect all tools with embeddings
        for server in self.list_servers():
            for tool in self.list_tools(server):
                cache_key = f"{server}.{tool}"
                
                # Get or compute embedding
                if cache_key not in self.embeddings_cache:
                    summary = await self.get_tool_summary(server, tool)
                    text = f"{summary['name']} {summary['description']}"
                    embedding = await self._get_embedding(text)
                    self.embeddings_cache[cache_key] = embedding
                    await self._save_embeddings_cache()
                
                similarity = self._cosine_similarity(
                    query_embedding, 
                    self.embeddings_cache[cache_key]
                )
                all_tools.append((similarity, server, tool))
        
        # Sort by similarity and get top_k
        all_tools.sort(key=lambda x: x[0], reverse=True)
        top_tools = all_tools[:top_k]
        
        # Format results based on detail level
        return await self._format_results(top_tools, detail_level)
    
    async def _keyword_search(
        self, 
        query: str, 
        top_k: int,
        detail_level: str
    ) -> List[Dict[str, Any]]:
        """Keyword-based search (fallback)."""
        query_lower = query.lower()
        query_terms = set(query_lower.split())
        
        all_tools = []
        
        # Collect all tools with relevance scores
        for server in self.list_servers():
            for tool in self.list_tools(server):
                summary = await self.get_tool_summary(server, tool)
                
                # Calculate relevance score
                text = f"{summary['name']} {summary['description']}".lower()
                
                # Exact phrase match
                if query_lower in text:
                    score = 10
                else:
                    # Term overlap
                    text_terms = set(text.split())
                    overlap = len(query_terms & text_terms)
                    score = overlap
                
                if score > 0:
                    all_tools.append((score, server, tool))
        
        # Sort by score and return top_k
        all_tools.sort(key=lambda x: x[0], reverse=True)
        top_tools = all_tools[:top_k]
        
        return await self._format_results(top_tools, detail_level)
    
    async def _format_results(
        self, 
        tools: List[tuple], 
        detail_level: str
    ) -> List[Dict[str, Any]]:
        """Format search results based on detail level."""
        results = []
        
        for score_or_similarity, server, tool_name in tools:
            if detail_level == "name":
                # Minimal: just names
                results.append({
                    "name": tool_name,
                    "server": server
                })
            
            elif detail_level == "summary":
                # Medium: names + descriptions
                summary = await self.get_tool_summary(server, tool_name)
                results.append(summary)
            
            elif detail_level == "full":
                # Maximum: complete definitions
                summary = await self.get_tool_summary(server, tool_name)
                definition = await self.get_tool_definition(server, tool_name)
                results.append({
                    **summary,
                    "definition": definition,
                    "import_statement": f"from servers.{server} import {tool_name}"
                })
        
        return results
    
    async def get_server_overview(self, server_name: str) -> Dict[str, Any]:
        """
        Get an overview of a server and its tools.
        
        Args:
            server_name: Server name
            
        Returns:
            Dictionary with server info and tool summaries
            
        Raises:
            ServerNotFoundError: If server doesn't exist
            
        Example:
            >>> discovery = ToolDiscovery()
            >>> overview = await discovery.get_server_overview('weather')
            >>> print(f"Server: {overview['name']}")
            >>> print(f"Tools: {len(overview['tools'])}")
        """
        tools = []
        for tool_name in self.list_tools(server_name):
            summary = await self.get_tool_summary(server_name, tool_name)
            tools.append(summary)
        
        # Read server __init__.py docstring
        init_path = self.servers_path / server_name / '__init__.py'
        description = ''
        if init_path.exists():
            async with aiofiles.open(init_path, 'r') as f:
                content = await f.read(500)
                match = re.search(r'"""(.*?)"""', content, re.DOTALL)
                if match:
                    description = match.group(1).strip()
        
        return {
            'name': server_name,
            'description': description,
            'tool_count': len(tools),
            'tools': tools
        }
    
    async def get_all_tools_summary(self) -> List[Dict[str, str]]:
        """
        Get a compact summary of all available tools.
        
        Returns name and description only (not full definitions).
        This is much smaller than loading all tool definitions.
        
        Returns:
            List of tool summaries
        """
        summaries = []
        for server in self.list_servers():
            for tool in self.list_tools(server):
                summary = await self.get_tool_summary(server, tool)
                summaries.append(summary)
        return summaries


# Global instance
tool_discovery = ToolDiscovery()
