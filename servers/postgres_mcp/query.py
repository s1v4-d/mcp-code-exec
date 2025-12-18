"""Run a safe SELECT query with optional row limit."""

import asyncio
from typing import Dict, Any, List
import sqlparse
from ._conn import get_pool, redacted_dsn


def _is_safe_select(sql: str) -> bool:
    parsed = sqlparse.parse(sql)
    if not parsed:
        return False
    stmt = parsed[0]
    return stmt.get_type() == "SELECT"


async def query(sql: str, limit: int = 100) -> Dict[str, Any]:
    """Execute a SELECT query with row limit.

    Args:
        sql: SQL SELECT statement
        limit: Max rows to return (default 100)
    Returns:
        Dict with columns and rows
    """
    if not _is_safe_select(sql):
        raise ValueError("Only SELECT queries are allowed.")
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(f"{sql} LIMIT {int(limit)}")
    await pool.close()
    # Convert to plain structures
    result_rows: List[Dict[str, Any]] = [dict(r) for r in rows]
    columns = list(result_rows[0].keys()) if result_rows else []
    return {"dsn": redacted_dsn(), "columns": columns, "rows": result_rows, "row_count": len(result_rows)}


def query_sync(sql: str, limit: int = 100) -> Dict[str, Any]:
    return asyncio.run(query(sql, limit))
