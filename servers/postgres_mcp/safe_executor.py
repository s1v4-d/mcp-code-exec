"""Safe Query Executor

Validates and executes SQL queries with safety checks.
Implements query classification and constraint enforcement.
"""

import re
import asyncpg
from typing import List, Dict, Any, Optional
import sqlparse
from sqlparse.sql import Token, TokenList
from sqlparse.tokens import Keyword, DML


class QueryValidationError(Exception):
    """Raised when query validation fails."""
    pass


class SafeQueryExecutor:
    """Executes SQL queries with safety validation."""
    
    # Dangerous SQL patterns (blocked)
    DANGEROUS_PATTERNS = [
        r'\bDROP\s+DATABASE\b',
        r'\bDROP\s+SCHEMA\b',
        r'\bTRUNCATE\s+TABLE\b',
        r'\bGRANT\b',
        r'\bREVOKE\b',
        r'\bALTER\s+USER\b',
        r'\bCREATE\s+USER\b',
        r'\bDROP\s+USER\b',
        r'\bSET\s+ROLE\b',
        r';\s*DROP\b',  # SQL injection attempt
        r'--.*DROP\b',  # SQL injection in comment
    ]
    
    def __init__(self, pool: asyncpg.Pool):
        """Initialize executor.
        
        Args:
            pool: asyncpg connection pool
        """
        self.pool = pool
    
    async def execute(
        self,
        query: str,
        params: List[Any],
        read_only: bool = True,
    ) -> Dict[str, Any]:
        """Execute a SQL query safely.
        
        Args:
            query: SQL query to execute
            params: Query parameters for parameterization
            read_only: If True, only allow SELECT queries
            
        Returns:
            Dictionary with:
                - rows: List of result rows (as dicts)
                - row_count: Number of rows returned/affected
                - query_type: Type of query (SELECT, INSERT, etc.)
                
        Raises:
            QueryValidationError: If query validation fails
        """
        # Validate query
        self._validate_query(query, read_only)
        
        # Parse query to determine type
        query_type = self._get_query_type(query)
        
        # Execute query
        async with self.pool.acquire() as conn:
            try:
                if query_type == "SELECT":
                    # Fetch query
                    rows = await conn.fetch(query, *params)
                    return {
                        "rows": [dict(row) for row in rows],
                        "row_count": len(rows),
                        "query_type": query_type,
                    }
                else:
                    # Mutation query (INSERT, UPDATE, DELETE)
                    result = await conn.execute(query, *params)
                    
                    # Extract row count from result string
                    # Result format: "INSERT 0 5" or "UPDATE 3" or "DELETE 2"
                    row_count = self._extract_row_count(result)
                    
                    return {
                        "rows": [],
                        "row_count": row_count,
                        "query_type": query_type,
                    }
                    
            except asyncpg.PostgresError as e:
                raise QueryValidationError(f"Query execution failed: {str(e)}")
    
    def _validate_query(self, query: str, read_only: bool):
        """Validate query for safety.
        
        Args:
            query: SQL query
            read_only: If True, only allow SELECT
            
        Raises:
            QueryValidationError: If query is unsafe
        """
        # Check for dangerous patterns
        query_upper = query.upper()
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, query_upper, re.IGNORECASE):
                raise QueryValidationError(
                    f"Dangerous SQL pattern detected: {pattern}"
                )
        
        # Check read-only constraint
        if read_only:
            query_type = self._get_query_type(query)
            if query_type != "SELECT":
                raise QueryValidationError(
                    f"Only SELECT queries allowed in read-only mode. Got: {query_type}"
                )
        
        # Parse query for additional validation
        try:
            parsed = sqlparse.parse(query)
            if not parsed:
                raise QueryValidationError("Empty or invalid SQL query")
        except Exception as e:
            raise QueryValidationError(f"Query parsing failed: {str(e)}")
    
    def _get_query_type(self, query: str) -> str:
        """Determine query type (SELECT, INSERT, UPDATE, DELETE, etc.).
        
        Args:
            query: SQL query
            
        Returns:
            Query type as string
        """
        parsed = sqlparse.parse(query)[0]
        
        # Find first DML keyword
        for token in parsed.tokens:
            if token.ttype is DML:
                return token.value.upper()
        
        # Check for DDL/other keywords
        query_upper = query.strip().upper()
        if query_upper.startswith("CREATE"):
            return "CREATE"
        elif query_upper.startswith("ALTER"):
            return "ALTER"
        elif query_upper.startswith("DROP"):
            return "DROP"
        
        # Default to SELECT
        return "SELECT"
    
    def _extract_row_count(self, result: str) -> int:
        """Extract row count from query result string.
        
        Args:
            result: Result string from asyncpg (e.g., "INSERT 0 5")
            
        Returns:
            Number of affected rows
        """
        # Result format: "COMMAND [oid] count"
        parts = result.split()
        if len(parts) >= 2:
            try:
                return int(parts[-1])
            except ValueError:
                pass
        
        return 0
