"""
SkyCast Desktop UI — Main Application Window
--------------------------------------------
Orchestrates all Tkinter components:
- Responsive Canvas layout with Pillow glassmorphism panels (1100x750 default, min 800x600)
- Asynchronous Open-Meteo network requests (never freezes the GUI)
- Settings & Favorites persistence via `storage.py`
- Offline fallback to cached weather data
- 10-minute auto-refresh cycle with manual refresh trigger
- Unit conversions (°C/°F, wind km/h/mph/m/s, pressure hPa/inHg)
- Weather particle animations (rain, snow, clouds, thunderstorm with lightning flash)
"""

import tkinter as tk
from tkinter import font as tkfont
import time
import queue
from typing import Dict, Any, Optional, List

from shared.weather_codes import get_weather_info
from desktop.storage import StorageManager
from desktop.api_client import WeatherApiClient
from desktop.ui.theme import get_theme, DEFAULT_THEME
from desktop.ui.panels import get_gradient_image, create_glass_card
from desktop.ui.animations import WeatherAnimator
from desktop.ui.search_bar import SearchBar
from desktop.ui.current_weather import CurrentWeatherCard
from desktop.ui.details_grid import DetailsGrid
from desktop.ui.forecast import ForecastView

class SkyCastMainWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("SkyCast — Real-Time Weather Application")
        self.geometry("1100x750")
        self.minsize(800, 600)

        # Thread-safe task queue for background workers
        self.task_queue = queue.Queue()
        self._poll_queue()

        # Core Managers
        self.storage = StorageManager()
        self.api_client = WeatherApiClient()

        # State
        self.units = self.storage.get_units()
        self.current_city = self.storage.get_last_city()
        self.weather_data: Optional[Dict[str, Any]] = None
        self.current_theme = DEFAULT_THEME
        self.last_updated_time: float = time.time()
        self.is_offline: bool = False
        self.status_message: str = "Ready"

        self.resize_debounce_id: Optional[str] = None
        self.auto_refresh_id: Optional[str] = None

        # Build Full Canvas
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.canvas.pack(fill="both", expand=True)

        # Setup Fonts
        self._init_fonts()

        # Child Component Controllers
        self.animator = WeatherAnimator(self.canvas)
        self.search_bar = SearchBar(
            parent_canvas=self.canvas,
            on_search_submit=self._on_search_submit,
            on_select_city=self._on_city_selected,
            on_query_autocomplete=self._on_query_autocomplete
        )
        self.hero_card = CurrentWeatherCard(
            canvas=self.canvas,
            on_toggle_favorite=self._toggle_favorite,
            on_refresh=self._manual_refresh
        )
        self.details_grid = DetailsGrid(self.canvas)
        self.forecast_view = ForecastView(self.canvas)

        # Bindings
        self.bind("<Configure>", self._on_resize)

        # Load initial weather (or offline cache if network fails)
        self.after(150, self._load_initial_data)

        # Start 10-minute auto-refresh cycle
        self._schedule_auto_refresh()

    def _init_fonts(self):
        self.fonts = {
            "logo": tkfont.Font(family="Segoe UI", size=16, weight="bold"),
            "title": tkfont.Font(family="Segoe UI", size=22, weight="bold"),
            "subtitle": tkfont.Font(family="Segoe UI", size=10),
            "temp_large": tkfont.Font(family="Segoe UI", size=50, weight="bold"),
            "h2": tkfont.Font(family="Segoe UI", size=13, weight="bold"),
            "body": tkfont.Font(family="Segoe UI", size=10),
            "body_bold": tkfont.Font(family="Segoe UI", size=10, weight="bold"),
            "small": tkfont.Font(family="Segoe UI", size=8),
            "small_bold": tkfont.Font(family="Segoe UI", size=8, weight="bold"),
            "icon_large": tkfont.Font(family="Segoe UI Emoji", size=46)
        }

    def _on_resize(self, event):
        if event.widget == self:
            if self.resize_debounce_id:
                self.after_cancel(self.resize_debounce_id)
            self.resize_debounce_id = self.after(80, self._redraw_ui)

    def _schedule_auto_refresh(self):
        """Auto-refresh every 10 minutes (600,000 ms)."""
        if self.auto_refresh_id:
            self.after_cancel(self.auto_refresh_id)
        self.auto_refresh_id = self.after(600000, self._auto_refresh_tick)

    def _auto_refresh_tick(self):
        self.load_weather(self.current_city, silent=True)
        self._schedule_auto_refresh()

    def _manual_refresh(self):
        self.status_message = "Refreshing live weather..."
        self._redraw_ui()
        self.load_weather(self.current_city)

    def _load_initial_data(self):
        # Load last city from storage
        last_c = self.storage.get_last_city()
        self.load_weather(last_c)

    def _poll_queue(self):
        """Process any pending thread callbacks safely in the Tkinter main loop."""
        try:
            while not self.task_queue.empty():
                callback = self.task_queue.get_nowait()
                try:
                    callback()
                except Exception as ex:
                    print(f"[MainThread Queue Error]: {ex}")
        except Exception:
            pass
        self.after(50, self._poll_queue)

    def dispatch_to_main_thread(self, callback):
        """Thread-safe dispatch from background workers into the Tkinter main thread."""
        self.task_queue.put(callback)

    def load_weather(self, city_info: Dict[str, Any], silent: bool = False):
        """Asynchronously load weather from Open-Meteo, with graceful offline fallback."""
        self.current_city = city_info
        lat = city_info.get("lat") or city_info.get("latitude", 51.5074)
        lon = city_info.get("lon") or city_info.get("longitude", -0.1278)

        if not silent:
            self.status_message = f"Fetching real-time weather for {city_info.get('name', 'city')}..."
            self._redraw_ui()

        temp_u = self.units.get("temp", "celsius")
        wind_u = self.units.get("wind", "kmh")

        def on_success(data: Dict[str, Any]):
            # Safely queue UI update into the main thread task queue
            self.dispatch_to_main_thread(lambda: self._apply_weather_success(data, city_info))

        def on_error(err_msg: str):
            self.dispatch_to_main_thread(lambda: self._apply_weather_error(err_msg))

        self.api_client.get_weather_async(lat, lon, temp_u, wind_u, on_success, on_error)

    def _apply_weather_success(self, data: Dict[str, Any], city_info: Dict[str, Any]):
        self.weather_data = data
        self.last_updated_time = time.time()
        self.is_offline = False
        self.status_message = f"Live weather updated for {city_info.get('name')}."

        # Cache for offline usage
        self.storage.save_cache(data)
        self.storage.set_last_city(city_info)

        # Dynamic Theme & Particle Animation
        curr = data.get("current", {})
        code = curr.get("weather_code", 0)
        is_day = curr.get("is_day", 1)
        w_info = get_weather_info(code, is_day)

        self.current_theme = get_theme(w_info["theme_key"])
        self.animator.set_animation(w_info["animation"])

        self._redraw_ui()

    def _apply_weather_error(self, err_msg: str):
        # Attempt offline fallback
        cached = self.storage.get_cache()
        if cached:
            self.weather_data = cached
            self.last_updated_time = self.storage.get_cache_timestamp()
            self.is_offline = True
            self.status_message = f"⚠️ {err_msg} — Displaying cached offline data."

            curr = cached.get("current", {})
            code = curr.get("weather_code", 0)
            is_day = curr.get("is_day", 1)
            w_info = get_weather_info(code, is_day)
            self.current_theme = get_theme(w_info["theme_key"])
            self.animator.set_animation(w_info["animation"])
        else:
            self.status_message = f"⚠️ {err_msg} — No cached data available."

        self._redraw_ui()

    # --- Search & Autocomplete Handlers ---

    def _on_query_autocomplete(self, query: str):
        def on_res(results):
            self.dispatch_to_main_thread(lambda: self._show_autocomplete(results))
        self.api_client.search_cities_async(query, on_res, lambda e: None)

    def _show_autocomplete(self, results):
        w = self.canvas.winfo_width()
        entry_w = min(max(int(w * 0.26), 200), 300)
        entry_x = int(w * 0.28)
        self.search_bar.update_suggestions(results, entry_x, 56, entry_w)

    def _on_city_selected(self, city_item: Dict[str, Any]):
        self.load_weather(city_item)

    def _on_search_submit(self, query: str):
        self.status_message = f"Searching for '{query}'..."
        self._redraw_ui()

        def on_res(results):
            if results:
                self.dispatch_to_main_thread(lambda: self.load_weather(results[0]))
            else:
                self.dispatch_to_main_thread(lambda: self._apply_weather_error(f"City '{query}' not found."))

        self.api_client.search_cities_async(query, on_res, lambda err: self.dispatch_to_main_thread(lambda: self._apply_weather_error(err)))

    # --- Favorites & Unit Toggles ---

    def _toggle_favorite(self):
        city_name = self.current_city.get("name", "")
        if self.storage.is_favorite(city_name):
            self.storage.remove_favorite(city_name)
            self.status_message = f"Removed {city_name} from favorites."
        else:
            self.storage.add_favorite(self.current_city)
            self.status_message = f"Added {city_name} to favorites ⭐"
        self._redraw_ui()

    def _show_favorites_menu(self):
        favs = self.storage.get_favorites()
        if not favs:
            self.status_message = "No favorite cities added yet. Click ⭐ to bookmark a city."
            self._redraw_ui()
            return

        # Simple popup listbox
        w = self.canvas.winfo_width()
        top_x = w - 410
        self.search_bar.update_suggestions(favs, top_x, 56, 200)

    def _toggle_temp_unit(self):
        curr = self.units.get("temp", "celsius")
        new_u = "fahrenheit" if curr == "celsius" else "celsius"
        self.units["temp"] = new_u
        self.storage.set_unit("temp", new_u)
        self.load_weather(self.current_city)

    def _toggle_wind_unit(self):
        curr = self.units.get("wind", "kmh")
        order = ["kmh", "mph", "ms"]
        next_u = order[(order.index(curr) + 1) % len(order)]
        self.units["wind"] = next_u
        self.storage.set_unit("wind", next_u)
        self.load_weather(self.current_city)

    def _toggle_pressure_unit(self):
        curr = self.units.get("pressure", "hPa")
        new_u = "inHg" if curr == "hPa" else "hPa"
        self.units["pressure"] = new_u
        self.storage.set_unit("pressure", new_u)
        self._redraw_ui()

    # --- Rendering Engine ---

    def _redraw_ui(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100 or h < 100:
            return

        self.canvas.delete("ui_element")
        self.canvas.delete("bg_gradient")

        # 1. Background linear gradient
        grad_img = get_gradient_image(
            w, h,
            self.current_theme["gradient_top"],
            self.current_theme["gradient_bottom"]
        )
        self.canvas.create_image(0, 0, image=grad_img, anchor="nw", tags="bg_gradient")

        # 2. Top Header Navigation
        self._draw_header(w)

        # 3. Layout Dimensions (2 Columns)
        margin = 25
        gap = 18
        top_y = 75

        # Responsive column split
        col_w = (w - margin * 2 - gap) // 2

        # Left Column: Hero Weather Card + Extra Details Grid
        hero_h = int((h - top_y - 40) * 0.48)
        details_y = top_y + hero_h + gap
        details_h = h - details_y - 35

        is_fav = self.storage.is_favorite(self.current_city.get("name", ""))
        self.hero_card.draw(
            x=margin, y=top_y, width=col_w, height=hero_h,
            city_info=self.current_city,
            weather_data=self.weather_data or {},
            theme=self.current_theme,
            units=self.units,
            is_fav=is_fav,
            last_updated_time=self.last_updated_time,
            is_offline=self.is_offline,
            fonts=self.fonts
        )

        self.details_grid.draw(
            x=margin, y=details_y, width=col_w, height=details_h,
            weather_data=self.weather_data or {},
            theme=self.current_theme,
            units=self.units,
            font_title=self.fonts["h2"],
            font_value=self.fonts["body_bold"],
            font_label=self.fonts["small_bold"],
            font_badge=self.fonts["small"]
        )

        # Right Column: 24h Trend Chart + 7-Day Forecast
        chart_x = margin + col_w + gap
        chart_h = int((h - top_y - 40) * 0.44)
        daily_y = top_y + chart_h + gap
        daily_h = h - daily_y - 35

        temp_sym = "°F" if self.units.get("temp") == "fahrenheit" else "°C"

        self.forecast_view.draw_trend_chart(
            x=chart_x, y=top_y, width=col_w, height=chart_h,
            weather_data=self.weather_data or {},
            theme=self.current_theme,
            temp_symbol=temp_sym,
            font_title=self.fonts["h2"],
            font_small=self.fonts["small"],
            font_bold=self.fonts["small_bold"]
        )

        self.forecast_view.draw_7day_forecast(
            x=chart_x, y=daily_y, width=col_w, height=daily_h,
            weather_data=self.weather_data or {},
            theme=self.current_theme,
            temp_symbol=temp_sym,
            font_title=self.fonts["h2"],
            font_body=self.fonts["body"],
            font_bold=self.fonts["body_bold"]
        )

        # Status Bar at Bottom
        self.canvas.create_text(
            margin, h - 16,
            text=f"✦ {self.status_message}   |   Open-Meteo API",
            font=self.fonts["small"],
            fill=self.current_theme["text_muted"],
            anchor="w",
            tags="ui_element"
        )

    def _draw_header(self, w: int):
        margin = 25
        # Logo & App Title
        self.canvas.create_text(
            margin, 36,
            text="✦ SKYCAST",
            font=self.fonts["logo"],
            fill=self.current_theme["text_primary"],
            anchor="w",
            tags="ui_element"
        )
        self.canvas.create_text(
            margin + 125, 38,
            text="Weather Intelligence",
            font=self.fonts["subtitle"],
            fill=self.current_theme["text_secondary"],
            anchor="w",
            tags="ui_element"
        )

        # Place native search entry
        entry_w = min(max(int(w * 0.26), 200), 300)
        entry_x = int(w * 0.28)
        self.canvas.create_window(entry_x, 38, window=self.search_bar.entry, width=entry_w, height=32, tags="ui_element")

        # Search Button
        s_btn_x = entry_x + entry_w // 2 + 25
        self._create_btn(s_btn_x, 22, 65, 32, "Search", "#2563EB", "#FFFFFF", self.search_bar.submit)

        # Favorites Button (⭐)
        fav_btn_x = s_btn_x + 72
        self._create_btn(fav_btn_x, 22, 85, 32, "★ Saved", "#334155", "#F8FAFC", self._show_favorites_menu)

        # Unit Toggles: Temp (°C/°F), Wind, Pressure
        t_sym = "°F" if self.units.get("temp") == "fahrenheit" else "°C"
        w_sym = self.units.get("wind", "kmh")
        p_sym = self.units.get("pressure", "hPa")

        btn1_x = w - margin - 220
        self._create_btn(btn1_x, 22, 65, 32, t_sym, "#1E293B", "#38BDF8", self._toggle_temp_unit)

        btn2_x = btn1_x + 72
        self._create_btn(btn2_x, 22, 65, 32, w_sym, "#1E293B", "#38BDF8", self._toggle_wind_unit)

        btn3_x = btn2_x + 72
        self._create_btn(btn3_x, 22, 65, 32, p_sym, "#1E293B", "#38BDF8", self._toggle_pressure_unit)

    def _create_btn(self, x: int, y: int, w: int, h: int, text: str, bg_color: str, fg_color: str, callback):
        tag = f"btn_{x}_{y}"
        btn_card = create_glass_card(w, h, radius=8, fill_rgba=(30, 41, 59, 210), border_rgba=(148, 163, 184, 100))
        self.canvas.create_image(x, y, image=btn_card, anchor="nw", tags=("ui_element", tag))
        self.canvas.create_text(
            x + w // 2, y + h // 2,
            text=text,
            font=self.fonts["small_bold"],
            fill=fg_color,
            tags=("ui_element", tag)
        )
        self.canvas.tag_bind(tag, "<Button-1>", lambda e: callback())
        self.canvas.tag_bind(tag, "<Enter>", lambda e: self.config(cursor="hand2"))
        self.canvas.tag_bind(tag, "<Leave>", lambda e: self.config(cursor=""))
