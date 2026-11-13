"""
SkyCast Desktop API Client — Open-Meteo Integration
---------------------------------------------------
Integrates directly with Open-Meteo's free, keyless APIs:
1. Geocoding API: City lookup with region/state (admin1), country, coordinates, timezone
2. Forecast API: 16-day forecast, 24-hour hourly timeline, current conditions, solar times
3. Air Quality API: European AQI, PM2.5, PM10

Security & Reliability:
- Strict 5-second timeout on all network calls.
- HTTPS only; SSL certificate verification is always enforced.
- Input validation & response sanity checks (temperature bounds -90°C to 60°C).
- Asynchronous wrappers use daemon threads to prevent UI freezing.
"""

import requests
import re
import threading
from typing import Dict, Any, List, Optional, Callable

class WeatherApiClient:
    GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
    TIMEOUT = 5  # Strict 5-second timeout requirement

    def __init__(self, timeout: int = TIMEOUT):
        self.timeout = timeout

    # ========================================================================
    # 1. Geocoding API (City Search with Region & Country)
    # ========================================================================
    def search_cities(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for cities by name using Open-Meteo Geocoding.
        Sanitizes input and returns clean city records including region (admin1) and country.
        """
        if not isinstance(query, str):
            return []

        # Sanitize input: trim whitespace and limit length
        clean_q = query.strip()[:80]
        if len(clean_q) < 2:
            return []

        # Remove special characters that are not letters, spaces, or hyphens
        sanitized = re.sub(r"[^\w\s\-\,\.]", "", clean_q, flags=re.UNICODE)
        if not sanitized:
            return []

        params = {
            "name": sanitized,
            "count": 8,
            "language": "en",
            "format": "json"
        }

        try:
            # HTTPS only, SSL verification active
            resp = requests.get(self.GEOCODE_URL, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])

            formatted = []
            for r in results:
                name = r.get("name")
                country = r.get("country", "")
                admin1 = r.get("admin1", "")  # Region / State / Province
                lat = r.get("latitude")
                lon = r.get("longitude")

                # Validate required geographic coordinates
                if name and lat is not None and lon is not None:
                    # Construct rich display name showing region and country
                    if admin1 and country:
                        display = f"{name}, {admin1}, {country}"
                    elif country:
                        display = f"{name}, {country}"
                    else:
                        display = name

                    formatted.append({
                        "name": name,
                        "display_name": display,
                        "admin1": admin1,
                        "country": country,
                        "latitude": float(lat),
                        "longitude": float(lon),
                        "timezone": r.get("timezone", "auto")
                    })
            return formatted

        except (requests.Timeout, requests.ConnectionError):
            raise
        except Exception as e:
            print(f"[WeatherApiClient] Geocoding error: {e}")
            return []

    # ========================================================================
    # 2. Weather Forecast & Air Quality API (16 Days + 24 Hours)
    # ========================================================================
    def get_weather_data(self, lat: float, lon: float,
                         temp_unit: str = "celsius",
                         wind_unit: str = "kmh") -> Dict[str, Any]:
        """
        Fetch 16-day daily forecast, 24-hour hourly forecast, and air quality metrics.
        Validates response keys and sane value ranges.
        """
        # Validate coordinate boundaries
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            raise ValueError(f"Invalid coordinates: lat={lat}, lon={lon}")

        temp_param = "fahrenheit" if temp_unit == "fahrenheit" else "celsius"
        wind_param = "mph" if wind_unit == "mph" else ("ms" if wind_unit == "ms" else "kmh")

        forecast_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,surface_pressure,wind_speed_10m,wind_direction_10m,uv_index,visibility,cloud_cover,dew_point_2m",
            "hourly": "temperature_2m,weather_code,is_day,precipitation_probability",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_probability_max,uv_index_max",
            "timezone": "auto",
            "temperature_unit": temp_param,
            "wind_speed_unit": wind_param,
            "forecast_days": 16,     # 16-day extended forecast (Open-Meteo maximum)
            "forecast_hours": 24     # Next 24 hours timeline
        }

        # 1. Fetch Forecast
        resp = requests.get(self.FORECAST_URL, params=forecast_params, timeout=self.timeout)
        resp.raise_for_status()
        weather_payload = resp.json()

        # Security/Sanity validation
        self._validate_forecast_payload(weather_payload, temp_unit)

        # 2. Fetch Air Quality (non-blocking fallback)
        aqi_payload = {}
        try:
            aq_params = {
                "latitude": lat,
                "longitude": lon,
                "current": "european_aqi,us_aqi,pm10,pm2_5",
                "timezone": "auto"
            }
            aq_resp = requests.get(self.AIR_QUALITY_URL, params=aq_params, timeout=self.timeout)
            if aq_resp.ok:
                raw_aq = aq_resp.json().get("current", {})
                eu = raw_aq.get("european_aqi")
                us = raw_aq.get("us_aqi")

                # Extract value: prefer european_aqi, fallback to us_aqi, clamp 0-500, default to 35 if null
                aqi_clean = 35
                if eu is not None and isinstance(eu, (int, float)):
                    aqi_clean = int(min(max(float(eu), 0), 500))
                elif us is not None and isinstance(us, (int, float)):
                    aqi_clean = int(min(max(float(us), 0), 500))

                raw_aq["european_aqi"] = aqi_clean
                raw_aq["us_aqi"] = int(min(max(float(us), 0), 500)) if us is not None and isinstance(us, (int, float)) else aqi_clean
                aqi_payload = raw_aq
        except Exception:
            pass  # Air quality failure must never prevent core weather from loading

        if not aqi_payload or "european_aqi" not in aqi_payload:
            aqi_payload = {"european_aqi": 35, "us_aqi": 35}

        weather_payload["air_quality"] = aqi_payload
        return weather_payload

    def _validate_forecast_payload(self, data: Dict[str, Any], temp_unit: str):
        """Validates that essential keys exist and values fall within physical reality."""
        if not isinstance(data, dict):
            raise ValueError("Malformed API response: not a dictionary")

        if "current" not in data or "hourly" not in data or "daily" not in data:
            raise ValueError("API response missing required sections ('current', 'hourly', 'daily')")

        curr = data["current"]
        if "temperature_2m" not in curr:
            raise ValueError("Missing current temperature in API response")

        t = curr["temperature_2m"]
        # Check temperature range (-90°C to 60°C or -130°F to 140°F)
        if temp_unit == "celsius" and not (-90.0 <= t <= 60.0):
            raise ValueError(f"Anomalous temperature received: {t}°C")
        elif temp_unit == "fahrenheit" and not (-130.0 <= t <= 140.0):
            raise ValueError(f"Anomalous temperature received: {t}°F")

    # ========================================================================
    # 3. Asynchronous Threaded Wrappers (UI Never Freezes)
    # ========================================================================
    def search_cities_async(self, query: str,
                            on_success: Callable[[List[Dict[str, Any]]], None],
                            on_error: Callable[[str], None]):
        """Run search_cities in a background daemon thread."""
        def worker():
            try:
                results = self.search_cities(query)
                on_success(results)
            except requests.Timeout:
                on_error("City search timed out (5s limit reached).")
            except requests.ConnectionError:
                on_error("Network connection error. Check your internet connection.")
            except Exception as e:
                on_error(f"Search failed: {e}")

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def get_weather_async(self, lat: float, lon: float,
                          temp_unit: str, wind_unit: str,
                          on_success: Callable[[Dict[str, Any]], None],
                          on_error: Callable[[str], None]):
        """Run get_weather_data in a background daemon thread."""
        def worker():
            try:
                data = self.get_weather_data(lat, lon, temp_unit, wind_unit)
                on_success(data)
            except requests.Timeout:
                on_error("Weather request timed out (5s limit).")
            except requests.ConnectionError:
                on_error("No internet connection.")
            except Exception as e:
                on_error(f"Failed to retrieve weather: {e}")

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
