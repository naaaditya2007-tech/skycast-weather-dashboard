"""
SkyCast Weather Engine — Shared WMO Codes, Time Phases, and Atmospheric Theme System
-----------------------------------------------------------------------------------
This module is the single source of truth for weather mapping in SkyCast.
It models real-world weather using TWO inputs:
  1. The weather condition code (WMO standard 0-99 from Open-Meteo)
  2. The searched city's local time phase (calculated from local time and sunrise/sunset,
     never from the local computer clock)

It defines:
- WMO weather codes (0 clear, 1-3 cloudy, 45/48 fog, 51-57 drizzle, 61-67 rain,
  71-77 snow, 80-82 showers, 85-86 snow showers, 95-99 thunderstorm)
- Time phases: Dawn, Day, Evening (Golden Hour), Dusk, Night
- Background wallpaper image filenames and procedural gradient fallbacks
- Color tints, text readability contrast, and particle animation types
- Air Quality Index (European AQI) and UV Index classifications
"""

import datetime
from typing import Dict, Any, Tuple, Optional

# ============================================================================
# 1. WMO Weather Code Mappings (0 to 99)
# ============================================================================
# Defined by the World Meteorological Organization.
WMO_CODES = {
    0: {
        "weather_type": "clear",
        "condition": "Clear Sky",
        "day_desc": "Sunny and clear skies",
        "night_desc": "Clear starry sky",
        "day_icon": "☀️",
        "night_icon": "🌙",
        "day_anim": "sunbeam",
        "night_anim": "stars",
        "bg_day": "clear.jpg",
        "bg_night": "clear_night.jpg"
    },
    1: {
        "weather_type": "partly_cloudy",
        "condition": "Mainly Clear",
        "day_desc": "Mostly sunny with light clouds",
        "night_desc": "Mostly clear with scattered clouds",
        "day_icon": "🌤️",
        "night_icon": "🌕",
        "day_anim": "clouds",
        "night_anim": "clouds",
        "bg_day": "partly_cloudy.jpg",
        "bg_night": "clear_night.jpg"
    },
    2: {
        "weather_type": "partly_cloudy",
        "condition": "Partly Cloudy",
        "day_desc": "Partly cloudy with sunny intervals",
        "night_desc": "Partly cloudy",
        "day_icon": "⛅",
        "night_icon": "☁️",
        "day_anim": "clouds",
        "night_anim": "clouds",
        "bg_day": "partly_cloudy.jpg",
        "bg_night": "clear_night.jpg"
    },
    3: {
        "weather_type": "overcast",
        "condition": "Overcast",
        "day_desc": "Cloudy and overcast ceiling",
        "night_desc": "Dense overcast skies",
        "day_icon": "☁️",
        "night_icon": "☁️",
        "day_anim": "clouds",
        "night_anim": "clouds",
        "bg_day": "overcast.jpg",
        "bg_night": "clear_night.jpg"
    },
    45: {
        "weather_type": "fog",
        "condition": "Fog",
        "day_desc": "Dense morning fog",
        "night_desc": "Thick night fog",
        "day_icon": "🌫️",
        "night_icon": "🌫️",
        "day_anim": "fog",
        "night_anim": "fog",
        "bg_day": "fog.jpg",
        "bg_night": "fog.jpg"
    },
    48: {
        "weather_type": "fog",
        "condition": "Depositing Rime Fog",
        "day_desc": "Freezing rime fog",
        "night_desc": "Freezing rime fog",
        "day_icon": "🌫️",
        "night_icon": "🌫️",
        "day_anim": "fog",
        "night_anim": "fog",
        "bg_day": "fog.jpg",
        "bg_night": "fog.jpg"
    },
    51: {
        "weather_type": "drizzle",
        "condition": "Light Drizzle",
        "day_desc": "Light patchy drizzle",
        "night_desc": "Light night drizzle",
        "day_icon": "🌦️",
        "night_icon": "🌧️",
        "day_anim": "drizzle",
        "night_anim": "drizzle",
        "bg_day": "rain.jpg",
        "bg_night": "rain_night.jpg"
    },
    53: {
        "weather_type": "drizzle",
        "condition": "Moderate Drizzle",
        "day_desc": "Steady drizzling precipitation",
        "night_desc": "Steady night drizzle",
        "day_icon": "🌧️",
        "night_icon": "🌧️",
        "day_anim": "drizzle",
        "night_anim": "drizzle",
        "bg_day": "rain.jpg",
        "bg_night": "rain_night.jpg"
    },
    55: {
        "weather_type": "drizzle",
        "condition": "Dense Drizzle",
        "day_desc": "Dense continuous drizzle",
        "night_desc": "Dense continuous drizzle",
        "day_icon": "🌧️",
        "night_icon": "🌧️",
        "day_anim": "drizzle",
        "night_anim": "drizzle",
        "bg_day": "rain.jpg",
        "bg_night": "rain_night.jpg"
    },
    56: {
        "weather_type": "drizzle",
        "condition": "Light Freezing Drizzle",
        "day_desc": "Freezing drizzle droplets",
        "night_desc": "Freezing drizzle",
        "day_icon": "🌧️",
        "night_icon": "🌧️",
        "day_anim": "drizzle",
        "night_anim": "drizzle",
        "bg_day": "rain.jpg",
        "bg_night": "rain_night.jpg"
    },
    57: {
        "weather_type": "drizzle",
        "condition": "Dense Freezing Drizzle",
        "day_desc": "Heavy freezing drizzle",
        "night_desc": "Heavy freezing drizzle",
        "day_icon": "🌧️",
        "night_icon": "🌧️",
        "day_anim": "drizzle",
        "night_anim": "drizzle",
        "bg_day": "rain.jpg",
        "bg_night": "rain_night.jpg"
    },
    61: {
        "weather_type": "rain",
        "condition": "Slight Rain",
        "day_desc": "Light rain showers",
        "night_desc": "Light passing rain",
        "day_icon": "🌦️",
        "night_icon": "🌧️",
        "day_anim": "rain",
        "night_anim": "rain",
        "bg_day": "rain.jpg",
        "bg_night": "rain_night.jpg"
    },
    63: {
        "weather_type": "rain",
        "condition": "Moderate Rain",
        "day_desc": "Moderate steady rainfall",
        "night_desc": "Steady rain overnight",
        "day_icon": "🌧️",
        "night_icon": "🌧️",
        "day_anim": "rain",
        "night_anim": "rain",
        "bg_day": "rain.jpg",
        "bg_night": "rain_night.jpg"
    },
    65: {
        "weather_type": "rain",
        "condition": "Heavy Rain",
        "day_desc": "Heavy downpour and rain sheets",
        "night_desc": "Torrential rain overnight",
        "day_icon": "🌧️",
        "night_icon": "🌧️",
        "day_anim": "rain",
        "night_anim": "rain",
        "bg_day": "rain.jpg",
        "bg_night": "rain_night.jpg"
    },
    66: {
        "weather_type": "rain",
        "condition": "Light Freezing Rain",
        "day_desc": "Light freezing rain",
        "night_desc": "Light freezing rain",
        "day_icon": "🌧️",
        "night_icon": "🌧️",
        "day_anim": "rain",
        "night_anim": "rain",
        "bg_day": "rain.jpg",
        "bg_night": "rain_night.jpg"
    },
    67: {
        "weather_type": "rain",
        "condition": "Heavy Freezing Rain",
        "day_desc": "Severe freezing rain",
        "night_desc": "Severe freezing rain",
        "day_icon": "🌧️",
        "night_icon": "🌧️",
        "day_anim": "rain",
        "night_anim": "rain",
        "bg_day": "rain.jpg",
        "bg_night": "rain_night.jpg"
    },
    71: {
        "weather_type": "snow",
        "condition": "Slight Snow Fall",
        "day_desc": "Light snow flurries",
        "night_desc": "Gentle snow flurries",
        "day_icon": "🌨️",
        "night_icon": "🌨️",
        "day_anim": "snow",
        "night_anim": "snow",
        "bg_day": "snow.jpg",
        "bg_night": "snow.jpg"
    },
    73: {
        "weather_type": "snow",
        "condition": "Moderate Snow Fall",
        "day_desc": "Steady snowfall accumulating",
        "night_desc": "Steady snowfall",
        "day_icon": "❄️",
        "night_icon": "❄️",
        "day_anim": "snow",
        "night_anim": "snow",
        "bg_day": "snow.jpg",
        "bg_night": "snow.jpg"
    },
    75: {
        "weather_type": "snow",
        "condition": "Heavy Snow Fall",
        "day_desc": "Heavy blizzard snowstorm",
        "night_desc": "Intense blizzard snow",
        "day_icon": "❄️",
        "night_icon": "❄️",
        "day_anim": "snow",
        "night_anim": "snow",
        "bg_day": "snow.jpg",
        "bg_night": "snow.jpg"
    },
    77: {
        "weather_type": "snow",
        "condition": "Snow Grains",
        "day_desc": "Fine snow grains",
        "night_desc": "Snow grains",
        "day_icon": "🌨️",
        "night_icon": "🌨️",
        "day_anim": "snow",
        "night_anim": "snow",
        "bg_day": "snow.jpg",
        "bg_night": "snow.jpg"
    },
    80: {
        "weather_type": "rain",
        "condition": "Slight Rain Showers",
        "day_desc": "Passing rain showers",
        "night_desc": "Scattered night showers",
        "day_icon": "🌦️",
        "night_icon": "🌧️",
        "day_anim": "rain",
        "night_anim": "rain",
        "bg_day": "rain.jpg",
        "bg_night": "rain_night.jpg"
    },
    81: {
        "weather_type": "rain",
        "condition": "Moderate Rain Showers",
        "day_desc": "Moderate rain showers",
        "night_desc": "Frequent rain showers",
        "day_icon": "🌧️",
        "night_icon": "🌧️",
        "day_anim": "rain",
        "night_anim": "rain",
        "bg_day": "rain.jpg",
        "bg_night": "rain_night.jpg"
    },
    82: {
        "weather_type": "rain",
        "condition": "Violent Rain Showers",
        "day_desc": "Torrential downpours",
        "night_desc": "Violent nocturnal showers",
        "day_icon": "⛈️",
        "night_icon": "⛈️",
        "day_anim": "rain",
        "night_anim": "rain",
        "bg_day": "rain.jpg",
        "bg_night": "rain_night.jpg"
    },
    85: {
        "weather_type": "snow",
        "condition": "Slight Snow Showers",
        "day_desc": "Scattered snow showers",
        "night_desc": "Scattered snow showers",
        "day_icon": "🌨️",
        "night_icon": "🌨️",
        "day_anim": "snow",
        "night_anim": "snow",
        "bg_day": "snow.jpg",
        "bg_night": "snow.jpg"
    },
    86: {
        "weather_type": "snow",
        "condition": "Heavy Snow Showers",
        "day_desc": "Heavy snow squalls",
        "night_desc": "Heavy snow squalls",
        "day_icon": "❄️",
        "night_icon": "❄️",
        "day_anim": "snow",
        "night_anim": "snow",
        "bg_day": "snow.jpg",
        "bg_night": "snow.jpg"
    },
    95: {
        "weather_type": "thunderstorm",
        "condition": "Thunderstorm",
        "day_desc": "Thunderstorms with lightning",
        "night_desc": "Night thunderstorms with lightning",
        "day_icon": "⚡",
        "night_icon": "🌩️",
        "day_anim": "thunderstorm",
        "night_anim": "thunderstorm",
        "bg_day": "thunderstorm.jpg",
        "bg_night": "thunderstorm.jpg"
    },
    96: {
        "weather_type": "thunderstorm",
        "condition": "Thunderstorm with Slight Hail",
        "day_desc": "Thunderstorms with hail",
        "night_desc": "Thunderstorms with hail",
        "day_icon": "⛈️",
        "night_icon": "⛈️",
        "day_anim": "thunderstorm",
        "night_anim": "thunderstorm",
        "bg_day": "thunderstorm.jpg",
        "bg_night": "thunderstorm.jpg"
    },
    99: {
        "weather_type": "thunderstorm",
        "condition": "Thunderstorm with Heavy Hail",
        "day_desc": "Severe thunderstorm with violent hail",
        "night_desc": "Severe nocturnal thunderstorm with hail",
        "day_icon": "⛈️",
        "night_icon": "⛈️",
        "day_anim": "thunderstorm",
        "night_anim": "thunderstorm",
        "bg_day": "thunderstorm.jpg",
        "bg_night": "thunderstorm.jpg"
    }
}

