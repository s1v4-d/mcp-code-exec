"""
Weather MCP Server

Provides weather data access via OpenWeatherMap API.
Tools for current weather, forecasts, and geographic data.
"""

from typing import Dict, Any, Optional

# Re-export tool functions
from .get_current_weather import get_current_weather
from .get_forecast import get_forecast
from .get_geo_data import get_geo_data

__all__ = [
    "get_current_weather",
    "get_forecast", 
    "get_geo_data",
]
