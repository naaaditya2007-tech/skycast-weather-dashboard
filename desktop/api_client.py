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

def calculate_aqi_from_pm25(pm25: float) -> int:
    """
    Standard EPA / Indian National Air Quality Index (NAQI) conversion from PM2.5 (ug/m3):
    Breakpoints (C_low - C_high) -> AQI (I_low - I_high)
      0.0 -  12.0 ->   0 -  50 (Good)
     12.1 -  35.4 ->  51 - 100 (Moderate)
     35.5 -  55.4 -> 101 - 150 (Unhealthy for Sensitive Groups)
     55.5 - 150.4 -> 151 - 200 (Unhealthy)
    150.5 - 250.4 -> 201 - 300 (Very Unhealthy)
    250.5 - 350.4 -> 301 - 400 (Hazardous)
    350.5 - 500.4 -> 401 - 500 (Hazardous)
    """
    if pm25 is None or pm25 < 0:
        return 50
    c = round(float(pm25), 1)
    breakpoints = [
        (0.0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 350.4, 301, 400),
        (350.5, 500.4, 401, 500),
    ]
    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= c <= c_high:
            return round(((i_high - i_low) / (c_high - c_low)) * (c - c_low) + i_low)
    if c > 500.4:
        return 500
    return 50

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
                "current": "us_aqi,european_aqi,pm2_5,pm10",
                "timezone": "auto"
            }
            aq_resp = requests.get(self.AIR_QUALITY_URL, params=aq_params, timeout=self.timeout)
            if aq_resp.ok:
                raw_aq = aq_resp.json().get("current", {})
                us_aqi = raw_aq.get("us_aqi")
                eu_aqi = raw_aq.get("european_aqi")
                pm2_5 = raw_aq.get("pm2_5")
                pm10 = raw_aq.get("pm10")

                # Extract US/Indian standard AQI (0-500 scale)
                aqi_clean = None
                if us_aqi is not None and isinstance(us_aqi, (int, float)) and float(us_aqi) > 0:
                    aqi_clean = int(min(max(float(us_aqi), 0), 500))
                elif pm2_5 is not None and isinstance(pm2_5, (int, float)):
                    # Calculate standard EPA / Indian AQI directly from PM2.5 concentration
                    aqi_clean = calculate_aqi_from_pm25(float(pm2_5))
                elif eu_aqi is not None and isinstance(eu_aqi, (int, float)):
                    # Approximate European AQI (0-100) -> standard scale (0-500)
                    aqi_clean = int(min(max(float(eu_aqi) * 2.5, 0), 500))
                else:
                    aqi_clean = 50

                raw_aq["us_aqi"] = aqi_clean
                raw_aq["aqi"] = aqi_clean
                raw_aq["pm2_5"] = round(float(pm2_5), 1) if pm2_5 is not None else 12.0
                raw_aq["pm10"] = round(float(pm10), 1) if pm10 is not None else 20.0
                aqi_payload = raw_aq
        except Exception:
            pass  # Air quality failure must never prevent core weather from loading

        if not aqi_payload or "us_aqi" not in aqi_payload:
            aqi_payload = {"us_aqi": 50, "aqi": 50, "pm2_5": 12.0, "pm10": 20.0}

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
