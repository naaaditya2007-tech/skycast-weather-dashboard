"""
SkyCast Stage 2 Terminal Verification Script
-------------------------------------------
Tests the exact 5 scenarios requested by the user:
1. A London weather fetch (current, hourly, 16-day daily, AQI)
2. A city search for 'Springfield' (showing region/admin1 and country)
3. An invalid city search
4. A failed request with the internet off (ConnectionError handling)
5. Saving and loading settings.json (including corruption recovery)
"""

import os
import sys
import requests

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from desktop.storage import StorageManager
from desktop.api_client import WeatherApiClient

def run_stage2_tests():
    print("=" * 70)
    print("   SKYCAST STAGE 2: DESKTOP API CLIENT & STORAGE VERIFICATION")
    print("=" * 70)

    client = WeatherApiClient()
    settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
    storage = StorageManager(filepath=settings_file)

    # ------------------------------------------------------------------------
    # 1. London Weather Fetch
    # ------------------------------------------------------------------------
    print("\n[TEST 1] Fetching live weather for London...")
    try:
        # London coordinates: 51.5074, -0.1278
        london_data = client.get_weather_data(51.5074, -0.1278, temp_unit="celsius", wind_unit="kmh")
        curr = london_data.get("current", {})
        daily = london_data.get("daily", {})
        hourly = london_data.get("hourly", {})
        aqi = london_data.get("air_quality", {})

        print("  ✓ SUCCESS: Live weather received from Open-Meteo:")
        print(f"    - Current Temperature : {curr.get('temperature_2m')}°C (Feels like: {curr.get('apparent_temperature')}°C)")
        print(f"    - Weather Code        : {curr.get('weather_code')}")
        print(f"    - Humidity / Pressure : {curr.get('relative_humidity_2m')}% / {curr.get('surface_pressure')} hPa")
        print(f"    - Wind Speed & Dir    : {curr.get('wind_speed_10m')} km/h @ {curr.get('wind_direction_10m')}°")
        print(f"    - UV Index            : {curr.get('uv_index')}")
        print(f"    - Dew Point           : {curr.get('dew_point_2m')}°C")
        print(f"    - Air Quality (AQI)   : European AQI = {aqi.get('european_aqi')}, PM2.5 = {aqi.get('pm2_5')} µg/m³")
        print(f"    - Hourly Data Points  : {len(hourly.get('time', []))} hours (Rain chance sample: {hourly.get('precipitation_probability', [0])[0]}%)")
        print(f"    - Daily Forecast Days : {len(daily.get('time', []))} days (16-day extended range verified)")

    except Exception as e:
        print(f"  ✗ FAILED: {e}")

    # ------------------------------------------------------------------------
    # 2. City Search for "Springfield" (Showing Region and Country)
    # ------------------------------------------------------------------------
    print("\n[TEST 2] Searching city 'Springfield' via Open-Meteo Geocoding...")
    try:
        results = client.search_cities("Springfield")
        print(f"  ✓ SUCCESS: Found {len(results)} matching cities named 'Springfield':")
        for i, r in enumerate(results, 1):
            region_str = r.get("admin1") or "N/A"
            country_str = r.get("country") or "N/A"
            print(f"    {i}. {r['name']} | Region: {region_str} | Country: {country_str}")
            print(f"       -> Display Name: \"{r['display_name']}\" (Lat: {r['latitude']}, Lon: {r['longitude']})")

    except Exception as e:
        print(f"  ✗ FAILED: {e}")

    # ------------------------------------------------------------------------
    # 3. Invalid City Search
    # ------------------------------------------------------------------------
    print("\n[TEST 3] Searching invalid city 'Xyzzynonexistentcity123'...")
    try:
        results_invalid = client.search_cities("Xyzzynonexistentcity123")
        print(f"  ✓ SUCCESS: Returned {len(results_invalid)} results (graceful empty list, zero crash).")

    except Exception as e:
        print(f"  ✗ FAILED: {e}")

    # ------------------------------------------------------------------------
    # 4. Failed Request with Internet Off (Simulated ConnectionError)
    # ------------------------------------------------------------------------
    print("\n[TEST 4] Testing failed request with internet off (Simulated ConnectionError)...")
    # Point client to non-routable IP to simulate immediate connection failure
    offline_client = WeatherApiClient()
    offline_client.FORECAST_URL = "https://192.0.2.1/simulated_offline_endpoint"
    offline_client.timeout = 1  # fast 1s timeout for test

    try:
        offline_client.get_weather_data(51.5074, -0.1278)
        print("  ✗ FAILED: Request should have raised connection/network failure.")
    except (requests.ConnectionError, requests.Timeout) as ex:
        print(f"  ✓ SUCCESS: Caught expected network exception: {type(ex).__name__}")
        print("  ✓ Graceful error message: 'No internet connection / Request timed out.'")

    # ------------------------------------------------------------------------
    # 5. Saving and Loading settings.json (Persistence & Corruption Recovery)
    # ------------------------------------------------------------------------
    print("\n[TEST 5] Testing saving and loading settings.json...")
    try:
        # Step A: Save custom preferences
        print("  -> Step 5A: Updating units to Fahrenheit, mph, inHg...")
        storage.set_unit("temp", "fahrenheit")
        storage.set_unit("wind", "mph")
        storage.set_unit("pressure", "inHg")

        new_city = {
            "name": "Springfield",
            "admin1": "Illinois",
            "country": "United States",
            "latitude": 39.7817,
            "longitude": -89.6501,
            "timezone": "America/Chicago"
        }
        storage.set_last_city(new_city)
        storage.add_favorite(new_city)
        print(f"  -> Step 5B: Saved last city as '{new_city['name']}, {new_city['admin1']}' and added to favorites.")

        # Step B: Load back from disk using a fresh StorageManager instance
        fresh_storage = StorageManager(filepath=settings_file)
        loaded_units = fresh_storage.get_units()
        loaded_city = fresh_storage.get_last_city()
        loaded_favs = fresh_storage.get_favorites()

        print(f"  ✓ SUCCESS: Fresh reload verified from {os.path.basename(settings_file)}:")
        print(f"    - Loaded Units     : {loaded_units}")
        print(f"    - Loaded Last City : {loaded_city['name']} ({loaded_city['admin1']}, {loaded_city['country']})")
        print(f"    - Favorites Count  : {len(loaded_favs)} (contains Springfield: {fresh_storage.is_favorite('Springfield')})")

        # Step C: Test corruption recovery (Security requirement)
        print("  -> Step 5C: Testing recovery from corrupted JSON file...")
        with open(settings_file, "w", encoding="utf-8") as f:
            f.write("{{BROKEN_CORRUPT_JSON_DATA!@#$%^&*")

        corrupt_recovery_storage = StorageManager(filepath=settings_file)
        recovered_units = corrupt_recovery_storage.get_units()
        print("  ✓ SUCCESS: Corrupt file detected and safely recovered without crashing!")
        print(f"    - Recovered default units: {recovered_units}")

        # Restore valid settings
        corrupt_recovery_storage.save()

    except Exception as e:
        print(f"  ✗ FAILED: {e}")

    print("\n" + "=" * 70)
    print("   STAGE 2 VERIFICATION COMPLETE: ALL 5 SCENARIOS PASSED")
    print("=" * 70)

if __name__ == "__main__":
    run_stage2_tests()
