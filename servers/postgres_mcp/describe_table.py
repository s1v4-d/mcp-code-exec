"""Describe columns of a given table."""

import asyncio
from typing import Dict, Any
from ._conn import get_pool, redacted_dsn


async def describe_table(schema: str, table: str) -> Dict[str, Any]:
    """Return column names and types for a table."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema=$1 AND table_name=$2
            ORDER BY ordinal_position
            """,
            schema,
            table,
        )
    await pool.close()
    cols = [
        {"name": r["column_name"], "type": r["data_type"], "nullable": r["is_nullable"]}
        for r in rows
    ]
    return {"dsn": redacted_dsn(), "schema": schema, "table": table, "columns": cols}


def describe_table_sync(schema: str, table: str) -> Dict[str, Any]:
    return asyncio.run(describe_table(schema, table))
