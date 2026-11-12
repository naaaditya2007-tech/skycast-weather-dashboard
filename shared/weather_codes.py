"""
Shared Weather Engine: WMO Weather Code Mappings and Theme Engine
Used by both the Tkinter Desktop application and the Web application.
"""

WMO_CODES = {
    0: {
        "condition": "Clear Sky",
        "day_desc": "Sunny and clear",
        "night_desc": "Clear skies",
        "theme": "sunny",
        "icon": "☀️",
        "night_icon": "🌙",
        "animation": "sunbeam"
    },
    1: {
        "condition": "Mainly Clear",
        "day_desc": "Mostly sunny",
        "night_desc": "Mostly clear",
        "theme": "partly_cloudy",
        "icon": "🌤️",
        "night_icon": "🌕",
        "animation": "clouds"
    },
    2: {
        "condition": "Partly Cloudy",
        "day_desc": "Partly cloudy",
        "night_desc": "Partly cloudy",
        "theme": "partly_cloudy",
        "icon": "⛅",
        "night_icon": "☁️",
        "animation": "clouds"
    },
    3: {
        "condition": "Overcast",
        "day_desc": "Cloudy skies",
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
        "animation": "fog"
    },
    48: {
        "condition": "Depositing Rime Fog",
        "day_desc": "Freezing fog",
        "night_desc": "Freezing fog",
        "theme": "fog",
        "icon": "🌫️",
        "night_icon": "🌫️",
        "animation": "fog"
    },
    51: {
        "condition": "Light Drizzle",
        "day_desc": "Light drizzling rain",
        "night_desc": "Light drizzle",
        "theme": "rainy",
        "icon": "🌦️",
        "night_icon": "🌧️",
        "animation": "rain"
    },
    53: {
        "condition": "Moderate Drizzle",
        "day_desc": "Drizzling rain",
        "night_desc": "Steady drizzle",
        "theme": "rainy",
        "icon": "🌧️",
        "night_icon": "🌧️",
        "animation": "rain"
    },
    55: {
        "condition": "Dense Drizzle",
        "day_desc": "Heavy drizzle",
        "night_desc": "Dense drizzle",
        "theme": "rainy",
        "icon": "🌧️",
        "night_icon": "🌧️",
        "animation": "rain"
    },
    61: {
        "condition": "Slight Rain",
        "day_desc": "Light rain",
        "night_desc": "Light rain showers",
        "theme": "rainy",
        "icon": "🌦️",
        "night_icon": "🌧️",
        "animation": "rain"
    },
    63: {
        "condition": "Moderate Rain",
        "day_desc": "Moderate rain",
        "night_desc": "Steady rain",
        "theme": "rainy",
        "icon": "🌧️",
        "night_icon": "🌧️",
        "animation": "rain"
    },
    65: {
        "condition": "Heavy Rain",
        "day_desc": "Heavy downpour",
        "night_desc": "Torrential rain",
        "theme": "rainy",
        "icon": "🌧️",
        "night_icon": "🌧️",
        "animation": "rain"
    },
    71: {
        "condition": "Slight Snow Fall",
        "day_desc": "Light flurries",
        "night_desc": "Light snow flurries",
        "theme": "snow",
        "icon": "🌨️",
        "night_icon": "🌨️",
        "animation": "snow"
    },
    73: {
        "condition": "Moderate Snow Fall",
        "day_desc": "Moderate snowfall",
        "night_desc": "Steady snow",
        "theme": "snow",
        "icon": "❄️",
        "night_icon": "❄️",
        "animation": "snow"
    },
    75: {
        "condition": "Heavy Snow Fall",
        "day_desc": "Heavy snowstorm",
        "night_desc": "Heavy blizzard snow",
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
        "night_desc": "Scattered night showers",
        "theme": "rainy",
        "icon": "🌦️",
        "night_icon": "🌧️",
        "animation": "rain"
    },
    81: {
        "condition": "Moderate Rain Showers",
        "day_desc": "Scattered showers",
        "night_desc": "Rain showers",
        "theme": "rainy",
        "icon": "🌧️",
        "night_icon": "🌧️",
        "animation": "rain"
    },
    82: {
        "condition": "Violent Rain Showers",
        "day_desc": "Violent downpours",
        "night_desc": "Violent night showers",
        "theme": "rainy",
        "icon": "⛈️",
        "night_icon": "⛈️",
        "animation": "rain"
    },
    85: {
        "condition": "Slight Snow Showers",
        "day_desc": "Scattered snow showers",
        "night_desc": "Snow showers",
        "theme": "snow",
        "icon": "🌨️",
        "night_icon": "🌨️",
        "animation": "snow"
    },
    86: {
        "condition": "Heavy Snow Showers",
        "day_desc": "Intense snow showers",
        "night_desc": "Heavy snow showers",
        "theme": "snow",
        "icon": "❄️",
        "night_icon": "❄️",
        "animation": "snow"
    },
    95: {
        "condition": "Thunderstorm",
        "day_desc": "Thunderstorms with lightning",
        "night_desc": "Severe night thunderstorms",
        "theme": "thunderstorm",
        "icon": "⚡",
        "night_icon": "🌩️",
        "animation": "thunderstorm"
    },
    96: {
        "condition": "Thunderstorm with Slight Hail",
        "day_desc": "Thunderstorm & hail",
        "night_desc": "Thunderstorm & hail",
        "theme": "thunderstorm",
        "icon": "⛈️",
        "night_icon": "⛈️",
        "animation": "thunderstorm"
    },
    99: {
        "condition": "Thunderstorm with Heavy Hail",
        "day_desc": "Severe thunderstorm with violent hail",
        "night_desc": "Severe thunderstorm & heavy hail",
        "theme": "thunderstorm",
        "icon": "⛈️",
        "night_icon": "⛈️",
        "animation": "thunderstorm"
    }
}

DEFAULT_WEATHER = {
    "condition": "Unknown",
    "day_desc": "Weather data available",
    "night_desc": "Weather data available",
    "theme": "cloudy",
    "icon": "🌤️",
    "night_icon": "🌙",
    "animation": "clouds"
}

def get_weather_info(code: int, is_day: int = 1) -> dict:
    """Returns weather details given a WMO code and day/night flag."""
    item = WMO_CODES.get(code, DEFAULT_WEATHER)
    desc = item["day_desc"] if is_day == 1 else item["night_desc"]
    icon = item["icon"] if is_day == 1 else item["night_icon"]
    theme_suffix = "day" if is_day == 1 else "night"
    
    return {
        "code": code,
        "condition": item["condition"],
        "description": desc,
        "theme_name": f"{item['theme']}_{theme_suffix}" if item['theme'] in ['sunny', 'partly_cloudy', 'fog'] else item['theme'],
        "base_theme": item["theme"],
        "is_day": bool(is_day),
        "icon": icon,
        "animation": item["animation"]
    }
