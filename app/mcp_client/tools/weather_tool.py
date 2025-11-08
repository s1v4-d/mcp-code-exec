"""Weather tool for MCP - OpenWeatherMap API integration."""

from typing import Dict, Any, List, Optional
import requests
import pandas as pd
from datetime import datetime, timedelta
from timezonefinder import TimezoneFinder
import pytz
from pathlib import Path


class WeatherTool:
    """
    Weather tool for MCP using OpenWeatherMap API.
    
    Provides current weather and 5-day forecast for any location
    using city name or zip code with country.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize weather tool.
        
        Args:
            api_key: OpenWeatherMap API key
        """
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org"
        
        # Load country codes CSV (we'll create a simple version)
        self.country_df = self._load_country_codes()
        self.timezone_finder = TimezoneFinder()
    
    def _load_country_codes(self) -> pd.DataFrame:
        """Load country codes for lookup."""
        # Simplified country code mapping
        country_data = {
            'name': ['UNITED STATES', 'USA', 'INDIA', 'UNITED KINGDOM', 'UK', 'CANADA', 'AUSTRALIA'],
            'alpha-2': ['US', 'US', 'IN', 'GB', 'GB', 'CA', 'AU'],
            'alpha-3': ['USA', 'USA', 'IND', 'GBR', 'GBR', 'CAN', 'AUS']
        }
        df = pd.DataFrame(country_data)
        df['name'] = df['name'].str.upper()
        return df
    
    def _get_response(self, url: str) -> Dict[str, Any]:
        """Make API request and return JSON response."""
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API Error: {response.status_code} - {response.text}")
    
    def get_geo_data(self, zip_code: Optional[str] = None, 
                     country_name: Optional[str] = None, 
                     city_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get geographical data with latitude and longitude.
        
        Args:
            zip_code: Zip/postal code
            country_name: Country name or code
            city_name: City name
            
        Returns:
            Dictionary with lat, lon, name, and country
        """
        country_code = None
        
        if country_name is not None:
            country_name_upper = country_name.upper()
            matched = self.country_df[
                (self.country_df['name'] == country_name_upper) | 
                (self.country_df['alpha-2'] == country_name_upper) | 
                (self.country_df['alpha-3'] == country_name_upper)
            ]
            if not matched.empty:
                country_code = matched['alpha-2'].iloc[0]
        
        if city_name is None and zip_code is None:
            raise ValueError("Need city name or zip code")
        
        if zip_code is not None:
            if country_code is None:
                raise ValueError("Country name required when using zip code")
            url = f"{self.base_url}/geo/1.0/zip?zip={zip_code},{country_code}&appid={self.api_key}"
            geo_data = self._get_response(url)
        elif city_name is not None:
            country_param = f",{country_code}" if country_code else ""
            url = f"{self.base_url}/geo/1.0/direct?q={city_name}{country_param}&limit=1&appid={self.api_key}"
            geo_data = self._get_response(url)
            if isinstance(geo_data, list) and len(geo_data) > 0:
                geo_data = geo_data[0]
            else:
                raise ValueError(f"City '{city_name}' not found")
        else:
            raise ValueError("Invalid parameters")
        
        return geo_data
    
    def get_local_datetime_timestamp(self, geo_data: Dict[str, Any], 
                                     days: int = 0, 
                                     hour: int = 10) -> float:
        """
        Get local datetime timestamp for a location.
        
        Args:
            geo_data: Geographic data with lat/lon
            days: Number of days in the future
            hour: Hour of the day (0-23)
            
        Returns:
            Unix timestamp for the requested time
        """
        latitude = geo_data["lat"]
        longitude = geo_data["lon"]
        
        local_timezone = self.timezone_finder.timezone_at(lng=longitude, lat=latitude)
        if local_timezone is None:
            # Fallback to UTC
            local_timezone = "UTC"
        
        local_requested_datetime = datetime.now(pytz.timezone(local_timezone)) + timedelta(days=days)
        
        if days != 0:
            local_requested_datetime = local_requested_datetime.replace(hour=hour, minute=0, second=0)
        
        return local_requested_datetime.timestamp()
    
    def get_weather(self, geo_data: Dict[str, Any], 
                    is_forecast: bool = False, 
                    local_requested_timestamp: Optional[float] = None) -> Dict[str, Any]:
        """
        Get current weather or forecast.
        
        Args:
            geo_data: Geographic data with lat/lon
            is_forecast: True for forecast, False for current weather
            local_requested_timestamp: Unix timestamp for forecast (required if is_forecast=True)
            
        Returns:
            Weather data dictionary
        """
        lat = geo_data['lat']
        lon = geo_data['lon']
        
        if not is_forecast:
            # Current weather
            url = f"{self.base_url}/data/2.5/weather?lat={lat}&lon={lon}&appid={self.api_key}&units=imperial"
            data = self._get_response(url)
            return data
        else:
            # 5-day forecast
            if local_requested_timestamp is None:
                raise ValueError("local_requested_timestamp required for forecast")
            
            url = f"{self.base_url}/data/2.5/forecast?lat={lat}&lon={lon}&appid={self.api_key}&units=imperial"
            data = self._get_response(url)
            
            # Find the closest forecast entry to the requested timestamp
            closest_entry = None
            min_diff = float('inf')
            
            for entry in data["list"]:
                diff = abs(entry["dt"] - local_requested_timestamp)
                if diff < min_diff:
                    min_diff = diff
                    closest_entry = entry
                else:
                    # Entries are sorted, so we can break once diff starts increasing
                    break
            
            return closest_entry if closest_entry else data["list"][0]
    
    def get_current_weather(self, zip_code: Optional[str] = None,
                           country_name: Optional[str] = None,
                           city_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Convenience method to get current weather.
        
        Args:
            zip_code: Zip/postal code
            country_name: Country name or code
            city_name: City name
            
        Returns:
            Current weather data
        """
        geo_data = self.get_geo_data(zip_code=zip_code, country_name=country_name, city_name=city_name)
        return self.get_weather(geo_data, is_forecast=False)
    
    def get_forecast(self, zip_code: Optional[str] = None,
                    country_name: Optional[str] = None,
                    city_name: Optional[str] = None,
                    days: int = 1,
                    hour: int = 12) -> Dict[str, Any]:
        """
        Convenience method to get weather forecast.
        
        Args:
            zip_code: Zip/postal code
            country_name: Country name or code
            city_name: City name
            days: Number of days in the future (1-5)
            hour: Hour of the day (0-23)
            
        Returns:
            Forecast weather data
        """
        if days < 1 or days > 5:
            raise ValueError("Forecast only available for 1-5 days ahead")
        
        geo_data = self.get_geo_data(zip_code=zip_code, country_name=country_name, city_name=city_name)
        timestamp = self.get_local_datetime_timestamp(geo_data, days=days, hour=hour)
        return self.get_weather(geo_data, is_forecast=True, local_requested_timestamp=timestamp)
    
    def get_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Get tool definitions for MCP registration.
        
        Returns:
            Dictionary of tool definitions
        """
        return {
            "get_geo_data": {
                "description": "Get geographical data (latitude, longitude) for a location using city name or zip code with country name",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "zip_code": {
                            "type": "string",
                            "description": "Zip/postal code"
                        },
                        "country_name": {
                            "type": "string",
                            "description": "Country name or 2-letter code (required with zip_code)"
                        },
                        "city_name": {
                            "type": "string",
                            "description": "City name"
                        }
                    }
                },
                "function": self.get_geo_data
            },
            "get_current_weather": {
                "description": "Get current weather for a location. Use city name or zip code with country.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "zip_code": {
                            "type": "string",
                            "description": "Zip/postal code"
                        },
                        "country_name": {
                            "type": "string",
                            "description": "Country name or 2-letter code"
                        },
                        "city_name": {
                            "type": "string",
                            "description": "City name"
                        }
                    }
                },
                "function": self.get_current_weather
            },
            "get_forecast": {
                "description": "Get weather forecast for 1-5 days ahead at a specific time. Returns forecast data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "zip_code": {
                            "type": "string",
                            "description": "Zip/postal code"
                        },
                        "country_name": {
                            "type": "string",
                            "description": "Country name or 2-letter code"
                        },
                        "city_name": {
                            "type": "string",
                            "description": "City name"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days ahead (1-5)",
                            "default": 1
                        },
                        "hour": {
                            "type": "integer",
                            "description": "Hour of the day (0-23)",
                            "default": 12
                        }
                    }
                },
                "function": self.get_forecast
            }
        }
