"""
SkyCast Weather Engine — Shared WMO Weather Code Mappings & Environmental Scales
-------------------------------------------------------------------------------
This module provides standard World Meteorological Organization (WMO) code mappings,
condition descriptions, icons, visual themes, animation types, and environmental
metric classifications (Air Quality Index and UV Index).

Used by both the Python Tkinter desktop application and mirrored in the web app.
"""

# WMO Weather Interpretation Codes (WW) defined by the World Meteorological Organization
# Keys: integer weather codes reported by Open-Meteo
WMO_CODES = {
    0: {
        "condition": "Clear Sky",
        "day_desc": "Sunny and clear",
        "night_desc": "Clear skies",
        "theme": "clear",
        "icon": "☀️",
        "night_icon": "🌙",
        "animation": "sunbeam"
    },
    1: {
        "condition": "Mainly Clear",
        "day_desc": "Mostly sunny",
        "night_desc": "Mostly clear",
        "theme": "cloudy",
        "icon": "🌤️",
        "night_icon": "🌕",
        "animation": "clouds"
    },
    2: {
        "condition": "Partly Cloudy",
        "day_desc": "Partly cloudy",
        "night_desc": "Partly cloudy",
        "theme": "cloudy",
        "icon": "⛅",
        "night_icon": "☁️",
        "animation": "clouds"
    },
    3: {
        "condition": "Overcast",
        "day_desc": "Overcast skies",
        "night_desc": "Overcast",
        "theme": "cloudy",
        "icon": "☁️",
        "night_icon": "☁️",
        "animation": "clouds"
    },
    45: {
        "condition": "Fog",
        "day_desc": "Foggy conditions",
        "night_desc": "Dense fog",
        "theme": "fog",
        "icon": "🌫️",
        "night_icon": "🌫️",
        "animation": "clouds"
    },
    48: {
        "condition": "Depositing Rime Fog",
        "day_desc": "Freezing rime fog",
        "night_desc": "Freezing rime fog",
        "theme": "fog",
        "icon": "🌫️",
        "night_icon": "🌫️",
        "animation": "clouds"
    },
    51: {
        "condition": "Light Drizzle",
        "day_desc": "Light patchy drizzle",
        "night_desc": "Light drizzle",
        "theme": "drizzle",
        "icon": "🌦️",
        "night_icon": "🌧️",
        "animation": "rain"
    },
    53: {
        "condition": "Moderate Drizzle",
        "day_desc": "Moderate drizzle",
        "night_desc": "Moderate drizzle",
        "theme": "drizzle",
        "icon": "🌧️",
        "night_icon": "🌧️",
        "animation": "rain"
    },
    55: {
        "condition": "Dense Drizzle",
        "day_desc": "Dense drizzle",
        "night_desc": "Heavy drizzle",
        "theme": "drizzle",
        "icon": "🌧️",
        "night_icon": "🌧️",
        "animation": "rain"
    },
    56: {
        "condition": "Light Freezing Drizzle",
        "day_desc": "Freezing drizzle",
        "night_desc": "Freezing drizzle",
        "theme": "drizzle",
        "icon": "🌧️",
        "night_icon": "🌧️",
        "animation": "rain"
    },
    57: {
        "condition": "Dense Freezing Drizzle",
        "day_desc": "Heavy freezing drizzle",
        "night_desc": "Heavy freezing drizzle",
        "theme": "drizzle",
        "icon": "🌧️",
        "night_icon": "🌧️",
        "animation": "rain"
    },
    61: {
        "condition": "Slight Rain",
        "day_desc": "Light rain",
        "night_desc": "Light rain",
        "theme": "rain",
        "icon": "🌦️",
        "night_icon": "🌧️",
        "animation": "rain"
    },
    63: {
        "condition": "Moderate Rain",
        "day_desc": "Moderate steady rain",
        "night_desc": "Steady rain",
        "theme": "rain",
        "icon": "🌧️",
        "night_icon": "🌧️",
        "animation": "rain"
    },
    65: {
        "condition": "Heavy Rain",
        "day_desc": "Heavy downpour",
        "night_desc": "Heavy downpour",
        "theme": "rain",
        "icon": "🌧️",
        "night_icon": "🌧️",
        "animation": "rain"
    },
    66: {
        "condition": "Light Freezing Rain",
        "day_desc": "Light freezing rain",
        "night_desc": "Light freezing rain",
        "theme": "rain",
        "icon": "🌧️",
        "night_icon": "🌧️",
        "animation": "rain"
    },
    67: {
        "condition": "Heavy Freezing Rain",
        "day_desc": "Heavy freezing rain",
        "night_desc": "Heavy freezing rain",
        "theme": "rain",
        "icon": "🌧️",
        "night_icon": "🌧️",
        "animation": "rain"
    },
    71: {
        "condition": "Slight Snow Fall",
        "day_desc": "Light snow flurries",
        "night_desc": "Light snow flurries",
        "theme": "snow",
        "icon": "🌨️",
        "night_icon": "🌨️",
        "animation": "snow"
    },
    73: {
        "condition": "Moderate Snow Fall",
        "day_desc": "Moderate snowfall",
        "night_desc": "Moderate snowfall",
        "theme": "snow",
        "icon": "❄️",
        "night_icon": "❄️",
        "animation": "snow"
    },
    75: {
        "condition": "Heavy Snow Fall",
        "day_desc": "Heavy snowstorm",
        "night_desc": "Heavy snowstorm",
        "theme": "snow",
        "icon": "❄️",
        "night_icon": "❄️",
        "animation": "snow"
    },
    77: {
        "condition": "Snow Grains",
        "day_desc": "Snow grains",
        "night_desc": "Snow grains",
        "theme": "snow",
        "icon": "🌨️",
        "night_icon": "🌨️",
        "animation": "snow"
    },
    80: {
        "condition": "Slight Rain Showers",
        "day_desc": "Passing rain showers",
        "night_desc": "Passing night showers",
        "theme": "rain",
        "icon": "🌦️",
        "night_icon": "🌧️",
        "animation": "rain"
    },
    81: {
        "condition": "Moderate Rain Showers",
        "day_desc": "Moderate rain showers",
        "night_desc": "Moderate showers",
        "theme": "rain",
        "icon": "🌧️",
        "night_icon": "🌧️",
        "animation": "rain"
    },
    82: {
        "condition": "Violent Rain Showers",
        "day_desc": "Torrential rain showers",
        "night_desc": "Torrential showers",
        "theme": "rain",
        "icon": "⛈️",
        "night_icon": "⛈️",
        "animation": "rain"
    },
    85: {
        "condition": "Slight Snow Showers",
        "day_desc": "Scattered snow showers",
        "night_desc": "Scattered snow showers",
        "theme": "snow",
        "icon": "🌨️",
        "night_icon": "🌨️",
        "animation": "snow"
    },
    86: {
        "condition": "Heavy Snow Showers",
        "day_desc": "Heavy snow showers",
        "night_desc": "Heavy snow showers",
        "theme": "snow",
        "icon": "❄️",
        "night_icon": "❄️",
        "animation": "snow"
    },
    95: {
        "condition": "Thunderstorm",
        "day_desc": "Thunderstorms with lightning",
        "night_desc": "Night thunderstorms",
        "theme": "thunderstorm",
        "icon": "⚡",
        "night_icon": "🌩️",
        "animation": "thunderstorm"
    },
    96: {
        "condition": "Thunderstorm with Slight Hail",
        "day_desc": "Thunderstorm with hail",
        "night_desc": "Thunderstorm with hail",
        "theme": "thunderstorm",
        "icon": "⛈️",
        "night_icon": "⛈️",
        "animation": "thunderstorm"
    },
    99: {
        "condition": "Thunderstorm with Heavy Hail",
        "day_desc": "Severe thunderstorm and hail",
        "night_desc": "Severe thunderstorm and hail",
        "theme": "thunderstorm",
        "icon": "⛈️",
        "night_icon": "⛈️",
        "animation": "thunderstorm"
    }
}

