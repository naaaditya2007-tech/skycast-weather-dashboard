"""
SkyCast Desktop UI — Extra Weather Detail Grid Component
--------------------------------------------------------
Renders 6 to 8 glass tiles on the Canvas:
1. UV Index (with WHO level and color label)
2. Air Quality Index (AQI with European scale color label)
3. Visibility (converted to km or miles)
4. Cloud Cover (%)
5. Dew Point (with unit toggle support)
6. Sunrise & Sunset times (formatted to local time)
7. Humidity (%)
8. Wind & Pressure
"""

import tkinter as tk
from typing import Dict, Any, List, Tuple
from shared.weather_codes import get_aqi_level, get_uv_level
from desktop.ui.panels import create_glass_card

class DetailsGrid:
    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas

    def draw(self, x: int, y: int, width: int, height: int,
             weather_data: Dict[str, Any],
             theme: Dict[str, Any],
             units: Dict[str, str],
             font_title: Any,
             font_value: Any,
             font_label: Any,
             font_badge: Any):
        """Draw the grid of weather metric tiles within the designated bounds."""
        if not weather_data or "current" not in weather_data:
            return

        curr = weather_data.get("current", {})
        daily = weather_data.get("daily", {})
        aqi_info = weather_data.get("air_quality", {})

        temp_unit = units.get("temp", "celsius")
        temp_sym = "°F" if temp_unit == "fahrenheit" else "°C"
        press_unit = units.get("pressure", "hPa")

        # 1. UV Index
        uv_val = curr.get("uv_index", 0.0)
        uv_info = get_uv_level(uv_val)

        # 2. Air Quality
        aqi_val = aqi_info.get("european_aqi", None)
        aqi_status = get_aqi_level(aqi_val) if aqi_val is not None else {"val": "--", "label": "N/A", "color": "#94A3B8"}

        # 3. Visibility
        vis_meters = curr.get("visibility", 10000)
        vis_str = f"{round(vis_meters / 1000, 1)} km" if temp_unit == "celsius" else f"{round(vis_meters / 1609.34, 1)} mi"

        # 4. Cloud Cover
        cloud_pct = f"{curr.get('cloud_cover', '--')}%"

        # 5. Dew Point
        dew_pt = curr.get("dew_point_2m", "--")
        dew_str = f"{round(dew_pt)}{temp_sym}" if isinstance(dew_pt, (int, float)) else "--"

        # 6. Sunrise & Sunset
        sunrises = daily.get("sunrise", [])
        sunsets = daily.get("sunset", [])
        sunrise_str = sunrises[0].split("T")[1] if sunrises else "--:--"
        sunset_str = sunsets[0].split("T")[1] if sunsets else "--:--"
        sun_str = f"🌅 {sunrise_str}  •  🌇 {sunset_str}"

        # 7. Pressure
        hpa_val = curr.get("surface_pressure", 1013)
        if press_unit == "inHg":
            press_str = f"{round(hpa_val * 0.02953, 2)} inHg"
        else:
            press_str = f"{round(hpa_val)} hPa"

        # 8. Humidity
        hum_str = f"{curr.get('relative_humidity_2m', '--')}%"

        # 6 Tiles in a 3 columns x 2 rows layout
        tiles = [
            {"icon": "☀️", "label": "UV INDEX", "value": f"{uv_info['val']} - {uv_info['label']}", "color": uv_info["color"]},
            {"icon": "🍃", "label": "AIR QUALITY", "value": f"AQI {aqi_status['val']} ({aqi_status['label']})", "color": aqi_status["color"]},
            {"icon": "👁️", "label": "VISIBILITY", "value": vis_str, "color": theme["text_primary"]},
            {"icon": "☁️", "label": "CLOUD COVER", "value": cloud_pct, "color": theme["text_primary"]},
            {"icon": "🌡️", "label": "DEW POINT", "value": dew_str, "color": theme["text_primary"]},
            {"icon": "🌅", "label": "SUNRISE / SUNSET", "value": sun_str, "color": theme["accent"]},
        ]

        cols = 3
        rows = 2
        gap = 10
        card_w = (width - gap * (cols - 1)) // cols
        card_h = (height - gap * (rows - 1)) // rows

        for idx, t in enumerate(tiles):
            c = idx % cols
            r = idx // cols
            tx = x + c * (card_w + gap)
            ty = y + r * (card_h + gap)

            card_img = create_glass_card(card_w, card_h, radius=12,
                                         fill_rgba=theme.get("card_fill", (255, 255, 255, 18)),
                                         border_rgba=theme.get("card_border", (255, 255, 255, 50)))
            self.canvas.create_image(tx, ty, image=card_img, anchor="nw", tags="ui_element")

            # Header row: Icon & Label
            self.canvas.create_text(
                tx + 14, ty + 18,
                text=f"{t['icon']}  {t['label']}",
                font=font_label,
                fill=theme["text_muted"],
                anchor="w",
                tags="ui_element"
            )

            # Value with highlight color
            self.canvas.create_text(
                tx + 14, ty + card_h - 18,
                text=t["value"],
                font=font_value,
                fill=t["color"],
                anchor="w",
                tags="ui_element"
            )
