"""RAG MCP Server.

Provides document search and management tools via MCP protocol.
"""

import sys
import asyncio
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import existing RAG implementation
from app.mcp_client.tools.rag_tool import RAGTool


logger = logging.getLogger("mcp.rag_server")


# Initialize RAG tool
rag_tool = RAGTool()


async def handle_search_documents(query: str, top_k: int = 5):
    """Search documents in RAG index."""
    try:
        result = await rag_tool.search_documents(query=query, top_k=top_k)
        return result
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {"error": str(e), "results": []}


async def handle_add_documents(documents: list):
    """Add documents to RAG index."""
    try:
        result = await rag_tool.add_documents(documents=documents)
        return result
    except Exception as e:
        logger.error(f"Add documents error: {e}")
        return {"error": str(e)}


async def handle_get_stats():
    """Get RAG index statistics."""
    try:
        result = await rag_tool.get_rag_stats()
        return result
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {"error": str(e)}


async def handle_clear_index():
    """Clear the RAG index."""
    try:
        result = await rag_tool.clear_rag_index()
        return result
    except Exception as e:
        logger.error(f"Clear error: {e}")
        return {"error": str(e)}


async def main():
    """Run the RAG MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger.info("Starting RAG MCP Server")
    
    # Create server
    server = Server("rag-server")
    
    # Register tools
    @server.list_tools()
    async def list_tools():
        """List available RAG tools."""
        return [
            Tool(
                name="search_documents",
                description="Search for documents in the RAG index",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results to return",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="add_documents",
                description="Add documents to the RAG index",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "documents": {
                            "type": "array",
                            "description": "List of documents to add",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "content": {"type": "string"},
                                    "metadata": {"type": "object"}
                                }
                            }
                        }
                    },
                    "required": ["documents"]
                }
            ),
            Tool(
                name="get_rag_stats",
                description="Get statistics about the RAG index",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="clear_rag_index",
                description="Clear all documents from the RAG index",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        """Handle tool execution."""
        logger.info(f"Tool called: {name}")
        logger.debug(f"Arguments: {arguments}")
        
        result = None
        
        if name == "search_documents":
            result = await handle_search_documents(**arguments)
        elif name == "add_documents":
            result = await handle_add_documents(**arguments)
        elif name == "get_rag_stats":
            result = await handle_get_stats()
        elif name == "clear_rag_index":
            result = await handle_clear_index()
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        
        # Return result as text content
        import json
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    # Run server via stdio
    logger.info("RAG server ready")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
