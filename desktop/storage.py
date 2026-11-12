"""
SkyCast Desktop Storage Module — settings.json Persistence
----------------------------------------------------------
Handles persistent configuration and caching using a local JSON file:
- User units preferences (temp: celsius/fahrenheit, wind: kmh/mph/ms, pressure: hPa/inHg)
- Last searched city for launch restoration
- User's saved favorites list (for the 'Other Cities' right column)
- Offline weather cache with timestamp

Security & Robustness:
- Strict try/except and type validation on load.
- Corrupt files or schema mismatch are safely reset to defaults without crashing.
"""

import json
import os
import time
from typing import Dict, Any, List, Optional

# Default path points to settings.json in desktop folder
DEFAULT_SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

# Verified default fallback schema
DEFAULT_SETTINGS = {
    "units": {
        "temp": "celsius",      # "celsius" | "fahrenheit"
        "wind": "kmh",          # "kmh" | "mph" | "ms"
        "pressure": "hPa"       # "hPa" | "inHg"
    },
    "last_city": {
        "name": "London",
        "country": "United Kingdom",
        "admin1": "England",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "timezone": "Europe/London"
    },
    "favorites": [
        {"name": "Beijing", "country": "China", "admin1": "Beijing", "latitude": 39.9042, "longitude": 116.4074},
        {"name": "Tokyo", "country": "Japan", "admin1": "Tokyo", "latitude": 35.6895, "longitude": 139.6917},
        {"name": "Brasília", "country": "Brazil", "admin1": "Federal District", "latitude": -15.7939, "longitude": -47.8828},
        {"name": "Berlin", "country": "Germany", "admin1": "Berlin", "latitude": 52.5200, "longitude": 13.4050},
        {"name": "Canberra", "country": "Australia", "admin1": "Australian Capital Territory", "latitude": -35.2809, "longitude": 149.1300}
    ],
    "cache": None,
    "cache_timestamp": 0
}

