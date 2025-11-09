"""CLI for MCP Server Code Generation

Usage:
    python -m app.mcp_client.codegen.cli generate <server_name> <output_dir>
    python -m app.mcp_client.codegen.cli discover
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any

from app.mcp_client.client import mcp_client
from .generator import ServerModuleGenerator


async def discover_servers() -> List[str]:
    """Discover available MCP servers.
    
    Returns:
        List of server names
    """
    # This would query the MCP client for available servers
    # For POC, we'll rely on manual invocation
    print("Available servers must be manually specified.")
    print("Example: python -m app.mcp_client.codegen.cli generate filesystem ./servers")
    return []


async def generate_server_wrapper(server_name: str, output_dir: str):
    """Generate wrapper code for an MCP server.
    
    Args:
        server_name: Name of the MCP server
        output_dir: Output directory for generated code
    """
    print(f"Generating wrapper for server: {server_name}")
    print(f"Output directory: {output_dir}")
    
    # Fetch tools from MCP server
    # NOTE: This requires the server to be running and accessible
    try:
        tools = await mcp_client.list_tools(server_name)
    except Exception as e:
        print(f"Error fetching tools from server '{server_name}': {e}")
        print("\nMake sure the MCP server is running and accessible.")
        sys.exit(1)
    
    if not tools:
        print(f"No tools found for server '{server_name}'")
        sys.exit(1)
    
    print(f"Found {len(tools)} tools: {[t['name'] for t in tools]}")
    
    # Generate wrapper module
    generator = ServerModuleGenerator()
    module_path = generator.generate_server_module(
        server_name=server_name,
        tools=tools,
        output_dir=output_dir,
    )
    
    print(f"\nGenerated server module at: {module_path}")
    print(f"\nYou can now import tools:")
    print(f"  from {module_path.name} import *")


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "discover":
        asyncio.run(discover_servers())
    elif command == "generate":
        if len(sys.argv) < 4:
            print("Usage: python -m app.mcp_client.codegen.cli generate <server_name> <output_dir>")
            sys.exit(1)
        
        server_name = sys.argv[2]
        output_dir = sys.argv[3]
        asyncio.run(generate_server_wrapper(server_name, output_dir))
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
