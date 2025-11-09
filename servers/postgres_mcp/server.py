"""PostgreSQL MCP Server

Provides safe, controlled access to PostgreSQL databases through MCP tools.
Implements query validation, schema inspection, and safe execution.
"""

import asyncio
import asyncpg
from typing import Dict, Any, List, Optional
from pathlib import Path

from .safe_executor import SafeQueryExecutor
from .schema_inspector import SchemaInspector


class PostgresServer:
    """PostgreSQL MCP Server implementation."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "postgres",
        user: str = "postgres",
        password: str = "postgres",
    ):
        """Initialize PostgreSQL server.
        
        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
        """
        self.connection_params = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password,
        }
        self.pool: Optional[asyncpg.Pool] = None
        self.executor: Optional[SafeQueryExecutor] = None
        self.inspector: Optional[SchemaInspector] = None
    
    async def start(self):
        """Start the server and initialize connection pool."""
        # Create connection pool
        self.pool = await asyncpg.create_pool(**self.connection_params)
        
        # Initialize executor and inspector
        self.executor = SafeQueryExecutor(self.pool)
        self.inspector = SchemaInspector(self.pool)
    
    async def stop(self):
        """Stop the server and close connections."""
        if self.pool:
            await self.pool.close()
    
    async def execute_query(
        self,
        query: str,
        params: Optional[List[Any]] = None,
        read_only: bool = True,
    ) -> Dict[str, Any]:
        """Execute a SQL query safely.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            read_only: If True, only allow SELECT queries
            
        Returns:
            Query result with rows and metadata
        """
        if not self.executor:
            raise RuntimeError("Server not started")
        
        return await self.executor.execute(
            query=query,
            params=params or [],
            read_only=read_only,
        )
    
    async def list_tables(self, schema: str = "public") -> List[Dict[str, str]]:
        """List all tables in a schema.
        
        Args:
            schema: Database schema name
            
        Returns:
            List of table information dictionaries
        """
        if not self.inspector:
            raise RuntimeError("Server not started")
        
        return await self.inspector.list_tables(schema)
    
    async def get_table_schema(
        self,
        table_name: str,
        schema: str = "public",
    ) -> Dict[str, Any]:
        """Get detailed schema for a table.
        
        Args:
            table_name: Table name
            schema: Schema name
            
        Returns:
            Table schema with columns, types, and constraints
        """
        if not self.inspector:
            raise RuntimeError("Server not started")
        
        return await self.inspector.get_table_schema(table_name, schema)
    
    async def search_tables(self, query: str) -> List[Dict[str, str]]:
        """Search for tables by name.
        
        Args:
            query: Search query
            
        Returns:
            List of matching tables
        """
        if not self.inspector:
            raise RuntimeError("Server not started")
        
        return await self.inspector.search_tables(query)


# Tool functions for MCP integration

async def execute_query(query: str, read_only: bool = True) -> Dict[str, Any]:
    """Execute a SQL query.
    
    Args:
        query: SQL query to execute
        read_only: Only allow SELECT queries if True
        
    Returns:
        Query results
    """
    # Get server instance (configured elsewhere)
    server = _get_server_instance()
    return await server.execute_query(query, read_only=read_only)


async def list_tables(schema: str = "public") -> List[Dict[str, str]]:
    """List all tables in a schema.
    
    Args:
        schema: Database schema name
        
    Returns:
        List of tables
    """
    server = _get_server_instance()
    return await server.list_tables(schema)


async def get_table_schema(table_name: str, schema: str = "public") -> Dict[str, Any]:
    """Get table schema.
    
    Args:
        table_name: Table name
        schema: Schema name
        
    Returns:
        Table schema
    """
    server = _get_server_instance()
    return await server.get_table_schema(table_name, schema)


async def search_tables(query: str) -> List[Dict[str, str]]:
    """Search for tables by name.
    
    Args:
        query: Search query
        
    Returns:
        Matching tables
    """
    server = _get_server_instance()
    return await server.search_tables(query)


# Server instance management
_server_instance: Optional[PostgresServer] = None


def _get_server_instance() -> PostgresServer:
    """Get or create server instance."""
    global _server_instance
    
    if _server_instance is None:
        raise RuntimeError("PostgreSQL server not initialized. Call setup_server() first.")
    
    return _server_instance


async def setup_server(
    host: str = "localhost",
    port: int = 5432,
    database: str = "postgres",
    user: str = "postgres",
    password: str = "postgres",
):
    """Initialize the PostgreSQL server.
    
    Args:
        host: Database host
        port: Database port
        database: Database name
        user: Database user
        password: Database password
    """
    global _server_instance
    
    _server_instance = PostgresServer(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
    )
    await _server_instance.start()


async def teardown_server():
    """Shutdown the PostgreSQL server."""
    global _server_instance
    
    if _server_instance:
        await _server_instance.stop()
        _server_instance = None
