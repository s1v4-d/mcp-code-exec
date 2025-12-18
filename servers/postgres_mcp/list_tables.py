"""List tables in the current PostgreSQL database schema(s)."""

import asyncio
from typing import List, Dict, Any
from ._conn import get_pool, redacted_dsn


async def list_tables(schemas: List[str] | None = None) -> Dict[str, Any]:
    """Return tables grouped by schema.

    Args:
        schemas: Optional list of schemas to include; defaults to ['public']
    Returns:
        Dict with connection info and tables per schema
    """
    schemas = schemas or ["public"]
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type='BASE TABLE' AND table_schema = ANY($1::text[])
            ORDER BY table_schema, table_name
            """,
            schemas,
        )
    await pool.close()
    grouped: Dict[str, List[str]] = {}
    for r in rows:
        grouped.setdefault(r["table_schema"], []).append(r["table_name"])
    return {"dsn": redacted_dsn(), "tables": grouped}


def list_tables_sync(schemas: List[str] | None = None) -> Dict[str, Any]:
    return asyncio.run(list_tables(schemas))
