"""Invoice MCP Server.

Provides invoice management tools via MCP protocol.
"""

import sys
import asyncio
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import existing invoice implementation
from app.mcp_client.tools.invoice_tool import InvoiceTool


logger = logging.getLogger("mcp.invoice_server")


# Initialize invoice tool
invoice_tool = InvoiceTool()


async def handle_fetch_invoices(
    start_date: str = None,
    end_date: str = None,
    category: str = None,
    min_amount: float = None,
    max_amount: float = None
):
    """Fetch invoices with filters."""
    try:
        result = await invoice_tool.fetch_invoices(
            start_date=start_date,
            end_date=end_date,
            category=category,
            min_amount=min_amount,
            max_amount=max_amount
        )
        return result
    except Exception as e:
        logger.error(f"Fetch error: {e}")
        return {"error": str(e), "invoices": []}


async def handle_update_anomaly_log(invoice_id: str, is_anomaly: bool, notes: str = None):
    """Update anomaly log for an invoice."""
    try:
        result = await invoice_tool.update_anomaly_log(
            invoice_id=invoice_id,
            is_anomaly=is_anomaly,
            notes=notes
        )
        return result
    except Exception as e:
        logger.error(f"Update error: {e}")
        return {"error": str(e)}


async def main():
    """Run the invoice MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger.info("Starting Invoice MCP Server")
    
    # Create server
    server = Server("invoice-server")
    
    # Register tools
    @server.list_tools()
    async def list_tools():
        """List available invoice tools."""
        return [
            Tool(
                name="fetch_invoices",
                description="Fetch invoices with optional filters",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Start date (YYYY-MM-DD)"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date (YYYY-MM-DD)"
                        },
                        "category": {
                            "type": "string",
                            "description": "Invoice category"
                        },
                        "min_amount": {
                            "type": "number",
                            "description": "Minimum amount"
                        },
                        "max_amount": {
                            "type": "number",
                            "description": "Maximum amount"
                        }
                    }
                }
            ),
            Tool(
                name="update_anomaly_log",
                description="Update anomaly status for an invoice",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "invoice_id": {
                            "type": "string",
                            "description": "Invoice ID"
                        },
                        "is_anomaly": {
                            "type": "boolean",
                            "description": "Is this invoice an anomaly"
                        },
                        "notes": {
                            "type": "string",
                            "description": "Notes about the anomaly"
                        }
                    },
                    "required": ["invoice_id", "is_anomaly"]
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        """Handle tool execution."""
        logger.info(f"Tool called: {name}")
        logger.debug(f"Arguments: {arguments}")
        
        result = None
        
        if name == "fetch_invoices":
            result = await handle_fetch_invoices(**arguments)
        elif name == "update_anomaly_log":
            result = await handle_update_anomaly_log(**arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        
        # Return result as text content
        import json
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    # Run server via stdio
    logger.info("Invoice server ready")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
