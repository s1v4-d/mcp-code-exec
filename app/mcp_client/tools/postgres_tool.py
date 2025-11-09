"""PostgreSQL tool for MCP - Database access and querying."""

from typing import Dict, Any, List, Optional
import asyncio

from servers.postgres_mcp.server import (
    setup_server,
    execute_query,
    list_tables,
    get_table_schema,
    search_tables,
    _get_server_instance
)
from app.config import settings


class PostgresTool:
    """PostgreSQL tool for MCP using PostgreSQL MCP server."""
    
    def __init__(self):
        """Initialize PostgreSQL tool."""
        self._initialized = False
        self._init_lock = asyncio.Lock()
    
    async def _ensure_initialized(self):
        """Ensure PostgreSQL server is initialized."""
        if self._initialized:
            return
        
        async with self._init_lock:
            if self._initialized:
                return
            
            try:
                # Try to get existing instance
                _get_server_instance()
                self._initialized = True
            except RuntimeError:
                # Server not initialized, set it up
                await setup_server(
                    host=settings.postgres_host,
                    port=settings.postgres_port,
                    database=settings.postgres_db,
                    user=settings.postgres_user,
                    password=settings.postgres_password,
                )
                self._initialized = True
    
    async def execute_query_wrapper(
        self,
        query: str,
        read_only: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a SQL query safely.
        
        Args:
            query: SQL query to execute
            read_only: If True, only allow SELECT queries
            
        Returns:
            Query result with rows and metadata
        """
        await self._ensure_initialized()
        print(f"[PostgreSQL Tool] Executing query: {query[:100]}... (read_only={read_only})")
        return await execute_query(query, read_only)
    
    async def list_tables_wrapper(self, schema: str = "public") -> List[Dict[str, str]]:
        """
        List all tables in a schema.
        
        Args:
            schema: Database schema name
            
        Returns:
            List of table information dictionaries
        """
        await self._ensure_initialized()
        print(f"[PostgreSQL Tool] Listing tables in schema: {schema}")
        return await list_tables(schema)
    
    async def get_table_schema_wrapper(
        self,
        table_name: str,
        schema: str = "public"
    ) -> Dict[str, Any]:
        """
        Get detailed schema for a table.
        
        Args:
            table_name: Table name
            schema: Schema name
            
        Returns:
            Table schema with columns, types, and constraints
        """
        await self._ensure_initialized()
        print(f"[PostgreSQL Tool] Getting schema for table: {schema}.{table_name}")
        return await get_table_schema(table_name, schema)
    
    async def search_tables_wrapper(self, query: str) -> List[Dict[str, str]]:
        """
        Search for tables by name.
        
        Args:
            query: Search query
            
        Returns:
            List of matching tables
        """
        await self._ensure_initialized()
        print(f"[PostgreSQL Tool] Searching tables: {query}")
        return await search_tables(query)
    
    def get_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get tool definitions for MCP registration."""
        return {
            "postgres_execute_query": {
                "description": "Execute a SQL query on the PostgreSQL database. Use this to query database tables, get data, or perform analysis. Supports SELECT queries by default (read_only=True).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SQL query to execute (e.g., SELECT * FROM customers)"
                        },
                        "read_only": {
                            "type": "boolean",
                            "description": "Only allow SELECT queries if True",
                            "default": True
                        }
                    },
                    "required": ["query"]
                },
                "function": self.execute_query_wrapper
            },
            "postgres_list_tables": {
                "description": "List all tables in the PostgreSQL database. Use this to discover what tables are available.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "schema": {
                            "type": "string",
                            "description": "Database schema name",
                            "default": "public"
                        }
                    },
                    "required": []
                },
                "function": self.list_tables_wrapper
            },
            "postgres_get_table_schema": {
                "description": "Get detailed schema information for a specific table, including columns, types, and constraints.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table"
                        },
                        "schema": {
                            "type": "string",
                            "description": "Schema name",
                            "default": "public"
                        }
                    },
                    "required": ["table_name"]
                },
                "function": self.get_table_schema_wrapper
            },
            "postgres_search_tables": {
                "description": "Search for tables by name pattern.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query or pattern"
                        }
                    },
                    "required": ["query"]
                },
                "function": self.search_tables_wrapper
            }
        }
