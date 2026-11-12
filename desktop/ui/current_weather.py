"""
SkyCast Desktop UI — Current Weather Hero Component
---------------------------------------------------
Renders the prominent current conditions hero card:
- City name, country, and local time
- Favorite bookmark button (⭐)
- Large weather condition icon & current temperature
- Condition description & feels-like temperature
- Wind speed & direction, pressure, humidity summary
- 'Last updated X min ago' indicator with manual refresh trigger
"""

import tkinter as tk
import datetime
from typing import Dict, Any, Callable
from shared.weather_codes import get_weather_info
from desktop.ui.panels import create_glass_card

class CurrentWeatherCard:
    def __init__(self, canvas: tk.Canvas, on_toggle_favorite: Callable[[], None], on_refresh: Callable[[], None]):
        self.canvas = canvas
        self.on_toggle_favorite = on_toggle_favorite
        self.on_refresh = on_refresh

    def draw(self, x: int, y: int, width: int, height: int,
             city_info: Dict[str, Any],
             weather_data: Dict[str, Any],
             theme: Dict[str, Any],
             units: Dict[str, str],
             is_fav: bool,
             last_updated_time: float,
             is_offline: bool,
             fonts: Dict[str, Any]):
        """Render the primary hero weather card."""
        card_img = create_glass_card(width, height, radius=20,
                                     fill_rgba=theme.get("glass_fill", (255, 255, 255, 28)),
                                     border_rgba=theme.get("glass_border", (255, 255, 255, 75)))
        self.canvas.create_image(x, y, image=card_img, anchor="nw", tags="ui_element")

        if not weather_data or "current" not in weather_data:
            self.canvas.create_text(
                x + width // 2, y + height // 2,
                text="Loading live weather data...",
                font=fonts["h2"],
                fill=theme["text_primary"],
                tags="ui_element"
            )
            return

        curr = weather_data.get("current", {})
        code = curr.get("weather_code", 0)
        is_day = curr.get("is_day", 1)
        w_info = get_weather_info(code, is_day)

        city_name = city_info.get("name", "London")
        country = city_info.get("country", "")

        # 1. City Name & Favorite Star
        self.canvas.create_text(
            x + 28, y + 36,
            text=f"📍 {city_name}",
            font=fonts["title"],
            fill=theme["text_primary"],
            anchor="w",
            tags="ui_element"
        )

        star_tag = "btn_favorite_star"
        star_icon = "★" if is_fav else "☆"
        star_col = "#F1C40F" if is_fav else theme["text_muted"]
        self.canvas.create_text(
            x + 28 + len(city_name) * 16 + 45, y + 36,
            text=star_icon,
            font=("Segoe UI", 18, "bold"),
            fill=star_col,
            anchor="w",
            tags=("ui_element", star_tag)
        )
        self.canvas.tag_bind(star_tag, "<Button-1>", lambda e: self.on_toggle_favorite())

        # 2. Local Time of searched city
        # Calculate local time based on UTC offset or ISO timestamp
        curr_time_str = curr.get("time", "")
        try:
            dt = datetime.datetime.fromisoformat(curr_time_str)
            local_time_display = dt.strftime("%A, %d %B • %I:%M %p")
        except Exception:
            local_time_display = datetime.datetime.now().strftime("%A, %d %B • %I:%M %p")

        location_sub = f"{country}  •  Local Time: {local_time_display}" if country else f"Local Time: {local_time_display}"
        self.canvas.create_text(
            x + 28, y + 68,
            text=location_sub,
            font=fonts["subtitle"],
            fill=theme["text_secondary"],
            anchor="w",
            tags="ui_element"
        )

        # 3. Weather Icon & Large Temperature
        temp_unit = units.get("temp", "celsius")
        temp_sym = "°F" if temp_unit == "fahrenheit" else "°C"
        temp_val = round(curr.get("temperature_2m", 0))

        self.canvas.create_text(
            x + 28, y + 138,
            text=w_info["icon"],
            font=fonts["icon_large"],
            anchor="w",
            tags="ui_element"
        )

        self.canvas.create_text(
            x + 135, y + 138,
            text=f"{temp_val}{temp_sym}",
            font=fonts["temp_large"],
            fill=theme["text_primary"],
            anchor="w",
            tags="ui_element"
        )

        # 4. Weather Condition Description & Feels Like
        feels = round(curr.get("apparent_temperature", 0))
        self.canvas.create_text(
            x + 28, y + 210,
            text=f"{w_info['condition']} — {w_info['description']}",
            font=fonts["h2"],
            fill=theme["accent"],
            anchor="w",
            tags="ui_element"
        )

        self.canvas.create_text(
            x + 28, y + 236,
            text=f"Feels like {feels}{temp_sym}",
            font=fonts["subtitle"],
            fill=theme["text_secondary"],
            anchor="w",
            tags="ui_element"
        )

        # 5. Last updated & Refresh indicator
        import time
        elapsed_sec = int(time.time() - last_updated_time)
        elapsed_min = max(elapsed_sec // 60, 0)
        time_text = "Updated just now" if elapsed_min < 1 else f"Updated {elapsed_min} min ago"

        if is_offline:
            status_text = f"⚠️ No connection - showing last saved data ({time_text})"
            status_col = "#F87171"
        else:
            status_text = f"● Live  •  {time_text}"
            status_col = "#34D399"

        self.canvas.create_text(
            x + 28, y + height - 20,
            text=status_text,
            font=("Segoe UI", 9),
            fill=status_col,
            anchor="w",
            tags="ui_element"
        )

        # Manual Refresh button
        refresh_tag = "btn_manual_refresh"
        self.canvas.create_text(
            x + width - 28, y + height - 20,
            text="🔄 Refresh",
            font=("Segoe UI", 9, "bold"),
            fill=theme["accent"],
            anchor="e",
            tags=("ui_element", refresh_tag)
        )
        self.canvas.tag_bind(refresh_tag, "<Button-1>", lambda e: self.on_refresh())