DEFAULT_ENTRY = {
    "weather_type": "partly_cloudy",
    "condition": "Partly Cloudy",
    "day_desc": "Scattered cloud cover",
    "night_desc": "Partly cloudy",
    "day_icon": "🌤️",
    "night_icon": "🌙",
    "day_anim": "clouds",
    "night_anim": "clouds",
    "bg_day": "partly_cloudy.jpg",
    "bg_night": "clear_night.jpg"
}

# ============================================================================
# 2. Time Phase Determination
# ============================================================================
def calculate_time_phase(local_dt: datetime.datetime,
                         sunrise_dt: Optional[datetime.datetime],
                         sunset_dt: Optional[datetime.datetime]) -> str:
    """
    Calculate the city's local solar time phase:
    - dawn: 45 min around sunrise (from 30 min before to 15 min after sunrise)
    - day: between sunrise and golden hour
    - evening: golden hour (from 60 min before sunset to 30 min after sunset)
    - dusk: after sunset until full dark (from 30 min to 90 min after sunset)
    - night: all other hours (astronomical night)
    """
    if not sunrise_dt or not sunset_dt:
        # Fallback based on hour of day
        h = local_dt.hour
        if 5 <= h < 7:
            return "dawn"
        elif 7 <= h < 17:
            return "day"
        elif 17 <= h < 19:
            return "evening"
        elif 19 <= h < 21:
            return "dusk"
        else:
            return "night"

    # Normalize dates to compare timestamps on same day
    t = local_dt.time()
    sr = sunrise_dt.time()
    ss = sunset_dt.time()

    t_sec = t.hour * 3600 + t.minute * 60 + t.second
    sr_sec = sr.hour * 3600 + sr.minute * 60 + sr.second
    ss_sec = ss.hour * 3600 + ss.minute * 60 + ss.second

    # Dawn: 30m before sunrise to 15m after sunrise
    if (sr_sec - 1800) <= t_sec <= (sr_sec + 900):
        return "dawn"
    # Day: after dawn up to 60m before sunset
    elif (sr_sec + 900) < t_sec < (ss_sec - 3600):
        return "day"
    # Evening (Golden Hour): 60m before sunset to 30m after sunset
    elif (ss_sec - 3600) <= t_sec <= (ss_sec + 1800):
        return "evening"
    # Dusk: 30m to 90m after sunset
    elif (ss_sec + 1800) < t_sec <= (ss_sec + 5400):
        return "dusk"
    # Night
    else:
        return "night"

