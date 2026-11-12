"""
Vercel Serverless Function: Unified Backend API
Handles /api/weather and /api/geocode.
"""

from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
REVERSE_GEO_URL = "https://api.bigdatacloud.net/data/reverse-geocode-client"

@app.route("/api/weather", methods=["GET"])
def get_weather():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    units = request.args.get("units", "celsius")

    if not lat or not lon:
        return jsonify({"error": "Latitude and longitude query parameters are required"}), 400

    unit_temp = "fahrenheit" if units == "fahrenheit" else "celsius"
    unit_wind = "mph" if units == "fahrenheit" else "kmh"

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
        resp = requests.get(OPEN_METEO_FORECAST_URL, params=params, timeout=10)
        resp.raise_for_status()
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": "Failed to fetch weather data", "details": str(e)}), 502

@app.route("/api/geocode", methods=["GET"])
def geocode():
    city = request.args.get("city")
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    if city:
        params = {
            "name": city.strip(),
            "count": 5,
            "language": "en",
            "format": "json"
        }
        try:
            resp = requests.get(GEOCODE_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            formatted = []
            for r in results:
                name = r.get("name")
                country = r.get("country", "")
                admin1 = r.get("admin1", "")
                loc_label = f"{name}, {admin1}, {country}" if admin1 else f"{name}, {country}"
                formatted.append({
                    "name": name,
                    "display_name": loc_label,
                    "country": country,
                    "latitude": r.get("latitude"),
                    "longitude": r.get("longitude")
                })
            return jsonify({"results": formatted})
        except Exception as e:
            return jsonify({"error": "Failed to search city", "details": str(e)}), 502

    elif lat and lon:
        params = {
            "latitude": lat,
            "longitude": lon,
            "localityLanguage": "en"
        }
        try:
            resp = requests.get(REVERSE_GEO_URL, params=params, timeout=10)
            resp.raise_for_status()
            r = resp.json()
            city_name = r.get("city") or r.get("locality") or r.get("principalSubdivision") or "Unknown Location"
            country_name = r.get("countryName", "")
            return jsonify({
                "city": city_name,
                "country": country_name,
                "display_name": f"{city_name}, {country_name}" if country_name else city_name,
                "latitude": float(lat),
                "longitude": float(lon)
            })
        except Exception as e:
            return jsonify({"error": "Failed to reverse geocode", "details": str(e)}), 502

    return jsonify({"error": "Provide city or lat+lon"}), 400

if __name__ == "__main__":
    app.run(port=5000)
