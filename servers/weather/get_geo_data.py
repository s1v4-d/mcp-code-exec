from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class GetGeoDataParams(BaseModel):
    """Parameters for get_geo_data."""
    location: str = Field(description="Location name")


async def get_geo_data(params: GetGeoDataParams) -> Dict[str, Any]:
    """
    Get geographic coordinates and timezone for a location
    
    Args:
        params: Tool parameters
        
    Returns:
        Tool execution result
    """
    from app.runtime.mcp_manager import call_tool
    
    result = await call_tool(
        "weather__get_geo_data",
        params.model_dump(exclude_none=True)
    )
    
    return result
