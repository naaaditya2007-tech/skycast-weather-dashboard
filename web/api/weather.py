"""
Vercel Serverless Function: Weather API Proxy
Calls Open-Meteo API to fetch current weather, hourly forecast, and 7-day forecast.
"""

from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

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
        data = resp.json()
        return jsonify(data)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to fetch weather data from Open-Meteo", "details": str(e)}), 502

if __name__ == "__main__":
    app.run(port=5000, debug=True)
