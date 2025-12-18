"""PostgreSQL MCP Server.

Wraps the postgres-mcp package to provide PostgreSQL database access via MCP.
This server provides:
- Schema inspection
- Query execution with safety features
- Explain plan analysis
- Index tuning recommendations
- Database health checks
- Top queries analysis

Based on crystaldba/postgres-mcp.
"""

import sys
import logging
import os

# Import the server module directly instead of the main function
# This avoids the asyncio.run() conflict
from postgres_mcp import server


logger = logging.getLogger("mcp.postgres_server")


if __name__ == "__main__":
    """Run the PostgreSQL MCP server.
    
    This directly calls the postgres-mcp server's main() function.
    The server expects DATABASE_URI environment variable to be set.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger.info("Starting PostgreSQL MCP Server (postgres-mcp)")
    
    # Check for DATABASE_URI in environment
    if not os.environ.get("DATABASE_URI"):
        logger.error("DATABASE_URI environment variable not set")
        sys.exit(1)
    
    # Call the server module's main() which properly handles asyncio
    try:
        # Import and run asyncio
        import asyncio
        asyncio.run(server.main())
    except Exception as e:
        logger.error(f"PostgreSQL MCP server error: {e}", exc_info=True)
        sys.exit(1)