# ============================================================================
# 3. Dynamic Atmospheric Themes Matrix (Weather Type x Time Phase)
# ============================================================================
# Color palettes and procedural gradients used as high-fidelity fallbacks
# if user sky wallpapers are not present in desktop/assets/backgrounds/.
TIME_PHASE_TINTS = {
    "dawn": {
        "rgba": (255, 182, 193, 40),       # Soft rose-pink coral tint
        "css_overlay": "rgba(255, 182, 193, 0.16)",
        "accent": "#F472B6",
        "description_prefix": "Dawn"
    },
    "day": {
        "rgba": (255, 255, 255, 0),         # Natural daylight
        "css_overlay": "rgba(255, 255, 255, 0)",
        "accent": "#38BDF8",
        "description_prefix": "Day"
    },
    "evening": {
        "rgba": (255, 154, 60, 50),        # Warm golden amber hour
        "css_overlay": "rgba(255, 154, 60, 0.20)",
        "accent": "#F59E0B",
        "description_prefix": "Golden Hour"
    },
    "dusk": {
        "rgba": (138, 43, 226, 45),         # Twilight deep purple
        "css_overlay": "rgba(138, 43, 226, 0.18)",
        "accent": "#C084FC",
        "description_prefix": "Dusk"
    },
    "night": {
        "rgba": (15, 23, 42, 65),          # Midnight deep navy
        "css_overlay": "rgba(15, 23, 42, 0.28)",
        "accent": "#60A5FA",
        "description_prefix": "Night"
    },
    "frost": {
        "rgba": (224, 242, 254, 50),       # Cool crisp blue-white frost tint (<5°C)
        "css_overlay": "rgba(224, 242, 254, 0.22)",
        "accent": "#BAE6FD",
        "description_prefix": "Frost"
    }
}

