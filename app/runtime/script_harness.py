"""
Script execution harness for MCP-enabled Python scripts.

This harness provides the main entry point for executing scripts with MCP tools.

Features:
- Persistent event loop for MCP async operations
- SIGINT/SIGTERM signal handling for graceful shutdown
- MCP client manager initialization
- Automatic cleanup on exit

Usage:
    python -m app.runtime.script_harness <script_path>
"""

import asyncio
import logging
import runpy
import signal
import sys
from pathlib import Path
from typing import Any, NoReturn

from app.runtime.mcp_manager import get_mcp_manager

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    stream=sys.stderr
)

logger = logging.getLogger("mcp_execution.script_harness")


def main() -> NoReturn:
    """Entry point for the script harness.
    
    This harness:
    1. Validates script path
    2. Creates persistent event loop
    3. Initializes MCP client manager
    4. Registers signal handlers (SIGINT/SIGTERM)
    5. Executes user script
    6. Cleans up connections on exit
    """
    # 1. Parse CLI arguments
    if len(sys.argv) < 2:
        logger.error("Usage: python -m app.runtime.script_harness <script_path>")
        sys.exit(1)

    script_path = Path(sys.argv[1]).resolve()

    # 2. Validate script exists
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        sys.exit(1)

    if not script_path.is_file():
        logger.error(f"Not a file: {script_path}")
        sys.exit(1)

    logger.info(f"Script: {script_path}")

    # 3. Add project root to Python path for imports
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        logger.debug(f"Added to sys.path: {project_root}")

    # Add servers/ directory for progressive disclosure
    servers_path = project_root / "servers"
    if servers_path.exists() and str(servers_path) not in sys.path:
        sys.path.insert(0, str(servers_path))
        logger.debug(f"Added servers to sys.path: {servers_path}")

    # 4. Create a persistent event loop
    # This ensures async context managers are entered and exited in the same loop
    # Critical for proper MCP connection lifecycle
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    logger.debug("Created persistent event loop")

    # 5. Initialize MCP client manager
    manager = get_mcp_manager()
    try:
        loop.run_until_complete(manager.load_config())
        logger.info("MCP client manager initialized (lazy loading)")
    except Exception as e:
        logger.error(f"Failed to initialize MCP client: {e}")
        loop.close()
        sys.exit(1)

    # 6. Set up signal handling for graceful shutdown
    def signal_handler(signum: int, frame: Any) -> None:
        """Handle shutdown signals (SIGINT/SIGTERM).
        
        This ensures graceful shutdown when user presses Ctrl+C
        or when the process receives a termination signal.
        """
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name}, shutting down gracefully...")
        sys.exit(130)  # Standard exit code for signal termination

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    logger.debug("Signal handlers registered (SIGINT, SIGTERM)")

    # 7. Execute the script
    exit_code = 0
    try:
        logger.info(f"Executing script: {script_path}")
        runpy.run_path(str(script_path), run_name="__main__")
        logger.info("Script execution completed successfully")

    except KeyboardInterrupt:
        logger.info("Execution interrupted by user (KeyboardInterrupt)")
        exit_code = 130

    except Exception as e:
        logger.error(f"Script execution failed: {e}", exc_info=True)
        exit_code = 1

    finally:
        # 8. Cleanup - ALWAYS runs, even on exception
        logger.debug("Cleaning up MCP connections...")
        try:
            # Run cleanup using the same event loop
            # Suppress BaseExceptionGroup from async generator cleanup
            loop.run_until_complete(manager.shutdown())
            logger.info("MCP cleanup complete")
        except BaseException as e:
            # Suppress BaseExceptionGroup from async generators (harmless in cleanup)
            if type(e).__name__ == "BaseExceptionGroup":
                logger.debug("Suppressed BaseExceptionGroup during cleanup")
            else:
                logger.error(f"Cleanup failed: {e}", exc_info=True)
                if exit_code == 0:
                    exit_code = 1
        finally:
            # 9. Close the event loop
            loop.close()
            logger.debug("Event loop closed")

        # 10. Exit with appropriate code
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
