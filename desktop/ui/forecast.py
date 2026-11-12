"""
SkyCast Desktop UI — Forecast & 24-Hour Trend Line Chart Component
------------------------------------------------------------------
Draws:
1. 24-Hour Temperature Trend Chart directly on the Tkinter Canvas with smooth
   connecting line segments, data point dots, and precipitation probabilities.
2. 7-Day Outlook list with daily condition icons, high/low bars, and rain chances.
"""

import tkinter as tk
import datetime
from typing import Dict, Any, List
from shared.weather_codes import get_weather_info
from desktop.ui.panels import create_glass_card

class ForecastView:
    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas

    def draw_trend_chart(self, x: int, y: int, width: int, height: int,
                         weather_data: Dict[str, Any],
                         theme: Dict[str, Any],
                         temp_symbol: str,
                         font_title: Any,
                         font_small: Any,
                         font_bold: Any):
        """Draw 24-hour temperature trend line chart with rain probability labels."""
        card_img = create_glass_card(width, height, radius=16,
                                     fill_rgba=theme.get("card_fill", (255, 255, 255, 18)),
                                     border_rgba=theme.get("card_border", (255, 255, 255, 55)))
        self.canvas.create_image(x, y, image=card_img, anchor="nw", tags="ui_element")

        # Title
        self.canvas.create_text(
            x + 18, y + 20,
            text="📈 24-Hour Temperature Trend & Rain Chance",
            font=font_title,
            fill=theme["text_primary"],
            anchor="w",
            tags="ui_element"
        )

        hourly = weather_data.get("hourly", {})
        times = hourly.get("time", [])[:24]
        temps = hourly.get("temperature_2m", [])[:24]
        rain_chances = hourly.get("precipitation_probability", [])[:24]
        weather_codes = hourly.get("weather_code", [])[:24]
        is_days = hourly.get("is_day", [])[:24]

        if not times or not temps:
            return

        # Select 8 evenly spaced checkpoints for chart labels
        step = max(len(times) // 8, 1)
        checkpoints = list(range(0, len(times), step))[:8]

        min_t = min(temps)
        max_t = max(temps)
        t_range = max(max_t - min_t, 1.0)

        chart_top = y + 55
        chart_bottom = y + height - 50
        chart_height = chart_bottom - chart_top
        chart_left = x + 35
        chart_right = x + width - 35
        chart_width = chart_right - chart_left

        points = []
        for i, idx in enumerate(checkpoints):
            t_val = temps[idx]
            px = chart_left + (i / (len(checkpoints) - 1)) * chart_width
            norm = (t_val - min_t) / t_range
            py = chart_bottom - norm * chart_height
            points.append((px, py, idx))

        # Draw connecting line segments with glowing accent
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            # Shadow line
            self.canvas.create_line(p1[0], p1[1] + 2, p2[0], p2[1] + 2,
                                    fill="#000000", width=3, stipple="gray25", tags="ui_element")
            # Accent line
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1],
                                    fill=theme["accent"], width=3, tags="ui_element")

        # Draw point markers, temperature labels, and rain chances
        for px, py, idx in points:
            t_val = round(temps[idx])
            t_time = times[idx]
            rain_p = rain_chances[idx] if idx < len(rain_chances) and rain_chances[idx] is not None else 0
            code = weather_codes[idx] if idx < len(weather_codes) else 0
            is_d = is_days[idx] if idx < len(is_days) else 1
            info = get_weather_info(code, is_d)

            # Format hour string (e.g. "3 PM")
            try:
                dt = datetime.datetime.fromisoformat(t_time)
                time_label = dt.strftime("%I %p").lstrip("0")
            except Exception:
                time_label = f"+{idx}h"

            # Outer ring & dot
            self.canvas.create_oval(px - 5, py - 5, px + 5, py + 5, fill=theme["accent"], outline="#FFFFFF", width=1, tags="ui_element")

            # Temp label above dot
            self.canvas.create_text(px, py - 14, text=f"{t_val}{temp_symbol}", font=font_bold, fill=theme["text_primary"], tags="ui_element")

            # Weather icon
            self.canvas.create_text(px, chart_bottom + 14, text=info["icon"], font=("Segoe UI Emoji", 11), tags="ui_element")

            # Time label below
            self.canvas.create_text(px, chart_bottom + 28, text=time_label, font=font_small, fill=theme["text_muted"], tags="ui_element")

            # Rain probability badge
            rain_col = "#7DD3FC" if rain_p > 0 else theme["text_muted"]
            self.canvas.create_text(px, chart_bottom + 42, text=f"💧{rain_p}%", font=font_small, fill=rain_col, tags="ui_element")

    def draw_7day_forecast(self, x: int, y: int, width: int, height: int,
                           weather_data: Dict[str, Any],
                           theme: Dict[str, Any],
                           temp_symbol: str,
                           font_title: Any,
                           font_body: Any,
                           font_bold: Any):
        """Draw 7-day extended forecast card."""
        card_img = create_glass_card(width, height, radius=18,
                                     fill_rgba=theme.get("glass_fill", (255, 255, 255, 25)),
                                     border_rgba=theme.get("glass_border", (255, 255, 255, 65)))
        self.canvas.create_image(x, y, image=card_img, anchor="nw", tags="ui_element")

        self.canvas.create_text(
            x + 22, y + 24,
            text="📅 7-Day Extended Forecast",
            font=font_title,
            fill=theme["text_primary"],
            anchor="w",
            tags="ui_element"
        )

        daily = weather_data.get("daily", {})
        dates = daily.get("time", [])[:7]
        max_temps = daily.get("temperature_2m_max", [])[:7]
        min_temps = daily.get("temperature_2m_min", [])[:7]
        codes = daily.get("weather_code", [])[:7]
        precips = daily.get("precipitation_probability_max", [])[:7]

        if not dates:
            return

        row_h = (height - 65) // max(len(dates), 1)

        for i, d_str in enumerate(dates):
            try:
                dt = datetime.date.fromisoformat(d_str)
                day_name = "Today" if i == 0 else dt.strftime("%A")
                date_label = dt.strftime("%b %d")
            except Exception:
                day_name = f"Day {i+1}"
                date_label = ""

            code = codes[i] if i < len(codes) else 0
            info = get_weather_info(code, 1)
            high_t = round(max_temps[i]) if i < len(max_temps) else "--"
            low_t = round(min_temps[i]) if i < len(min_temps) else "--"
            rain_val = precips[i] if i < len(precips) and precips[i] is not None else 0

            ry = y + 55 + i * row_h

            # Subtle glass row background
            row_bg = create_glass_card(width - 32, row_h - 6, radius=10,
                                       fill_rgba=(255, 255, 255, 12),
                                       border_rgba=(255, 255, 255, 30))
            self.canvas.create_image(x + 16, ry, image=row_bg, anchor="nw", tags="ui_element")

            # Day name & Date
            self.canvas.create_text(x + 30, ry + (row_h - 6) // 2 - 8, text=day_name, font=font_bold, fill=theme["text_primary"], anchor="w", tags="ui_element")
            self.canvas.create_text(x + 30, ry + (row_h - 6) // 2 + 10, text=date_label, font=("Segoe UI", 8), fill=theme["text_muted"], anchor="w", tags="ui_element")

            # Icon & Condition
            self.canvas.create_text(x + int(width * 0.36), ry + (row_h - 6) // 2, text=f"{info['icon']}  {info['condition']}", font=font_body, fill=theme["text_primary"], anchor="w", tags="ui_element")

            # Rain probability badge
            self.canvas.create_text(x + int(width * 0.65), ry + (row_h - 6) // 2, text=f"💧 {rain_val}%", font=font_body, fill="#7DD3FC", anchor="w", tags="ui_element")

            # High / Low temperatures
            self.canvas.create_text(x + width - 30, ry + (row_h - 6) // 2, text=f"{high_t}{temp_symbol} / {low_t}{temp_symbol}", font=font_bold, fill=theme["text_primary"], anchor="e", tags="ui_element")