PROCEDURAL_GRADIENTS = {
    "clear_day": ((30, 80, 160), (230, 150, 60)),
    "clear_dawn": ((45, 35, 80), (255, 160, 140)),
    "clear_evening": ((25, 40, 95), (245, 140, 45)),
    "clear_dusk": ((20, 15, 45), (105, 45, 115)),
    "clear_night": ((8, 12, 28), (20, 36, 72)),

    "partly_cloudy_day": ((35, 60, 105), (85, 145, 195)),
    "partly_cloudy_dawn": ((40, 45, 85), (210, 140, 150)),
    "partly_cloudy_evening": ((30, 45, 85), (220, 130, 70)),
    "partly_cloudy_dusk": ((22, 20, 50), (80, 50, 90)),
    "partly_cloudy_night": ((10, 16, 32), (25, 36, 56)),

    "overcast_day": ((45, 55, 68), (95, 108, 122)),
    "overcast_dawn": ((40, 42, 58), (115, 105, 115)),
    "overcast_evening": ((42, 45, 60), (120, 95, 80)),
    "overcast_dusk": ((25, 26, 38), (55, 50, 65)),
    "overcast_night": ((14, 18, 26), (32, 40, 50)),

    "fog_day": ((55, 65, 75), (120, 130, 140)),
    "fog_dawn": ((50, 48, 65), (140, 125, 130)),
    "fog_evening": ((50, 52, 65), (145, 120, 105)),
    "fog_dusk": ((28, 28, 38), (65, 60, 75)),
    "fog_night": ((18, 22, 28), (42, 48, 56)),

    "drizzle_day": ((26, 46, 72), (65, 110, 150)),
    "drizzle_night": ((12, 20, 35), (28, 48, 70)),

    "rain_day": ((20, 34, 56), (42, 75, 110)),
    "rain_night": ((10, 18, 32), (24, 42, 65)),

    "thunderstorm_day": ((20, 15, 45), (55, 32, 90)),
    "thunderstorm_night": ((12, 10, 30), (36, 20, 60)),

    "snow_day": ((25, 42, 65), (95, 135, 175)),
    "snow_night": ((15, 24, 38), (42, 68, 96))
}

