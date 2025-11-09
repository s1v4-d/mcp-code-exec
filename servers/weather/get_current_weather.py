"""
Get current weather for a location.

Tool: get_current_weather
Description: Retrieves current weather conditions for a city or zip code.
"""

from typing import Dict, Any, Optional
from servers.client import mcp_client


async def get_current_weather(
    city_name: Optional[str] = None,
    zip_code: Optional[str] = None,
    country_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get current weather for a location.
    
    Provide either city_name OR zip_code (with country_name).
    
    Args:
        city_name: City name (e.g., "Tokyo", "London")
        zip_code: Zip/postal code
        country_name: Country name or 2-letter code (e.g., "Japan", "JP", "United Kingdom", "UK")
            Required when using zip_code, optional for city_name
    
    Returns:
        Weather data dictionary with structure:
        {
            "coord": {"lon": float, "lat": float},
            "weather": [{"id": int, "main": str, "description": str, "icon": str}],
            "main": {
                "temp": float,      # Temperature in Fahrenheit
                "feels_like": float,
                "temp_min": float,
                "temp_max": float,
                "pressure": int,    # hPa
                "humidity": int     # Percentage
            },
            "wind": {"speed": float, "deg": int},
            "clouds": {"all": int},
            "dt": int,              # Timestamp
            "sys": {"country": str, "sunrise": int, "sunset": int},
            "name": str             # City name
        }
    
    Example:
        >>> # Get weather for a city
        >>> weather = await get_current_weather(city_name="Tokyo", country_name="Japan")
        >>> print(f"Temperature: {weather['main']['temp']}°F")
        >>> print(f"Conditions: {weather['weather'][0]['description']}")
        
        >>> # Get weather by zip code
        >>> weather = await get_current_weather(zip_code="10001", country_name="US")
    
    Raises:
        ValueError: If neither city_name nor zip_code provided, or if country_name
                   missing when using zip_code
    """
    return await mcp_client.call_tool("get_current_weather", {
        "city_name": city_name,
        "zip_code": zip_code,
        "country_name": country_name
    })
