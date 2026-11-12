"""
Desktop Open-Meteo API Client for SkyCast.
Handles city geocoding, reverse geocoding, and weather forecast queries.
"""

import requests
from typing import Dict, Any, List, Optional, Callable
import threading

class WeatherApiClient:
    BASE_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
    BASE_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
    BASE_REVERSE_GEO_URL = "https://api.bigdatacloud.net/data/reverse-geocode-client"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def search_cities(self, query: str) -> List[Dict[str, Any]]:
        """Search cities by name using Open-Meteo Geocoding API."""
        if not query or len(query.strip()) < 2:
            return []
        params = {
            "name": query.strip(),
            "count": 5,
            "language": "en",
            "format": "json"
        }
        try:
            resp = requests.get(self.BASE_GEOCODE_URL, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            formatted = []
            for r in results:
                name = r.get("name")
                country = r.get("country", "")
                admin1 = r.get("admin1", "")
                location_str = f"{name}, {admin1}, {country}" if admin1 else f"{name}, {country}"
                formatted.append({
                    "name": name,
                    "display_name": location_str,
                    "country": country,
                    "latitude": r.get("latitude"),
                    "longitude": r.get("longitude"),
                    "timezone": r.get("timezone", "auto")
                })
            return formatted
        except Exception as e:
            print(f"Geocoding error: {e}")
            return []

    def get_weather(self, lat: float, lon: float, is_fahrenheit: bool = False) -> Optional[Dict[str, Any]]:
        """Fetch current weather, hourly forecast, and 7-day forecast."""
        unit_temp = "fahrenheit" if is_fahrenheit else "celsius"
        unit_wind = "mph" if is_fahrenheit else "kmh"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,surface_pressure,wind_speed_10m,wind_direction_10m",
            "hourly": "temperature_2m,weather_code,is_day",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_probability_max",
            "timezone": "auto",
            "temperature_unit": unit_temp,
            "wind_speed_unit": unit_wind,
            "forecast_days": 7
        }
        try:
            resp = requests.get(self.BASE_WEATHER_URL, params=params, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Weather fetch error: {e}")
            return None

    def fetch_weather_async(self, lat: float, lon: float, is_fahrenheit: bool,
                            on_success: Callable[[Dict[str, Any]], None],
                            on_error: Callable[[str], None]):
        """Runs get_weather in a background thread."""
        def worker():
            try:
                data = self.get_weather(lat, lon, is_fahrenheit)
                if data:
                    on_success(data)
                else:
                    on_error("Unable to retrieve weather data from Open-Meteo.")
            except Exception as ex:
                on_error(str(ex))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def search_cities_async(self, query: str,
                            on_success: Callable[[List[Dict[str, Any]]], None],
                            on_error: Callable[[str], None]):
        """Runs search_cities in a background thread."""
        def worker():
            try:
                results = self.search_cities(query)
                on_success(results)
            except Exception as ex:
                on_error(str(ex))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
