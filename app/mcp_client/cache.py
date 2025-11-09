"""Tool caching for MCP client to reduce redundant list_tools() calls."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, List, Optional


@dataclass
class CacheEntry:
    """Cached tool definitions with metadata."""
    
    tools: List[Dict]
    cached_at: datetime
    hits: int = 0


class ToolCache:
    """
    Thread-safe LRU cache for MCP tool definitions.
    
    Reduces redundant list_tools() calls by caching tool definitions
    with configurable TTL and max size.
    
    Example:
        cache = ToolCache(max_size=50, ttl_seconds=1800)
        
        # Try to get from cache
        tools = cache.get("weather_server")
        if tools is None:
            # Cache miss - fetch from server
            tools = fetch_tools_from_server()
            cache.set("weather_server", tools)
    """
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        Initialize tool cache.
        
        Args:
            max_size: Maximum number of entries to cache
            ttl_seconds: Time-to-live for cached entries in seconds
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._max_size = max_size
        self._ttl = timedelta(seconds=ttl_seconds)
    
    def get(self, server_name: str) -> Optional[List[Dict]]:
        """
        Get cached tools for a server.
        
        Args:
            server_name: Name of the MCP server
            
        Returns:
            Cached tools if found and not expired, None otherwise
        """
        with self._lock:
            entry = self._cache.get(server_name)
            if not entry:
                return None
            
            # Check TTL
            if datetime.now() - entry.cached_at > self._ttl:
                del self._cache[server_name]
                return None
            
            # Increment hit counter
            entry.hits += 1
            return entry.tools
    
    def set(self, server_name: str, tools: List[Dict]) -> None:
        """
        Cache tools for a server.
        
        If cache is at capacity, evicts the oldest entry.
        
        Args:
            server_name: Name of the MCP server
            tools: List of tool definitions to cache
        """
        with self._lock:
            # Evict oldest entry if at capacity
            if len(self._cache) >= self._max_size and server_name not in self._cache:
                oldest_key = min(
                    self._cache.items(),
                    key=lambda x: x[1].cached_at
                )[0]
                del self._cache[oldest_key]
            
            self._cache[server_name] = CacheEntry(
                tools=tools,
                cached_at=datetime.now()
            )
    
    def invalidate(self, server_name: str) -> None:
        """
        Invalidate cache for a specific server.
        
        Args:
            server_name: Name of the MCP server
        """
        with self._lock:
            self._cache.pop(server_name, None)
    
    def clear(self) -> None:
        """Clear entire cache."""
        with self._lock:
            self._cache.clear()
    
    def stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats including entry count,
            total hits, and server list
        """
        with self._lock:
            return {
                "entries": len(self._cache),
                "total_hits": sum(e.hits for e in self._cache.values()),
                "servers": list(self._cache.keys()),
                "max_size": self._max_size,
                "ttl_seconds": int(self._ttl.total_seconds())
            }
