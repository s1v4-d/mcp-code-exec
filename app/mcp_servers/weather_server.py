"""Weather MCP Server.

Provides weather-related tools via MCP protocol.
"""

import sys
import asyncio
import logging
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import existing weather implementation
from app.mcp_client.tools.weather_tool import WeatherTool
from app.config import settings


logger = logging.getLogger("mcp.weather_server")


# Initialize weather tool
weather_tool = None

try:
    if settings.open_weather_api_key:
        weather_tool = WeatherTool(api_key=settings.open_weather_api_key)
        logger.info("Weather tool initialized")
    else:
        logger.warning("No weather API key - server will have no tools")
except Exception as e:
    logger.error(f"Failed to initialize weather tool: {e}")


async def handle_get_current_weather(city: str, units: Optional[str] = "metric"):
    """Get current weather for a city."""
    if not weather_tool:
        return {"error": "Weather API not configured"}
    
    try:
        # WeatherTool uses city_name parameter, not city
        result = await weather_tool.get_current_weather(city_name=city)
        return result
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return {"error": str(e)}


async def handle_get_forecast(city: str, days: Optional[int] = 5, units: Optional[str] = "metric"):
    """Get weather forecast for a city."""
    if not weather_tool:
        return {"error": "Weather API not configured"}
    
    try:
        # WeatherTool uses city_name parameter, not city
        result = await weather_tool.get_forecast(city_name=city, days=days)
        return result
    except Exception as e:
        logger.error(f"Forecast API error: {e}")
        return {"error": str(e)}


async def handle_get_geo_data(location: str):
    """Get geographic data for a location."""
    if not weather_tool:
        return {"error": "Weather API not configured"}
    
    try:
        result = weather_tool.get_geo_data(location=location)
        return result
    except Exception as e:
        logger.error(f"Geo data error: {e}")
        return {"error": str(e)}


async def main():
    """Run the weather MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger.info("Starting Weather MCP Server")
    
    # Create server
    server = Server("weather-server")
    
    # Register tools
    @server.list_tools()
    async def list_tools():
        """List available weather tools."""
        tools = []
        
        if weather_tool:
            tools = [
                Tool(
                    name="get_current_weather",
                    description="Get current weather conditions for a city",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "City name"
                            },
                            "units": {
                                "type": "string",
                                "description": "Units: metric, imperial, or standard",
                                "default": "metric"
                            }
                        },
                        "required": ["city"]
                    }
                ),
                Tool(
                    name="get_forecast",
                    description="Get weather forecast for a city",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "City name"
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days (1-5)",
                                "default": 5
                            },
                            "units": {
                                "type": "string",
                                "description": "Units: metric, imperial, or standard",
                                "default": "metric"
                            }
                        },
                        "required": ["city"]
                    }
                ),
                Tool(
                    name="get_geo_data",
                    description="Get geographic coordinates and timezone for a location",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "Location name"
                            }
                        },
                        "required": ["location"]
                    }
                )
            ]
        
        return tools
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        """Handle tool execution."""
        logger.info(f"Tool called: {name}")
        logger.debug(f"Arguments: {arguments}")
        
        result = None
        
        if name == "get_current_weather":
            result = await handle_get_current_weather(**arguments)
        elif name == "get_forecast":
            result = await handle_get_forecast(**arguments)
        elif name == "get_geo_data":
            result = await handle_get_geo_data(**arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        
        # Return result as text content
        import json
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    # Run server via stdio
    logger.info("Weather server ready")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
