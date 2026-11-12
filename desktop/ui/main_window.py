"""
Main Tkinter Window for SkyCast Desktop.
Provides glassmorphism layout, live weather display, hourly & 7-day forecast cards,
search autocomplete, unit toggle, and particle animation hooks.
"""

import tkinter as tk
from tkinter import font as tkfont
import datetime
from typing import Optional, Dict, Any, List

from shared.weather_codes import get_weather_info
from desktop.api_client import WeatherApiClient
from desktop.ui.theme import get_theme, DEFAULT_THEME
from desktop.ui.panels import get_gradient_image, create_glass_card
from desktop.ui.animations import WeatherAnimator

class SkyCastApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("SkyCast — Real-Time Weather Application")
        self.geometry("1120x760")
        self.minsize(920, 640)

        # State
        self.api_client = WeatherApiClient()
        self.is_fahrenheit = False
        self.current_city = "London"
        self.current_country = "United Kingdom"
        self.current_lat = 51.5074
        self.current_lon = -0.1278
        self.weather_data: Optional[Dict[str, Any]] = None
        self.current_theme = DEFAULT_THEME
        self.search_debounce_id = None
        self.resize_debounce_id = None

        # Build UI
        self._setup_ui()

        # Initialize Animator
        self.animator = WeatherAnimator(self.canvas)

        # Bind resize event
        self.bind("<Configure>", self._on_resize)
        self.bind("<Return>", lambda e: self._on_search_submit())

        # Load initial city weather
        self.after(200, lambda: self.load_weather(self.current_lat, self.current_lon, self.current_city, self.current_country))

    def _setup_ui(self):
        # Configure fonts
        self.font_logo = tkfont.Font(family="Segoe UI", size=18, weight="bold")
        self.font_title = tkfont.Font(family="Segoe UI", size=24, weight="bold")
        self.font_subtitle = tkfont.Font(family="Segoe UI", size=11)
        self.font_temp = tkfont.Font(family="Segoe UI", size=54, weight="bold")
        self.font_h2 = tkfont.Font(family="Segoe UI", size=14, weight="bold")
        self.font_body = tkfont.Font(family="Segoe UI", size=10)
        self.font_body_bold = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        self.font_icon_large = tkfont.Font(family="Segoe UI Emoji", size=48)
        self.font_icon_mid = tkfont.Font(family="Segoe UI Emoji", size=20)
        self.font_icon_small = tkfont.Font(family="Segoe UI Emoji", size=14)

        # Root Canvas that fills entire window
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.canvas.pack(fill="both", expand=True)

        # Search Entry Widget overlaid on top
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_text_changed)

        self.search_entry = tk.Entry(
            self.canvas,
            textvariable=self.search_var,
            font=("Segoe UI", 11),
            bg="#1E293B",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            relief="flat",
            highlightthickness=1,
            highlightcolor="#38BDF8",
            highlightbackground="#475569"
        )

        # Search suggestions popup listbox
        self.suggest_box = tk.Listbox(
            self.canvas,
            font=("Segoe UI", 10),
            bg="#0F172A",
            fg="#F1F5F9",
            selectbackground="#2563EB",
            selectforeground="#FFFFFF",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#38BDF8",
            activestyle="none"
        )
        self.suggest_box.bind("<<ListboxSelect>>", self._on_select_suggestion)

        # Status text tag
        self.status_message = "Ready"

    def _on_resize(self, event):
        # Only handle window resize (not child widgets)
        if event.widget == self:
            if self.resize_debounce_id:
                self.after_cancel(self.resize_debounce_id)
            self.resize_debounce_id = self.after(100, self._redraw_all)

    def _redraw_all(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100 or h < 100:
            return

        self.canvas.delete("ui_element")
        self.canvas.delete("bg_gradient")

        # 1. Background gradient
        grad_img = get_gradient_image(
            w, h,
            self.current_theme["gradient_top"],
            self.current_theme["gradient_bottom"]
        )
        self.canvas.create_image(0, 0, image=grad_img, anchor="nw", tags="bg_gradient")

        # 2. Top Header & Navigation Bar
        self._draw_header(w)

        # 3. Main Weather View (Hero + 4 Metric Cards)
        self._draw_hero_panel(w, h)

        # 4. Hourly Forecast Slider / Panel
        self._draw_hourly_forecast(w, h)

        # 5. 7-Day Forecast Panel
        self._draw_daily_forecast(w, h)

        # 6. Status Message
        self.canvas.create_text(
            30, h - 20,
            text=f"✦ Status: {self.status_message}  |  Data provided by Open-Meteo",
            font=self.font_body,
            fill="#94A3B8",
            anchor="w",
            tags="ui_element"
        )

    def _draw_header(self, w: int):
        # Logo and Title
        self.canvas.create_text(
            30, 36,
            text="✦ SKYCAST",
            font=self.font_logo,
            fill=self.current_theme["text_primary"],
            anchor="w",
            tags="ui_element"
        )
        self.canvas.create_text(
            170, 38,
            text="Real-Time Weather Intelligence",
            font=self.font_subtitle,
            fill=self.current_theme["text_secondary"],
            anchor="w",
            tags="ui_element"
        )

        # Search Bar Entry placement
        entry_w = min(max(int(w * 0.28), 220), 320)
        entry_x = w - entry_w - 240
        self.canvas.create_window(entry_x, 38, window=self.search_entry, width=entry_w, height=34, tags="ui_element")

        # Search Button (🔍)
        search_btn_x = entry_x + entry_w // 2 + 30
        self._draw_button(
            x=search_btn_x, y=21, w=75, h=34,
            text="Search",
            bg_color="#2563EB",
            fg_color="#FFFFFF",
            callback=self._on_search_submit
        )

        # Unit Toggle Button (°C / °F)
        unit_btn_x = search_btn_x + 85
        unit_text = "°F" if self.is_fahrenheit else "°C"
        toggle_label = f"Unit: {unit_text}"
        self._draw_button(
            x=unit_btn_x, y=21, w=90, h=34,
            text=toggle_label,
            bg_color="#334155",
            fg_color="#F8FAFC",
            callback=self._toggle_units
        )

    def _draw_button(self, x: int, y: int, w: int, h: int, text: str, bg_color: str, fg_color: str, callback):
        tag_btn = f"btn_{x}_{y}"
        # Button Card
        card = create_glass_card(w, h, radius=8, fill_rgba=(30, 41, 59, 220), border_rgba=(148, 163, 184, 120))
        self.canvas.create_image(x, y, image=card, anchor="nw", tags=("ui_element", tag_btn))
        self.canvas.create_text(
            x + w // 2, y + h // 2,
            text=text,
            font=self.font_body_bold,
            fill=fg_color,
            tags=("ui_element", tag_btn)
        )
        self.canvas.tag_bind(tag_btn, "<Button-1>", lambda e: callback())
        self.canvas.tag_bind(tag_btn, "<Enter>", lambda e: self.config(cursor="hand2"))
        self.canvas.tag_bind(tag_btn, "<Leave>", lambda e: self.config(cursor=""))

    def _draw_hero_panel(self, w: int, h: int):
        left_w = int(w * 0.44)
        hero_h = int(h * 0.50)
        x = 30
        y = 75

        # Glass Panel
        card = create_glass_card(left_w, hero_h, radius=20, fill_rgba=self.current_theme["glass_fill"], border_rgba=self.current_theme["glass_border"])
        self.canvas.create_image(x, y, image=card, anchor="nw", tags="ui_element")

        if not self.weather_data or "current" not in self.weather_data:
            self.canvas.create_text(
                x + left_w // 2, y + hero_h // 2,
                text="Loading live weather...",
                font=self.font_h2,
                fill=self.current_theme["text_primary"],
                tags="ui_element"
            )
            return

        curr = self.weather_data["current"]
        w_code = curr.get("weather_code", 0)
        is_day = curr.get("is_day", 1)
        w_info = get_weather_info(w_code, is_day)

        # Location title
        self.canvas.create_text(
            x + 25, y + 35,
            text=f"📍 {self.current_city}",
            font=self.font_title,
            fill=self.current_theme["text_primary"],
            anchor="w",
            tags="ui_element"
        )
        now_str = datetime.datetime.now().strftime("%A, %d %B • %I:%M %p")
        self.canvas.create_text(
            x + 25, y + 68,
            text=f"{self.current_country}  |  {now_str}",
            font=self.font_subtitle,
            fill=self.current_theme["text_secondary"],
            anchor="w",
            tags="ui_element"
        )

        # Big Weather Icon & Temperature
        icon_str = w_info["icon"]
        temp_val = curr.get("temperature_2m", "--")
        unit_symbol = "°F" if self.is_fahrenheit else "°C"

        self.canvas.create_text(
            x + 30, y + 140,
            text=icon_str,
            font=self.font_icon_large,
            anchor="w",
            tags="ui_element"
        )
        self.canvas.create_text(
            x + 130, y + 140,
            text=f"{round(temp_val)}{unit_symbol}",
            font=self.font_temp,
            fill=self.current_theme["text_primary"],
            anchor="w",
            tags="ui_element"
        )

        # Condition Description & Feels Like
        feels_like = curr.get("apparent_temperature", "--")
        self.canvas.create_text(
            x + 25, y + 215,
            text=f"{w_info['condition']} — {w_info['description']}",
            font=self.font_h2,
            fill=self.current_theme["accent"],
            anchor="w",
            tags="ui_element"
        )
        self.canvas.create_text(
            x + 25, y + 242,
            text=f"Feels like {round(feels_like)}{unit_symbol}",
            font=self.font_subtitle,
            fill=self.current_theme["text_secondary"],
            anchor="w",
            tags="ui_element"
        )

        # 4 Mini Metric Cards Inside Hero
        metric_y = y + 280
        metric_w = (left_w - 50) // 4
        metric_h = 75

        metrics = [
            ("💧 Humidity", f"{curr.get('relative_humidity_2m', '--')}%"),
            ("💨 Wind", f"{curr.get('wind_speed_10m', '--')} {'mph' if self.is_fahrenheit else 'km/h'}"),
            ("⏲ Pressure", f"{round(curr.get('surface_pressure', 0))} hPa"),
            ("🌧 Rain Prob", f"{curr.get('precipitation', 0)} mm")
        ]

        for i, (label, val) in enumerate(metrics):
            mx = x + 15 + i * (metric_w + 6)
            m_card = create_glass_card(metric_w, metric_h, radius=10, fill_rgba=(255, 255, 255, 18), border_rgba=(255, 255, 255, 45))
            self.canvas.create_image(mx, metric_y, image=m_card, anchor="nw", tags="ui_element")
            self.canvas.create_text(
                mx + metric_w // 2, metric_y + 22,
                text=label,
                font=self.font_body,
                fill=self.current_theme["text_secondary"],
                tags="ui_element"
            )
            self.canvas.create_text(
                mx + metric_w // 2, metric_y + 48,
                text=val,
                font=self.font_body_bold,
                fill=self.current_theme["text_primary"],
                tags="ui_element"
            )

    def _draw_hourly_forecast(self, w: int, h: int):
        left_w = int(w * 0.44)
        x = 30
        y = int(h * 0.50) + 95
        hourly_h = h - y - 35
        if hourly_h < 100:
            return

        card = create_glass_card(left_w, hourly_h, radius=18, fill_rgba=self.current_theme["glass_fill"], border_rgba=self.current_theme["glass_border"])
        self.canvas.create_image(x, y, image=card, anchor="nw", tags="ui_element")

        self.canvas.create_text(
            x + 20, y + 22,
            text="⏱ Hourly Forecast (Next 24h)",
            font=self.font_h2,
            fill=self.current_theme["text_primary"],
            anchor="w",
            tags="ui_element"
        )

        if not self.weather_data or "hourly" not in self.weather_data:
            return

        hourly = self.weather_data["hourly"]
        times = hourly.get("time", [])[:24]
        temps = hourly.get("temperature_2m", [])[:24]
        codes = hourly.get("weather_code", [])[:24]
        is_days = hourly.get("is_day", [])[:24]

        # Display first 6 key intervals (e.g. +1h, +3h, +6h, +9h, +12h, +18h)
        indices = [0, 2, 5, 8, 12, 17] if len(times) >= 18 else list(range(min(6, len(times))))
        card_w = (left_w - 40) // len(indices)

        for i, idx in enumerate(indices):
            if idx >= len(times):
                continue
            t_str = times[idx]
            dt = datetime.datetime.fromisoformat(t_str)
            hour_label = dt.strftime("%I %p").lstrip("0")
            temp_val = temps[idx]
            code = codes[idx]
            is_d = is_days[idx] if idx < len(is_days) else 1
            info = get_weather_info(code, is_d)

            cx = x + 12 + i * (card_w + 3)
            cy = y + 45
            ch = hourly_h - 60

            # Mini hour pill
            h_card = create_glass_card(card_w, ch, radius=10, fill_rgba=(255, 255, 255, 14), border_rgba=(255, 255, 255, 40))
            self.canvas.create_image(cx, cy, image=h_card, anchor="nw", tags="ui_element")

            self.canvas.create_text(cx + card_w // 2, cy + 20, text=hour_label, font=self.font_body, fill=self.current_theme["text_secondary"], tags="ui_element")
            self.canvas.create_text(cx + card_w // 2, cy + 46, text=info["icon"], font=self.font_icon_mid, tags="ui_element")
            unit_sym = "°F" if self.is_fahrenheit else "°C"
            self.canvas.create_text(cx + card_w // 2, cy + 74, text=f"{round(temp_val)}{unit_sym}", font=self.font_body_bold, fill=self.current_theme["text_primary"], tags="ui_element")

    def _draw_daily_forecast(self, w: int, h: int):
        left_w = int(w * 0.44)
        daily_x = left_w + 50
        daily_w = w - daily_x - 30
        daily_y = 75
        daily_h = h - daily_y - 35
        if daily_w < 200 or daily_h < 200:
            return

        card = create_glass_card(daily_w, daily_h, radius=20, fill_rgba=self.current_theme["glass_fill"], border_rgba=self.current_theme["glass_border"])
        self.canvas.create_image(daily_x, daily_y, image=card, anchor="nw", tags="ui_element")

        self.canvas.create_text(
            daily_x + 25, daily_y + 30,
            text="📅 7-Day Forecast",
            font=self.font_h2,
            fill=self.current_theme["text_primary"],
            anchor="w",
            tags="ui_element"
        )

        if not self.weather_data or "daily" not in self.weather_data:
            return

        daily = self.weather_data["daily"]
        dates = daily.get("time", [])[:7]
        codes = daily.get("weather_code", [])[:7]
        t_max = daily.get("temperature_2m_max", [])[:7]
        t_min = daily.get("temperature_2m_min", [])[:7]
        precip = daily.get("precipitation_probability_max", [])[:7]

        row_h = (daily_h - 70) // max(len(dates), 1)
        unit_sym = "°F" if self.is_fahrenheit else "°C"

        for i, date_str in enumerate(dates):
            dt = datetime.date.fromisoformat(date_str)
            day_name = "Today" if i == 0 else dt.strftime("%A")
            formatted_date = dt.strftime("%b %d")
            code = codes[i] if i < len(codes) else 0
            info = get_weather_info(code, 1)
            high = t_max[i] if i < len(t_max) else "--"
            low = t_min[i] if i < len(t_min) else "--"
            rain_chance = f"{precip[i]}%" if i < len(precip) and precip[i] is not None else "--"

            ry = daily_y + 60 + i * row_h

            # Subtle alternating hover-style glass row
            r_card = create_glass_card(daily_w - 40, row_h - 8, radius=8, fill_rgba=(255, 255, 255, 12), border_rgba=(255, 255, 255, 30))
            self.canvas.create_image(daily_x + 20, ry, image=r_card, anchor="nw", tags="ui_element")

            # Day name & Date
            self.canvas.create_text(
                daily_x + 35, ry + (row_h - 8) // 2 - 8,
                text=day_name,
                font=self.font_body_bold,
                fill=self.current_theme["text_primary"],
                anchor="w",
                tags="ui_element"
            )
            self.canvas.create_text(
                daily_x + 35, ry + (row_h - 8) // 2 + 10,
                text=formatted_date,
                font=self.font_body,
                fill=self.current_theme["text_secondary"],
                anchor="w",
                tags="ui_element"
            )

            # Weather Icon & Condition
            self.canvas.create_text(
                daily_x + int(daily_w * 0.36), ry + (row_h - 8) // 2,
                text=f"{info['icon']}  {info['condition']}",
                font=self.font_body,
                fill=self.current_theme["text_primary"],
                anchor="w",
                tags="ui_element"
            )

            # Rain probability badge
            self.canvas.create_text(
                daily_x + int(daily_w * 0.65), ry + (row_h - 8) // 2,
                text=f"💧 {rain_chance}",
                font=self.font_body,
                fill=self.current_theme["text_secondary"],
                anchor="w",
                tags="ui_element"
            )

            # High / Low Temperature
            self.canvas.create_text(
                daily_x + daily_w - 45, ry + (row_h - 8) // 2,
                text=f"{round(high)}{unit_sym} / {round(low)}{unit_sym}",
                font=self.font_body_bold,
                fill=self.current_theme["text_primary"],
                anchor="e",
                tags="ui_element"
            )

    def _on_search_text_changed(self, *args):
        if self.search_debounce_id:
            self.after_cancel(self.search_debounce_id)
        self.search_debounce_id = self.after(350, self._query_suggestions)

    def _query_suggestions(self):
        text = self.search_var.get().strip()
        if len(text) < 2:
            self.suggest_box.place_forget()
            return

        def on_results(results):
            self.after(0, lambda: self._show_suggestions(results))

        self.api_client.search_cities_async(text, on_results, lambda err: None)

    def _show_suggestions(self, results: List[Dict[str, Any]]):
        if not results:
            self.suggest_box.place_forget()
            return

        self.suggest_results = results
        self.suggest_box.delete(0, tk.END)
        for r in results:
            self.suggest_box.insert(tk.END, f"  {r['display_name']}")

        w = self.canvas.winfo_width()
        entry_w = min(max(int(w * 0.28), 220), 320)
        entry_x = w - entry_w - 240
        self.suggest_box.place(x=entry_x, y=58, width=entry_w, height=min(len(results) * 26 + 10, 140))
        self.suggest_box.lift()

    def _on_select_suggestion(self, event):
        sel = self.suggest_box.curselection()
        if not sel or not hasattr(self, "suggest_results"):
            return
        item = self.suggest_results[sel[0]]
        self.suggest_box.place_forget()
        self.search_var.set(item["name"])
        self.load_weather(item["latitude"], item["longitude"], item["name"], item["country"])

    def _on_search_submit(self):
        text = self.search_var.get().strip()
        if not text:
            return
        self.suggest_box.place_forget()
        self.status_message = f"Searching for '{text}'..."
        self._redraw_all()

        def on_results(results):
            if results:
                top = results[0]
                self.after(0, lambda: self.load_weather(top["latitude"], top["longitude"], top["name"], top["country"]))
            else:
                self.after(0, lambda: self._show_error(f"City '{text}' not found."))

        self.api_client.search_cities_async(text, on_results, lambda err: self._show_error(err))

    def _toggle_units(self):
        self.is_fahrenheit = not self.is_fahrenheit
        self.status_message = f"Switched unit to {'°F' if self.is_fahrenheit else '°C'}"
        self.load_weather(self.current_lat, self.current_lon, self.current_city, self.current_country)

    def load_weather(self, lat: float, lon: float, city: str, country: str):
        self.current_lat = lat
        self.current_lon = lon
        self.current_city = city
        self.current_country = country
        self.status_message = f"Fetching real-time weather for {city}..."
        self._redraw_all()

        def on_success(data):
            self.after(0, lambda: self._apply_weather_data(data))

        def on_error(msg):
            self.after(0, lambda: self._show_error(msg))

        self.api_client.fetch_weather_async(lat, lon, self.is_fahrenheit, on_success, on_error)

    def _apply_weather_data(self, data: Dict[str, Any]):
        self.weather_data = data
        curr = data.get("current", {})
        code = curr.get("weather_code", 0)
        is_day = curr.get("is_day", 1)
        w_info = get_weather_info(code, is_day)

        # Update Theme
        self.current_theme = get_theme(w_info["theme_name"])

        # Update Animation
        self.animator.set_animation(w_info["animation"])

        self.status_message = f"Updated live weather for {self.current_city}."
        self._redraw_all()

    def _show_error(self, message: str):
        self.status_message = f"⚠️ {message}"
        self._redraw_all()
