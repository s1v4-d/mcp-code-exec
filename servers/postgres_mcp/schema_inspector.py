"""Schema Inspector

Provides database schema introspection capabilities.
"""

import asyncpg
from typing import List, Dict, Any


class SchemaInspector:
    """Inspects PostgreSQL database schema."""
    
    def __init__(self, pool: asyncpg.Pool):
        """Initialize inspector.
        
        Args:
            pool: asyncpg connection pool
        """
        self.pool = pool
    
    async def list_tables(self, schema: str = "public") -> List[Dict[str, str]]:
        """List all tables in a schema.
        
        Args:
            schema: Schema name
            
        Returns:
            List of table info dictionaries
        """
        query = """
            SELECT 
                table_name,
                table_type
            FROM information_schema.tables
            WHERE table_schema = $1
            ORDER BY table_name
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, schema)
            return [
                {
                    "name": row["table_name"],
                    "type": row["table_type"],
                    "schema": schema,
                }
                for row in rows
            ]
    
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
            Table schema dictionary
        """
        # Get columns
        columns_query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
        """
        
        # Get primary key
        pk_query = """
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = $1::regclass AND i.indisprimary
        """
        
        async with self.pool.acquire() as conn:
            # Get columns
            column_rows = await conn.fetch(columns_query, schema, table_name)
            columns = [
                {
                    "name": row["column_name"],
                    "type": row["data_type"],
                    "nullable": row["is_nullable"] == "YES",
                    "default": row["column_default"],
                }
                for row in column_rows
            ]
            
            # Get primary key
            pk_rows = await conn.fetch(pk_query, f"{schema}.{table_name}")
            primary_key = [row["attname"] for row in pk_rows]
            
            return {
                "table_name": table_name,
                "schema": schema,
                "columns": columns,
                "primary_key": primary_key,
            }
    
    async def search_tables(self, query: str) -> List[Dict[str, str]]:
        """Search for tables by name.
        
        Args:
            query: Search query (case-insensitive)
            
        Returns:
            List of matching tables
        """
        sql = """
            SELECT 
                table_name,
                table_type,
                table_schema
            FROM information_schema.tables
            WHERE table_name ILIKE $1
            ORDER BY table_schema, table_name
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql, f"%{query}%")
            return [
                {
                    "name": row["table_name"],
                    "type": row["table_type"],
                    "schema": row["table_schema"],
                }
                for row in rows
            ]
    
    async def get_table_row_count(
        self,
        table_name: str,
        schema: str = "public",
    ) -> int:
        """Get approximate row count for a table.
        
        Args:
            table_name: Table name
            schema: Schema name
            
        Returns:
            Approximate row count
        """
        query = f'SELECT COUNT(*) FROM "{schema}"."{table_name}"'
        
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(query)
            return result or 0
