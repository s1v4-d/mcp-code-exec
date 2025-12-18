"""Postgres MCP-like server API exposed as filesystem code.

Implements progressive disclosure per docs/paper.txt:
- Tools are discoverable via files in servers/postgres_mcp/
- Agent loads only needed tool signatures and writes code to call them

Env vars used for connection:
- PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASSWORD
"""

from .query import query
from .list_tables import list_tables
from .describe_table import describe_table

__all__ = ["query", "list_tables", "describe_table"]
