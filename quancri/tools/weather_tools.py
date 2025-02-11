import asyncio
from typing import Optional, Dict, Any, List

import math

from quancri.models.tool_model import ToolCategory
from quancri.tools.tool import Tool


class WeatherTool(Tool):
    """A tool for fetching weather data and forecasts.

    This tool provides:
    1. Current weather conditions
    2. Hourly forecasts
    3. Daily forecasts
    4. Historical weather data
    5. Weather alerts and warnings

    Weather data includes:
    - Temperature (°C and °F)
    - Humidity
    - Wind speed and direction
    - Precipitation probability
    - Weather conditions (sunny, rainy, etc.)
    """

    name = "Weather Tool"
    description = "Fetches weather data including current conditions, forecasts, and historical data"
    category = ToolCategory.WEATHER

    async def execute(self,
                      location: str,
                      forecast_days: Optional[int] = None,
                      hourly: bool = False,
                      include_alerts: bool = False,
                      date: Optional[str] = None) -> Dict[str, Any]:
        """Fetch weather data for a specific location.

        Args:
        location: City name or coordinates (e.g., 'New York' or '40.7128,-74.0060')
        forecast_days: Number of days for forecast (1-7)
        hourly: Whether to include hourly forecast
        include_alerts: Whether to include weather alerts
        date: Specific date for historical data (YYYY-MM-DD)

        Returns:
        Dict[str, Any]: Weather data including:
            - current: Current weather conditions
            - forecast: Daily or hourly forecast if requested
            - alerts: Weather alerts if requested
            - history: Historical data if date is provided

        Examples:
            # Get current weather
            >>> await execute(location="New York")
            {
                "current": {
                    "temperature": 22,
                    "temperature_fahrenheit": 71.6,
                    "humidity": 65,
                    "wind_speed": 10,
                    "wind_direction": "NE",
                    "condition": "Partly Cloudy"
                }
            }

            # Get 3-day forecast
            >>> await execute(location="New York", forecast_days=3)
            {
                "current": {...},
                "forecast": [
                    {
                        "date": "2025-02-01",
                        "temperature_high": 24,
                        "temperature_low": 18,
                        "condition": "Sunny"
                    },
                    ...
                ]
            },
            # Get weather for past 5 days
            >>> await execute(location="New York", date="2025-02-01")
            {
                "current": {...},
                "history": [
                    {
                        "date": "2025-02-01",
                        "temperature_high": 24,
                        "temperature_low": 18,
                        "condition": "Sunny"
                    },
                    {
                        "date": "2025-01-31",
                        "temperature_high": 22,
                        "temperature_low": 10,
                        "condition": "Cloudy"
                    },
                    ...
                ]
            }
        """
        await asyncio.sleep(0.1)  # Simulate API delay

        # Mock implementation - in production, you would call a real weather API
        response = {
            "current": self._generate_current_weather(location)
        }

        if forecast_days:
            response["forecast"] = self._generate_forecast(
                location,
                forecast_days,
                hourly
            )

        if include_alerts:
            response["alerts"] = self._generate_alerts(location)

        if date:
            response["history"] = self._generate_historical_weather(
                location,
                date
            )

        return response

    def _generate_current_weather(self, location: str) -> Dict[str, Any]:
        """Generate mock current weather data"""
        # Use hash of location to generate consistent but varying data
        base = abs(hash(location)) % 100

        conditions = [
            "Sunny", "Partly Cloudy", "Cloudy",
            "Light Rain", "Heavy Rain", "Thunderstorm"
        ]

        temp_c = 20 + (base % 15)  # Temperature between 20-35°C
        return {
            "temperature": temp_c,
            "temperature_fahrenheit": round((temp_c * 9 / 5) + 32, 1),
            "humidity": 50 + (base % 30),  # Humidity between 50-80%
            "wind_speed": 5 + (base % 20),  # Wind speed between 5-25 km/h
            "wind_direction": ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][base % 8],
            "condition": conditions[base % len(conditions)]
        }

    def _generate_forecast(self,
                           location: str,
                           days: int,
                           hourly: bool) -> List[Dict[str, Any]]:
        """Generate mock forecast data"""
        forecast = []
        base_temp = abs(hash(location)) % 10 + 20  # Base temperature 20-30°C

        if hourly:
            # Generate hourly forecast for the requested days
            for day in range(days):
                for hour in range(24):
                    temp_variation = math.sin(hour * math.pi / 12) * 5
                    forecast.append({
                        "timestamp": f"2025-02-{day + 1:02d} {hour:02d}:00",
                        "temperature": round(base_temp + temp_variation, 1),
                        "precipitation_chance": abs(hash(f"{location}{day}{hour}")) % 100
                    })
        else:
            # Generate daily forecast
            for day in range(days):
                daily_variation = (hash(f"{location}{day}") % 10) - 5
                forecast.append({
                    "date": f"2025-02-{day + 1:02d}",
                    "temperature_high": round(base_temp + 5 + daily_variation, 1),
                    "temperature_low": round(base_temp - 5 + daily_variation, 1),
                    "precipitation_chance": abs(hash(f"{location}{day}")) % 100
                })

        return forecast

    def _generate_alerts(self, location: str) -> List[Dict[str, str]]:
        """Generate mock weather alerts"""
        # Only generate alerts sometimes based on location hash
        if abs(hash(location)) % 4 == 0:
            return [{
                "type": "Weather Advisory",
                "severity": "Moderate",
                "message": "Strong winds expected in the afternoon"
            }]
        return []

    def _generate_historical_weather(self,
                                     location: str,
                                     date: str) -> Dict[str, Any]:
        """Generate mock historical weather data"""
        base = abs(hash(f"{location}{date}")) % 100
        return {
            "temperature_high": 25 + (base % 10),
            "temperature_low": 15 + (base % 8),
            "precipitation": (base % 20) / 10,  # 0-2 inches
            "wind_speed": 5 + (base % 15)
        }
