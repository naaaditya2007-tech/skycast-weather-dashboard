"""
SkyCast Desktop API Client — Open-Meteo Integration
---------------------------------------------------
Interacts exclusively with the free, keyless Open-Meteo suite:
1. Geocoding API: City lookup with coordinates & timezone
2. Forecast API: Current conditions, extra detail tiles, hourly & 7-day outlook
3. Air Quality API: European AQI, PM2.5, PM10

All network calls are strictly capped at 5 seconds timeout.
Asynchronous wrappers utilize Python's standard `threading.Thread` to prevent UI freezing.
"""

import requests
import threading
from typing import Dict, Any, List, Optional, Callable

class WeatherApiClient:
    GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
    TIMEOUT = 5  # 5 seconds strict timeout as per requirements

    def search_cities(self, query: str) -> List[Dict[str, Any]]:
        """
        Search cities by name using Open-Meteo Geocoding API.
        Returns a list of clean city dictionaries.
        """
        clean_q = query.strip()
        if len(clean_q) < 2:
            return []

        params = {
            "name": clean_q,
            "count": 6,
            "language": "en",
            "format": "json"
        }
        resp = requests.get(self.GEOCODE_URL, params=params, timeout=self.TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])

        formatted = []
        for r in results:
            name = r.get("name")
            country = r.get("country", "")
            admin1 = r.get("admin1", "")
            display_str = f"{name}, {admin1}, {country}" if admin1 else f"{name}, {country}"
            formatted.append({
                "name": name,
                "display_name": display_str,
                "country": country,
                "latitude": r.get("latitude"),
                "longitude": r.get("longitude"),
                "timezone": r.get("timezone", "auto")
            })
        return formatted

    def get_weather_data(self, lat: float, lon: float,
                         temp_unit: str = "celsius",
                         wind_unit: str = "kmh") -> Dict[str, Any]:
        """
        Fetch both weather forecast and air quality data, combining them into a unified payload.
        """
        forecast_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,surface_pressure,wind_speed_10m,wind_direction_10m,uv_index,visibility,cloud_cover,dew_point_2m",
            "hourly": "temperature_2m,weather_code,is_day,precipitation_probability",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_probability_max,uv_index_max",
            "timezone": "auto",
            "temperature_unit": "fahrenheit" if temp_unit == "fahrenheit" else "celsius",
            "wind_speed_unit": "mph" if wind_unit == "mph" else ("ms" if wind_unit == "ms" else "kmh"),
            "forecast_days": 7,
            "forecast_hours": 24
        }

        # 1. Weather forecast call
        resp = requests.get(self.FORECAST_URL, params=forecast_params, timeout=self.TIMEOUT)
        resp.raise_for_status()
        weather_data = resp.json()

        # 2. Air quality call (optional enhancement)
        aqi_data = {}
        try:
            aq_params = {
                "latitude": lat,
                "longitude": lon,
                "current": "european_aqi,us_aqi,pm10,pm2_5",
                "timezone": "auto"
            }
            aq_resp = requests.get(self.AIR_QUALITY_URL, params=aq_params, timeout=self.TIMEOUT)
            if aq_resp.ok:
                aqi_data = aq_resp.json().get("current", {})
        except Exception as e:
            print(f"[WeatherApiClient] Air Quality fetch notice: {e}")

        # Inject air quality metrics into payload
        weather_data["air_quality"] = aqi_data
        return weather_data

    # --- Asynchronous Threaded Wrappers ---

    def search_cities_async(self, query: str,
                            on_success: Callable[[List[Dict[str, Any]]], None],
                            on_error: Callable[[str], None]):
        """Run search_cities in a non-blocking background thread."""
        def worker():
            try:
                results = self.search_cities(query)
                on_success(results)
            except requests.Timeout:
                on_error("City search timed out (5s). Please check your internet connection.")
            except requests.ConnectionError:
                on_error("Network connection error. Please verify your connection.")
            except Exception as e:
                on_error(f"Search failed: {e}")

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def get_weather_async(self, lat: float, lon: float,
                          temp_unit: str, wind_unit: str,
                          on_success: Callable[[Dict[str, Any]], None],
                          on_error: Callable[[str], None]):
        """Run get_weather_data in a non-blocking background thread."""
        def worker():
            try:
                data = self.get_weather_data(lat, lon, temp_unit, wind_unit)
                on_success(data)
            except requests.Timeout:
                on_error("Weather request timed out (5s).")
            except requests.ConnectionError:
                on_error("No internet connection.")
            except Exception as e:
                on_error(f"Failed to fetch weather: {e}")

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
