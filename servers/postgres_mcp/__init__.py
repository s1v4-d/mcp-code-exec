"""PostgreSQL MCP Server

Provides safe database access through MCP tools.
"""

from .server import (
    PostgresServer,
    execute_query,
    list_tables,
    get_table_schema,
    search_tables,
    setup_server,
    teardown_server,
)

__all__ = [
    'PostgresServer',
    'execute_query',
    'list_tables',
    'get_table_schema',
    'search_tables',
    'setup_server',
    'teardown_server',
]
