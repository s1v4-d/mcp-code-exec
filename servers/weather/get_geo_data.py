"""
Get geographic data (latitude/longitude) for a location.

Tool: get_geo_data
Description: Retrieves geographic coordinates for a city or zip code.
"""

from typing import Dict, Any, Optional
from servers.client import mcp_client


async def get_geo_data(
    city_name: Optional[str] = None,
    zip_code: Optional[str] = None,
    country_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get geographic coordinates for a location.
    
    Useful for determining latitude/longitude before making
    other weather API calls or for mapping purposes.
    
    Args:
        city_name: City name
        zip_code: Zip/postal code
        country_name: Country name or 2-letter code
            Required when using zip_code
    
    Returns:
        Geographic data dictionary with structure:
        {
            "name": str,        # Location name
            "lat": float,       # Latitude
            "lon": float,       # Longitude
            "country": str,     # Country code
            "state": str        # State/region (if available)
        }
    
    Example:
        >>> # Get coordinates for a city
        >>> geo = await get_geo_data(city_name="Sydney", country_name="Australia")
        >>> print(f"Coordinates: {geo['lat']}, {geo['lon']}")
        
        >>> # Get coordinates by zip code
        >>> geo = await get_geo_data(zip_code="90210", country_name="US")
        >>> print(f"Location: {geo['name']}")
    
    Raises:
        ValueError: If neither city_name nor zip_code provided
    """
    return await mcp_client.call_tool("get_geo_data", {
        "city_name": city_name,
        "zip_code": zip_code,
        "country_name": country_name
    })
