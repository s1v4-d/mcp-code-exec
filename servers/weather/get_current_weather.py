from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class GetCurrentWeatherParams(BaseModel):
    """Parameters for get_current_weather."""
    city: str = Field(description="City name")
    units: Optional[str] = Field(default=None, description="Units: metric, imperial, or standard")


async def get_current_weather(params: GetCurrentWeatherParams) -> Dict[str, Any]:
    """
    Get current weather conditions for a city
    
    Args:
        params: Tool parameters
        
    Returns:
        Tool execution result
    """
    from app.runtime.mcp_manager import call_tool
    
    result = await call_tool(
        "weather__get_current_weather",
        params.model_dump(exclude_none=True)
    )
    
    return result
