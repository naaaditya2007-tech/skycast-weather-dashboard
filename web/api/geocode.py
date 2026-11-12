"""
Vercel Serverless Function: Geocode & Reverse Geocode API
Handles city name search and coordinate-to-city reverse geocoding.
"""

from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
REVERSE_GEO_URL = "https://api.bigdatacloud.net/data/reverse-geocode-client"

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

    return jsonify({"error": "Please provide 'city' or both 'lat' and 'lon'"}), 400

if __name__ == "__main__":
    app.run(port=5001, debug=True)
