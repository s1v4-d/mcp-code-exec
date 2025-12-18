"""Startup initialization for MCP runtime.

This module initializes the MCP manager when the app starts.
"""

import asyncio
import logging
from pathlib import Path

from .mcp_manager import get_mcp_manager


logger = logging.getLogger("mcp_execution.startup")


async def initialize_mcp():
    """
    Initialize MCP manager on startup.
    
    This loads the configuration but doesn't connect to servers yet.
    Connections happen lazily on first tool call.
    """
    try:
        manager = get_mcp_manager()
        config_path = Path.cwd() / "mcp_config.json"
        
        if not config_path.exists():
            logger.warning(f"MCP config not found: {config_path}")
            logger.info("MCP features will be unavailable")
            return
        
        await manager.load_config(config_path)
        logger.info("MCP runtime initialized (lazy loading enabled)")
        
    except Exception as e:
        logger.error(f"MCP initialization failed: {e}")
        logger.info("App will continue without MCP features")


def init_on_startup():
    """
    Synchronous wrapper for startup initialization.
    
    Call this from FastAPI startup event.
    """
    asyncio.run(initialize_mcp())
