"""
SkyCast Storage Module — Settings, Favorites, and Offline Cache
--------------------------------------------------------------
Handles local JSON persistence for:
1. User unit preferences (temp: °C/°F, wind: km/h/mph/m/s, pressure: hPa/inHg)
2. Last searched city for auto-restoring state upon launch
3. Favourites list (add, remove, toggle)
4. Offline cache of the last retrieved weather payload
"""

import json
import os
import time
from typing import Dict, Any, List, Optional

STORAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skycast_data.json")

DEFAULT_SETTINGS = {
    "units": {
        "temp": "celsius",     # "celsius" or "fahrenheit"
        "wind": "kmh",         # "kmh", "mph", or "ms"
        "pressure": "hPa"      # "hPa" or "inHg"
    },
    "last_city": {
        "name": "London",
        "country": "United Kingdom",
        "lat": 51.5074,
        "lon": -0.1278,
        "timezone": "Europe/London"
    },
    "favorites": [
        {"name": "London", "country": "United Kingdom", "lat": 51.5074, "lon": -0.1278},
        {"name": "Tokyo", "country": "Japan", "lat": 35.6895, "lon": 139.6917},
        {"name": "New York", "country": "United States", "lat": 40.7128, "lon": -74.0060}
    ],
    "cache": None,
    "cache_timestamp": 0
}

class StorageManager:
    def __init__(self, filepath: str = STORAGE_FILE):
        self.filepath = filepath
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load configuration from disk with default fallback."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    # Merge with default settings to preserve new keys
                    merged = dict(DEFAULT_SETTINGS)
                    merged.update(loaded)
                    return merged
            except Exception as e:
                print(f"[StorageManager] Error reading {self.filepath}: {e}. Using defaults.")
        return dict(DEFAULT_SETTINGS)

    def save(self) -> bool:
        """Write current configuration safely to disk."""
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[StorageManager] Error saving to {self.filepath}: {e}")
            return False

    # Unit getters and setters
    def get_units(self) -> Dict[str, str]:
        return self.data.get("units", DEFAULT_SETTINGS["units"])

    def set_unit(self, category: str, value: str):
        """category: 'temp' | 'wind' | 'pressure'"""
        if "units" not in self.data:
            self.data["units"] = dict(DEFAULT_SETTINGS["units"])
        self.data["units"][category] = value
        self.save()

    # Last searched city
    def get_last_city(self) -> Dict[str, Any]:
        return self.data.get("last_city", DEFAULT_SETTINGS["last_city"])

    def set_last_city(self, city_dict: Dict[str, Any]):
        self.data["last_city"] = city_dict
        self.save()

    # Favorites management
    def get_favorites(self) -> List[Dict[str, Any]]:
        return self.data.get("favorites", [])

    def is_favorite(self, city_name: str) -> bool:
        target = city_name.strip().lower()
        for fav in self.get_favorites():
            if fav.get("name", "").strip().lower() == target:
                return True
        return False

    def add_favorite(self, city_dict: Dict[str, Any]) -> bool:
        if not self.is_favorite(city_dict.get("name", "")):
            self.data["favorites"].append(city_dict)
            self.save()
            return True
        return False

    def remove_favorite(self, city_name: str) -> bool:
        target = city_name.strip().lower()
        favs = self.get_favorites()
        initial_len = len(favs)
        self.data["favorites"] = [f for f in favs if f.get("name", "").strip().lower() != target]
        if len(self.data["favorites"]) < initial_len:
            self.save()
            return True
        return False

    # Offline cache
    def save_cache(self, weather_payload: Dict[str, Any]):
        """Persist weather data for offline fallback."""
        self.data["cache"] = weather_payload
        self.data["cache_timestamp"] = int(time.time())
        self.save()

    def get_cache(self) -> Optional[Dict[str, Any]]:
        """Retrieve cached weather payload if available."""
        return self.data.get("cache")

    def get_cache_timestamp(self) -> int:
        return self.data.get("cache_timestamp", 0)