# ============================================================================
# 4. Main Resolution Engine
# ============================================================================
def resolve_theme(wmo_code: int,
                  is_day: int = 1,
                  temp_c: float = 20.0,
                  local_time_dt: Optional[datetime.datetime] = None,
                  sunrise_dt: Optional[datetime.datetime] = None,
                  sunset_dt: Optional[datetime.datetime] = None,
                  forced_theme: Optional[str] = None) -> Dict[str, Any]:
    """
    Given the weather code, temperature, and local solar timings, determines:
    - Current time phase (dawn, day, evening, dusk, night)
    - Applied wallpaper filename
    - Color tint and opacity
    - Readability overlay flag
    - Animation type
    - Procedural gradient colors for Canvas fallback
    """
    entry = WMO_CODES.get(wmo_code, DEFAULT_ENTRY)
    w_type = entry["weather_type"]

    # 1. Calculate time phase
    if forced_theme:
        # Hidden preview mode (e.g. forced via F2 or ?theme=rain-night)
        parts = forced_theme.lower().split("-")
        phase = parts[1] if len(parts) > 1 else ("night" if not is_day else "day")
        if parts[0] in ["clear", "partly_cloudy", "overcast", "fog", "drizzle", "rain", "thunderstorm", "snow"]:
            w_type = parts[0]
    elif local_time_dt:
        phase = calculate_time_phase(local_time_dt, sunrise_dt, sunset_dt)
    else:
        phase = "day" if is_day == 1 else "night"

    is_night_phase = phase in ("night", "dusk")

    # 2. Check for Frost condition on cold clear days
    is_frost = (w_type == "clear" and temp_c < 5.0 and phase in ("day", "dawn"))

    # 3. Resolve background wallpaper file
    if is_night_phase:
        bg_file = entry["bg_night"]
        icon = entry["night_icon"]
        desc = entry["night_desc"]
        anim = entry["night_anim"]
    else:
        bg_file = entry["bg_day"]
        icon = entry["day_icon"]
        desc = entry["day_desc"]
        anim = entry["day_anim"]

    # 4. Resolve Tint
    tint_info = TIME_PHASE_TINTS["frost"] if is_frost else TIME_PHASE_TINTS.get(phase, TIME_PHASE_TINTS["day"])

    # 5. Resolve Procedural Gradient Fallback
    grad_key = f"{w_type}_{phase}"
    gradient = PROCEDURAL_GRADIENTS.get(grad_key)
    if not gradient:
        # Secondary fallback
        grad_key_day = f"{w_type}_night" if is_night_phase else f"{w_type}_day"
        gradient = PROCEDURAL_GRADIENTS.get(grad_key_day, ((25, 42, 86), (30, 41, 59)))

    # Theme CSS class name (e.g. 'theme-clear-evening', 'theme-rain-night')
    theme_key = f"{w_type}_{phase}"
    css_class = f"theme-{w_type.replace('_', '-')}-{phase}"

    return {
        "wmo_code": wmo_code,
        "weather_type": w_type,
        "time_phase": phase,
        "theme_key": theme_key,
        "css_class": css_class,
        "condition": entry["condition"],
        "description": desc,
        "icon": icon,
        "animation": anim,
        "bg_filename": bg_file,
        "tint_rgba": tint_info["rgba"],
        "css_overlay": tint_info["css_overlay"],
        "accent": tint_info["accent"],
        "gradient_top": gradient[0],
        "gradient_bottom": gradient[1],
        "text_primary": "#FFFFFF",
        "text_secondary": "#E2E8F0" if is_night_phase else "#F8FAFC",
        "text_muted": "#94A3B8",
        "glass_tint_opacity": 0.18,
        "readability_overlay": True if phase in ("day", "evening", "dawn") else False
    }

# ============================================================================
# 5. Metric Scale Helpers (AQI & UV)
# ============================================================================
def get_weather_info(code: int, is_day: int = 1) -> Dict[str, Any]:
    """Compatibility helper returning resolved theme dictionary."""
    return resolve_theme(wmo_code=code, is_day=is_day)

def get_aqi_level(european_aqi: Optional[float]) -> Dict[str, Any]:
    """European Air Quality Index (AQI) scale."""
    val = round(float(european_aqi or 0))
    if val <= 20:
        return {"val": val, "label": "Good", "color": "#10B981"}
    elif val <= 40:
        return {"val": val, "label": "Fair", "color": "#FBBF24"}
    elif val <= 60:
        return {"val": val, "label": "Moderate", "color": "#F97316"}
    elif val <= 80:
        return {"val": val, "label": "Poor", "color": "#EF4444"}
    elif val <= 100:
        return {"val": val, "label": "Very Poor", "color": "#A855F7"}
    else:
        return {"val": val, "label": "Hazardous", "color": "#881337"}

def get_uv_level(uv_val: Optional[float]) -> Dict[str, Any]:
    """WHO UV Index categories."""
    val = round(float(uv_val or 0), 1)
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