class StorageManager:
    def __init__(self, filepath: str = DEFAULT_SETTINGS_PATH):
        self.filepath = filepath
        self.data: Dict[str, Any] = self._load_and_validate()

    def _get_defaults(self) -> Dict[str, Any]:
        """Return a fresh copy of default settings."""
        return {
            "units": dict(DEFAULT_SETTINGS["units"]),
            "last_city": dict(DEFAULT_SETTINGS["last_city"]),
            "favorites": [dict(f) for f in DEFAULT_SETTINGS["favorites"]],
            "cache": None,
            "cache_timestamp": 0
        }

    def _load_and_validate(self) -> Dict[str, Any]:
        """
        Load settings.json with type-checking and validation.
        Resets safely to defaults if corrupted or unreadable.
        """
        defaults = self._get_defaults()
        if not os.path.exists(self.filepath):
            return defaults

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    print("[StorageManager] settings.json was empty. Initializing defaults.")
                    return defaults
                raw = json.loads(content)

            # Security: Type validation
            if not isinstance(raw, dict):
                print("[StorageManager] Corrupt root structure. Resetting to defaults.")
                return defaults

            validated = dict(defaults)

            # Validate 'units'
            if "units" in raw and isinstance(raw["units"], dict):
                u = raw["units"]
                if u.get("temp") in ("celsius", "fahrenheit"):
                    validated["units"]["temp"] = u["temp"]
                if u.get("wind") in ("kmh", "mph", "ms"):
                    validated["units"]["wind"] = u["wind"]
                if u.get("pressure") in ("hPa", "inHg"):
                    validated["units"]["pressure"] = u["pressure"]

            # Validate 'last_city'
            if "last_city" in raw and isinstance(raw["last_city"], dict):
                c = raw["last_city"]
                if isinstance(c.get("name"), str) and ("latitude" in c or "lat" in c):
                    validated["last_city"] = {
                        "name": str(c.get("name", "London")),
                        "country": str(c.get("country", "")),
                        "admin1": str(c.get("admin1", "")),
                        "latitude": float(c.get("latitude", c.get("lat", 51.5074))),
                        "longitude": float(c.get("longitude", c.get("lon", -0.1278))),
                        "timezone": str(c.get("timezone", "auto"))
                    }

            # Validate 'favorites'
            if "favorites" in raw and isinstance(raw["favorites"], list):
                fav_list = []
                for item in raw["favorites"]:
                    if isinstance(item, dict) and "name" in item:
                        fav_list.append({
                            "name": str(item.get("name")),
                            "country": str(item.get("country", "")),
                            "admin1": str(item.get("admin1", "")),
                            "latitude": float(item.get("latitude", item.get("lat", 0.0))),
                            "longitude": float(item.get("longitude", item.get("lon", 0.0)))
                        })
                validated["favorites"] = fav_list

            # Cache & timestamp
            if "cache" in raw and isinstance(raw["cache"], dict):
                validated["cache"] = raw["cache"]
            if "cache_timestamp" in raw and isinstance(raw["cache_timestamp"], (int, float)):
                validated["cache_timestamp"] = int(raw["cache_timestamp"])

            return validated

        except Exception as e:
            print(f"[StorageManager] Error reading settings ({e}). Safely resetting to defaults.")
            return defaults

    def save(self) -> bool:
        """Atomically persist validated settings to settings.json."""
        try:
            # Ensure parent dir exists
            os.makedirs(os.path.dirname(os.path.abspath(self.filepath)), exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[StorageManager] Error saving settings: {e}")
            return False

    # --- Unit Controls ---
    def get_units(self) -> Dict[str, str]:
        return dict(self.data.get("units", DEFAULT_SETTINGS["units"]))

    def set_unit(self, category: str, value: str) -> bool:
        """Update unit choice: category in ('temp', 'wind', 'pressure')."""
        valid_options = {
            "temp": ("celsius", "fahrenheit"),
            "wind": ("kmh", "mph", "ms"),
            "pressure": ("hPa", "inHg")
        }
        if category in valid_options and value in valid_options[category]:
            self.data["units"][category] = value
            return self.save()
        return False

    # --- Last City ---
    def get_last_city(self) -> Dict[str, Any]:
        return dict(self.data.get("last_city", DEFAULT_SETTINGS["last_city"]))

    def set_last_city(self, city: Dict[str, Any]) -> bool:
        self.data["last_city"] = {
            "name": str(city.get("name", "London")),
            "country": str(city.get("country", "")),
            "admin1": str(city.get("admin1", "")),
            "latitude": float(city.get("latitude", city.get("lat", 51.5074))),
            "longitude": float(city.get("longitude", city.get("lon", -0.1278))),
            "timezone": str(city.get("timezone", "auto"))
        }
        return self.save()

    # --- Favorites Management (Other Cities) ---
    def get_favorites(self) -> List[Dict[str, Any]]:
        return [dict(f) for f in self.data.get("favorites", [])]

    def is_favorite(self, city_name: str) -> bool:
        target = city_name.strip().lower()
        return any(f.get("name", "").strip().lower() == target for f in self.get_favorites())

    def add_favorite(self, city: Dict[str, Any]) -> bool:
        name = str(city.get("name", "")).strip()
        if not name or self.is_favorite(name):
            return False
        clean_entry = {
            "name": name,
            "country": str(city.get("country", "")),
            "admin1": str(city.get("admin1", "")),
            "latitude": float(city.get("latitude", city.get("lat", 0.0))),
            "longitude": float(city.get("longitude", city.get("lon", 0.0)))
        }
        self.data["favorites"].append(clean_entry)
        return self.save()

    def remove_favorite(self, city_name: str) -> bool:
        target = city_name.strip().lower()
        favs = self.get_favorites()
        initial_len = len(favs)
        self.data["favorites"] = [f for f in favs if f.get("name", "").strip().lower() != target]
        if len(self.data["favorites"]) < initial_len:
            return self.save()
        return False

    # --- Offline Fallback Cache ---
    def save_cache(self, weather_data: Dict[str, Any]) -> bool:
        self.data["cache"] = weather_data
        self.data["cache_timestamp"] = int(time.time())
        return self.save()

    def get_cache(self) -> Optional[Dict[str, Any]]:
        return self.data.get("cache")

    def get_cache_timestamp(self) -> int:
        return self.data.get("cache_timestamp", 0)
