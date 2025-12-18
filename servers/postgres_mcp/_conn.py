import os
import asyncpg
from typing import Optional


async def get_pool(min_size: int = 1, max_size: int = 5) -> asyncpg.Pool:
    """Create (or return) a connection pool using env vars.

    Env:
      PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASSWORD
    """
    host = os.getenv("PG_HOST", "localhost")
    port = int(os.getenv("PG_PORT", "5432"))
    database = os.getenv("PG_DB", "postgres")
    user = os.getenv("PG_USER", "postgres")
    password = os.getenv("PG_PASSWORD", "")
    return await asyncpg.create_pool(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        min_size=min_size,
        max_size=max_size,
    )


def redacted_dsn() -> str:
    host = os.getenv("PG_HOST", "localhost")
    port = os.getenv("PG_PORT", "5432")
    database = os.getenv("PG_DB", "postgres")
    user = os.getenv("PG_USER", "postgres")
    return f"postgres://{user}:***@{host}:{port}/{database}"
