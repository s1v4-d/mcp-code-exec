"""
Get weather forecast for a location.

Tool: get_forecast
Description: Retrieves weather forecast for 1-5 days ahead at a specific hour.
"""

from typing import Dict, Any, Optional
from servers.client import mcp_client


def get_forecast(
    city_name: Optional[str] = None,
    zip_code: Optional[str] = None,
    country_name: Optional[str] = None,
    days: int = 1,
    hour: int = 12
) -> Dict[str, Any]:
    """
    Get weather forecast for a location.
    
    Retrieves forecast for a specific day (1-5 days ahead) and hour.
    Uses local timezone for the location.
    
    Args:
        city_name: City name (e.g., "Paris", "New York")
        zip_code: Zip/postal code
        country_name: Country name or 2-letter code
            Required when using zip_code, optional for city_name
        days: Number of days ahead (1-5), default 1
        hour: Hour of the day (0-23), default 12 (noon)
    
    Returns:
        Forecast data dictionary with structure:
        {
            "dt": int,              # Forecast timestamp
            "main": {
                "temp": float,      # Temperature in Fahrenheit
                "feels_like": float,
                "temp_min": float,
                "temp_max": float,
                "pressure": int,
                "humidity": int
            },
            "weather": [{"id": int, "main": str, "description": str, "icon": str}],
            "clouds": {"all": int},
            "wind": {"speed": float, "deg": int},
            "pop": float,           # Probability of precipitation (0-1)
            "dt_txt": str          # Forecast time as text
        }
    
    Example:
        >>> # Get forecast for tomorrow at 2 PM
        >>> forecast = get_forecast(
        ...     city_name="London",
        ...     country_name="UK",
        ...     days=1,
        ...     hour=14
        ... )
        >>> print(f"Temperature: {forecast['main']['temp']}°F")
        >>> print(f"Conditions: {forecast['weather'][0]['description']}")
        
        >>> # Get forecast for 3 days ahead
        >>> forecast = get_forecast(city_name="Tokyo", days=3, hour=10)
    
    Raises:
        ValueError: If days not in range 1-5, or if required parameters missing
    """
    return mcp_client.call_tool("get_forecast", {
        "city_name": city_name,
        "zip_code": zip_code,
        "country_name": country_name,
        "days": days,
        "hour": hour
    })
