from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class GetForecastParams(BaseModel):
    """Parameters for get_forecast."""
    city: str = Field(description="City name")
    days: Optional[int] = Field(default=None, description="Number of days (1-5)")
    units: Optional[str] = Field(default=None, description="Units: metric, imperial, or standard")


async def get_forecast(params: GetForecastParams) -> Dict[str, Any]:
    """
    Get weather forecast for a city
    
    Args:
        params: Tool parameters
        
    Returns:
        Tool execution result
    """
    from app.runtime.mcp_manager import call_tool
    
    result = await call_tool(
        "weather__get_forecast",
        params.model_dump(exclude_none=True)
    )
    
    return result
