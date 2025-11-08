"""Weather API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from app.mcp_client.tools.weather_tool import WeatherTool
from app.config import settings

router = APIRouter()

# Initialize weather tool
weather_tool = WeatherTool(api_key=settings.open_weather_api_key)


class WeatherRequest(BaseModel):
    """Request for weather data."""
    city_name: Optional[str] = Field(None, description="City name")
    zip_code: Optional[str] = Field(None, description="Zip/postal code")
    country_name: Optional[str] = Field(None, description="Country name or code (required with zip_code)")


class ForecastRequest(WeatherRequest):
    """Request for weather forecast."""
    days: int = Field(default=1, description="Number of days ahead (1-5)", ge=1, le=5)
    hour: int = Field(default=12, description="Hour of the day (0-23)", ge=0, le=23)


class WeatherResponse(BaseModel):
    """Weather response."""
    status: str
    location: str
    data: Dict[str, Any]


@router.post("/current", response_model=WeatherResponse)
async def get_current_weather(request: WeatherRequest) -> WeatherResponse:
    """
    Get current weather for a location.
    
    Provide either city_name or zip_code with country_name.
    """
    try:
        if not request.city_name and not request.zip_code:
            raise HTTPException(
                status_code=400,
                detail="Must provide either city_name or zip_code"
            )
        
        if request.zip_code and not request.country_name:
            raise HTTPException(
                status_code=400,
                detail="country_name required when using zip_code"
            )
        
        weather_data = weather_tool.get_current_weather(
            city_name=request.city_name,
            zip_code=request.zip_code,
            country_name=request.country_name
        )
        
        location = request.city_name or f"{request.zip_code}, {request.country_name}"
        
        return WeatherResponse(
            status="success",
            location=location,
            data=weather_data
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forecast", response_model=WeatherResponse)
async def get_weather_forecast(request: ForecastRequest) -> WeatherResponse:
    """
    Get weather forecast for a location.
    
    Forecast available for 1-5 days ahead.
    """
    try:
        if not request.city_name and not request.zip_code:
            raise HTTPException(
                status_code=400,
                detail="Must provide either city_name or zip_code"
            )
        
        if request.zip_code and not request.country_name:
            raise HTTPException(
                status_code=400,
                detail="country_name required when using zip_code"
            )
        
        forecast_data = weather_tool.get_forecast(
            city_name=request.city_name,
            zip_code=request.zip_code,
            country_name=request.country_name,
            days=request.days,
            hour=request.hour
        )
        
        location = request.city_name or f"{request.zip_code}, {request.country_name}"
        
        return WeatherResponse(
            status="success",
            location=f"{location} ({request.days} days ahead at {request.hour}:00)",
            data=forecast_data
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/geo/{location}")
async def get_geo_data(location: str, country: Optional[str] = None):
    """
    Get geographical data (lat/lon) for a location.
    
    Args:
        location: City name or zip code
        country: Country name or code (optional, but recommended)
    """
    try:
        # Try as city name first
        try:
            geo_data = weather_tool.get_geo_data(
                city_name=location,
                country_name=country
            )
        except:
            # Try as zip code
            if country:
                geo_data = weather_tool.get_geo_data(
                    zip_code=location,
                    country_name=country
                )
            else:
                raise ValueError("Country required for zip code lookup")
        
        return {
            "status": "success",
            "location": location,
            "data": geo_data
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