DEFAULT_WEATHER = {
    "condition": "Partly Cloudy",
    "day_desc": "Scattered cloud cover",
    "night_desc": "Partly cloudy",
    "theme": "cloudy",
    "icon": "🌤️",
    "night_icon": "🌙",
    "animation": "clouds"
}

def get_weather_info(code: int, is_day: int = 1) -> dict:
    """
    Resolve WMO weather code into condition info, icon, day/night theme, and particle animation.
    """
    item = WMO_CODES.get(code, DEFAULT_WEATHER)
    is_day_bool = bool(is_day)
    desc = item["day_desc"] if is_day_bool else item["night_desc"]
    icon = item["icon"] if is_day_bool else item["night_icon"]
    time_suffix = "day" if is_day_bool else "night"
    theme_key = f"{item['theme']}_{time_suffix}"

    return {
        "code": code,
        "condition": item["condition"],
        "description": desc,
        "theme": item["theme"],
        "theme_key": theme_key,
        "is_day": is_day_bool,
        "icon": icon,
        "animation": item["animation"]
    }

def get_aqi_level(european_aqi: float) -> dict:
    """
    European Air Quality Index (AQI) scale interpretation:
    0-20: Good (Green)
    20-40: Fair (Yellow)
    40-60: Moderate (Orange)
    60-80: Poor (Red)
    80-100: Very Poor (Purple)
    100+: Extremely Poor (Maroon)
    """
    val = round(float(european_aqi or 0))
    if val <= 20:
        return {"val": val, "label": "Good", "color": "#10B981", "bg": "rgba(16, 185, 129, 0.2)"}
    elif val <= 40:
        return {"val": val, "label": "Fair", "color": "#FBBF24", "bg": "rgba(251, 191, 36, 0.2)"}
    elif val <= 60:
        return {"val": val, "label": "Moderate", "color": "#F97316", "bg": "rgba(249, 115, 22, 0.2)"}
    elif val <= 80:
        return {"val": val, "label": "Poor", "color": "#EF4444", "bg": "rgba(239, 68, 68, 0.2)"}
    elif val <= 100:
        return {"val": val, "label": "Very Poor", "color": "#A855F7", "bg": "rgba(168, 85, 247, 0.2)"}
    else:
        return {"val": val, "label": "Extremely Poor", "color": "#881337", "bg": "rgba(136, 19, 55, 0.2)"}

def get_uv_level(uv_index: float) -> dict:
    """
    WHO UV Index scale:
    0-2: Low (Green)
    3-5: Moderate (Yellow)
    6-7: High (Orange)
    8-10: Very High (Red)
    11+: Extreme (Purple)
    """
    val = round(float(uv_index or 0), 1)
    if val <= 2.9:
        return {"val": val, "label": "Low", "color": "#10B981"}
    elif val <= 5.9:
        return {"val": val, "label": "Moderate", "color": "#FBBF24"}
    elif val <= 7.9:
        return {"val": val, "label": "High", "color": "#F97316"}
    elif val <= 10.9:
        return {"val": val, "label": "Very High", "color": "#EF4444"}
    else:
        return {"val": val, "label": "Extreme", "color": "#A855F7"}
