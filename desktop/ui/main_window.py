"""
SkyCast Desktop UI — Main Application Window (Stage 4 Complete)
--------------------------------------------------------------
Full real-time Open-Meteo weather integration:
- Search with 300 ms debounced autocomplete (city, region, country)
- Live current weather card with real WMO mapping, local time, and dynamic summary
- No text cutoffs: condition wraps/shrinks font; only long city names truncate with '...'
- Bottom padding inside main card so summary never touches the edge
- 24-hour temperature trend line chart on canvas with min/max annotations
- Today (hourly scrollable) / Week (7-day) / 16 Days (extended) tabs with rain chance
- Overview grid with 6 rich glass tiles:
  1. Humidity (large droplet + dew point)
  2. UV Index (vertical gradient thermometer bar + category)
  3. Visibility (haze icon + distance status)
  4. Wind (compass + speed & direction)
  5. Pressure (barometer dial + hPa/inHg)
  6. Air Quality & Sun (AQI rating + sunrise/sunset)
- Other Cities right column using saved favorites with [+ Add Fav] and [✕ Remove]
- Thread-safe background network requests with safe UI dispatch
- Loading state spinner & friendly error notification banner
"""

import sys
import os
import time
import queue
import math
import datetime
import threading
import tkinter as tk
from tkinter import font as tkfont
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image, ImageTk

# Windows High-DPI Awareness
if sys.platform == "win32":
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from shared.weather_codes import resolve_theme, get_weather_info, get_aqi_level, get_uv_level
from desktop.storage import StorageManager
from desktop.api_client import WeatherApiClient
from desktop.ui.panels import (
    generate_procedural_background,
    render_frosted_glass_panel,
    clear_panel_cache
)
from desktop.ui.icons import get_weather_icon_image, get_icon_for_wmo
from desktop.ui.other_cities import OtherCitiesPanel, truncate_text
from desktop.ui.animations import WeatherAnimator

PREVIEW_PRESETS = [
    {
        "label": "Rain — Day",
        "wallpaper": "partly_cloudy.jpg",
        "anim": "rain",
        "wmo": 63,
        "is_day": 1,
        "temp": 14,
        "apparent": 13,
        "cond": "Moderate Rain",
        "summary": "Persistent rain showers with overcast skies. Keep an umbrella handy."
    },
    {
        "label": "Thunderstorm — Night",
        "wallpaper": "rain_night.jpg",
        "anim": "thunderstorm",
        "wmo": 95,
        "is_day": 0,
        "temp": 17,
        "apparent": 16,
        "cond": "Thunderstorm",
        "summary": "Active lightning strikes and heavy downpours throughout the night."
    },
    {
        "label": "Snow — Day",
        "wallpaper": "snow.jpg",
        "anim": "snow",
        "wmo": 73,
        "is_day": 1,
        "temp": -2,
        "apparent": -6,
        "cond": "Snow Showers",
        "summary": "Crisp winter flurries with drifting snow and sub-zero temperatures."
    },
    {
        "label": "Clear — Night",
        "wallpaper": "clear_night.jpg",
        "anim": "stars",
        "wmo": 0,
        "is_day": 0,
        "temp": 8,
        "apparent": 7,
        "cond": "Clear Sky",
        "summary": "Brilliant starry sky with calm winds and cool nighttime temperatures."
    },
    {
        "label": "Fog — Dawn",
        "wallpaper": "fog.jpg",
        "anim": "fog",
        "wmo": 45,
        "is_day": 1,
        "temp": 6,
        "apparent": 5,
        "cond": "Dense Fog",
        "summary": "Misty morning haze with low visibility. Gentle warming expected later."
    },
    {
        "label": "Clear — Day",
        "wallpaper": "clear_day.jpg",
        "anim": "clouds",
        "wmo": 0,
        "is_day": 1,
        "temp": 22,
        "apparent": 21,
        "cond": "Sunny & Clear",
        "summary": "Bright sunny afternoon with gentle breeze and perfect outdoor weather."
    },
    {
        "label": "Drizzle — Day",
        "wallpaper": "cloudy.jpg",
        "anim": "drizzle",
        "wmo": 51,
        "is_day": 1,
        "temp": 12,
        "apparent": 11,
        "cond": "Light Drizzle",
        "summary": "Fine misty drizzle under cool overcast cloud layers."
    },
    {
        "label": "Overcast — Evening",
        "wallpaper": "cloudy.jpg",
        "anim": "clouds",
        "wmo": 3,
        "is_day": 0,
        "temp": 11,
        "apparent": 10,
        "cond": "Overcast Evening",
        "summary": "Dense cloud cover with rich sunset hues and light evening breeze."
    }
]

class SkyCastMainWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("SkyCast — Real-Time Weather Application")
        self.geometry("1100x750")
        self.minsize(800, 600)

        # Thread-safe queue for background thread execution
        self.task_queue = queue.Queue()
        self._poll_queue()

        # Core Managers
        self.storage = StorageManager()
        self.api_client = WeatherApiClient()

        # State
        self.units = self.storage.get_units()
        self.active_tab = "Today"  # 'Today', 'Week', '16 Days'
        self.current_city = self.storage.get_last_city()
        self.weather_data: Optional[Dict[str, Any]] = None
        self.favorites_weather: List[Dict[str, Any]] = []
        self.is_loading: bool = False
        self.error_banner_text: Optional[str] = None
        self.error_banner_id: Optional[str] = None

        # Autocomplete Search State
        self.search_debounce_id: Optional[str] = None
        self.search_suggestions: List[Dict[str, Any]] = []
        self.show_search_dropdown: bool = False

        # Visual Theme & Backgrounds
        self.current_theme = resolve_theme(0, is_day=1, temp_c=15.0)
        self.bg_pil_image: Optional[Image.Image] = None
        self.bg_photo: Optional[ImageTk.PhotoImage] = None
        self.forced_wallpaper: Optional[str] = None
        self._icon_refs: List[Any] = []
        self.resize_debounce_id: Optional[str] = None

        # Canvas Host
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.canvas.pack(fill="both", expand=True)

        # Initialize Fonts
        self._init_fonts()

        # Dynamic Weather Particle Animation Engine (Stage 5)
        self.animator = WeatherAnimator(self.canvas)

        # Auto-Refresh & Timers
        self.last_updated_time = time.time()
        self.after(60000, self._tick_update_timer)

        # F2 Preview & Multi-page Forecast State
        self.f2_badge_text: Optional[str] = None
        self.f2_badge_id: Optional[str] = None
        self.sixteen_days_page: int = 0
        self.is_fading: bool = False

        # Popovers & Interactive Top-Bar State
        self.show_settings_popover: bool = False
        self.show_about_popover: bool = False
        self.settings_popover_bbox: Tuple[int, int, int, int] = (0, 0, 0, 0)
        self.about_popover_bbox: Tuple[int, int, int, int] = (0, 0, 0, 0)
        self.cache_cleared_notice: bool = False
        self.favs_reset_notice: bool = False
        self._last_gear_x: int = 0
        self._last_logo_x: int = 0

        # Right Column Favorites Panel
        self.other_cities_panel = OtherCitiesPanel(
            self.canvas,
            on_select_city=self._on_select_favorite_city,
            on_remove_city=self._on_remove_favorite_city,
            on_add_current_city=self._on_toggle_current_favorite
        )

        # Bindings
        self.bind("<Configure>", self._on_resize)
        self.bind("<F2>", lambda e: self._toggle_preview_mode())
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # Build embedded search entry widget & standard native widgets
        self._build_search_widget()
        self._init_native_widgets()

        # Load initial live weather
        self.load_weather_for_city(self.current_city)
        self._load_favorites_weather()

    def _init_fonts(self):
        """Configure crisp typography for high-DPI monitors."""
        self.fonts = {
            "logo": tkfont.Font(family="Segoe UI", size=15, weight="bold"),
            "city_title": tkfont.Font(family="Segoe UI", size=19, weight="bold"),
            "temp_huge": tkfont.Font(family="Segoe UI", size=48, weight="bold"),
            "tile_val": tkfont.Font(family="Segoe UI", size=26, weight="bold"),
            "h2": tkfont.Font(family="Segoe UI", size=13, weight="bold"),
            "h3": tkfont.Font(family="Segoe UI", size=11, weight="bold"),
            "body": tkfont.Font(family="Segoe UI", size=10),
            "body_bold": tkfont.Font(family="Segoe UI", size=10, weight="bold"),
            "small": tkfont.Font(family="Segoe UI", size=9),
            "small_bold": tkfont.Font(family="Segoe UI", size=9, weight="bold"),
            "chart_label": tkfont.Font(family="Segoe UI", size=8, weight="bold"),
        }

    def _poll_queue(self):
        """Safely execute callbacks dispatched from background threads."""
        try:
            if not self.winfo_exists():
                return
            while not self.task_queue.empty():
                callback = self.task_queue.get_nowait()
                try:
                    callback()
                except Exception as ex:
                    print(f"[SkyCast Queue Error]: {ex}")
            if self.winfo_exists():
                self.after(40, self._poll_queue)
        except Exception:
            pass

    def dispatch_to_main_thread(self, callback):
        self.task_queue.put(callback)

    def _on_resize(self, event):
        """Debounced resize handler: only re-renders panels when resizing stops."""
        if event.widget == self:
            if self.resize_debounce_id:
                self.after_cancel(self.resize_debounce_id)
            self.resize_debounce_id = self.after(80, self._render_all_panels)

    # ========================================================================
    # Search Widget & Autocomplete Dropdown
    # ========================================================================
    def _build_search_widget(self):
        self.search_var = tk.StringVar(value="")
        self.search_entry = tk.Entry(
            self.canvas,
            textvariable=self.search_var,
            font=self.fonts["body_bold"],
            bg="#1E293B",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            relief="flat",
            bd=0,
            highlightthickness=0
        )
        self.search_entry.bind("<KeyRelease>", self._on_search_key)
        self.search_entry.bind("<Return>", self._on_search_enter)
        self.search_entry.bind("<Escape>", lambda e: self._close_search_dropdown())
        self.search_entry.bind("<FocusIn>", self._on_search_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_search_focus_out)
        self._placeholder_active = True
        self.search_var.set("Search City...")

    def _init_native_widgets(self):
        """MANDATORY: Standard native tk.Label and tk.Button widgets embedded via canvas.create_window."""
        btn_style = {
            "bd": 0,
            "relief": "flat",
            "highlightthickness": 0,
            "bg": "#3b4d66",
            "fg": "#ffffff",
            "activebackground": "#526b8a",
            "activeforeground": "#ffffff",
            "cursor": "hand2"
        }

        # 1. Header Labels (tk.Label)
        self.lbl_brand_title = tk.Label(
            self.canvas,
            text="SkyCast",
            font=self.fonts["logo"],
            bg="#243447",
            fg="#FFFFFF",
            bd=0,
            relief="flat",
            highlightthickness=0,
            cursor="hand2"
        )
        self.lbl_brand_title.bind("<Button-1>", lambda e: self._toggle_about_popover())

        self.lbl_updated_status = tk.Label(
            self.canvas,
            text="Updated just now",
            font=self.fonts["small_bold"],
            bg="#243447",
            fg="#CBD5E1",
            bd=0,
            relief="flat",
            highlightthickness=0
        )

        # 2. Header Buttons (tk.Button)
        self.btn_refresh = tk.Button(
            self.canvas,
            text="⟳",
            font=("Segoe UI", 12, "bold"),
            command=self.refresh_weather,
            **btn_style
        )

        t_sym = "°F" if self.units.get("temp") == "fahrenheit" else "°C"
        self.btn_unit_toggle = tk.Button(
            self.canvas,
            text=f"[{t_sym}]",
            font=self.fonts["body_bold"],
            command=self._toggle_units,
            **btn_style
        )

        self.btn_settings = tk.Button(
            self.canvas,
            text="⚙",
            font=("Segoe UI", 13, "bold"),
            command=self.open_settings_modal,
            **btn_style
        )

        # 3. Forecast Tab Buttons (tk.Button)
        self.btn_tab_today = tk.Button(
            self.canvas,
            text="Today",
            font=self.fonts["small_bold"],
            command=lambda: self._switch_forecast_tab("Today"),
            **btn_style
        )
        self.btn_tab_week = tk.Button(
            self.canvas,
            text="Week",
            font=self.fonts["small_bold"],
            command=lambda: self._switch_forecast_tab("Week"),
            **btn_style
        )
        self.btn_tab_16days = tk.Button(
            self.canvas,
            text="16 Days",
            font=self.fonts["small_bold"],
            command=lambda: self._switch_forecast_tab("16 Days"),
            **btn_style
        )

    def open_settings_modal(self):
        """MANDATORY: Open clean tk.Toplevel settings dialog built with standard tk.Frame, tk.Label, and tk.Button widgets."""
        self.show_settings_popover = True
        modal = tk.Toplevel(self)
        modal.title("SkyCast — Settings & Controls")
        modal.geometry("380x490")
        modal.resizable(False, False)
        modal.configure(bg="#0f172a")
        modal.transient(self)
        modal.grab_set()

        try:
            mx = self.winfo_x() + (self.winfo_width() - 380) // 2
            my = self.winfo_y() + (self.winfo_height() - 490) // 2
            modal.geometry(f"+{max(mx, 50)}+{max(my, 50)}")
        except Exception:
            pass

        btn_style = {
            "bd": 0,
            "relief": "flat",
            "highlightthickness": 0,
            "bg": "#334155",
            "fg": "#ffffff",
            "activebackground": "#475569",
            "activeforeground": "#ffffff",
            "cursor": "hand2"
        }

        # Header Frame
        hdr_frame = tk.Frame(modal, bg="#1e293b", padx=16, pady=12)
        hdr_frame.pack(fill="x")
        lbl_title = tk.Label(hdr_frame, text="⚙ Settings & Controls", font=("Segoe UI", 13, "bold"), bg="#1e293b", fg="#38BDF8")
        lbl_title.pack(side="left")

        def close_modal():
            self.show_settings_popover = False
            modal.destroy()
            self._render_all_panels()

        modal.protocol("WM_DELETE_WINDOW", close_modal)
        btn_close = tk.Button(hdr_frame, text="✕", font=("Segoe UI", 11, "bold"), command=close_modal, **btn_style)
        btn_close.pack(side="right")

        content = tk.Frame(modal, bg="#0f172a", padx=18, pady=12)
        content.pack(fill="both", expand=True)

        # 1. Temperature Units
        lbl_u = tk.Label(content, text="TEMPERATURE UNITS", font=("Segoe UI", 9, "bold"), bg="#0f172a", fg="#94A3B8")
        lbl_u.pack(anchor="w", pady=(0, 6))

        u_frame = tk.Frame(content, bg="#0f172a")
        u_frame.pack(fill="x", pady=(0, 12))

        def set_unit(unit):
            self._set_temp_unit(unit)
            update_unit_buttons()

        btn_c = tk.Button(u_frame, text="°C  Celsius", font=("Segoe UI", 10, "bold"), command=lambda: set_unit("celsius"), **btn_style)
        btn_c.pack(side="left", expand=True, fill="x", padx=(0, 4))
        btn_f = tk.Button(u_frame, text="°F  Fahrenheit", font=("Segoe UI", 10, "bold"), command=lambda: set_unit("fahrenheit"), **btn_style)
        btn_f.pack(side="right", expand=True, fill="x", padx=(4, 0))

        def update_unit_buttons():
            cur = self.units.get("temp", "celsius")
            btn_c.config(bg="#0284c7" if cur == "celsius" else "#334155")
            btn_f.config(bg="#0284c7" if cur == "fahrenheit" else "#334155")
        update_unit_buttons()

        # 2. Atmospheric Weather Theme Previews (F2)
        lbl_p = tk.Label(content, text="ATMOSPHERIC PREVIEW MODES (F2)", font=("Segoe UI", 9, "bold"), bg="#0f172a", fg="#94A3B8")
        lbl_p.pack(anchor="w", pady=(4, 6))

        p_frame = tk.Frame(content, bg="#0f172a")
        p_frame.pack(fill="x", pady=(0, 8))

        presets_list = [
            ("☀️ Clear Day", "Clear — Day"),
            ("🌙 Clear Night", "Clear — Night"),
            ("🌧️ Rain", "Rain — Day"),
            ("⛈️ Thunder", "Thunderstorm — Night"),
            ("❄️ Snow", "Snow — Day"),
            ("🌫️ Fog", "Fog — Dawn"),
            ("⛅ Overcast", "Overcast — Evening"),
            ("🌧️ Drizzle", "Drizzle — Day"),
        ]

        for i, (txt, key) in enumerate(presets_list):
            row = i // 2
            col = i % 2
            p_btn = tk.Button(
                p_frame,
                text=txt,
                font=("Segoe UI", 9),
                command=lambda k=key: self._apply_preview_by_label(k),
                **btn_style
            )
            p_btn.grid(row=row, column=col, sticky="ew", padx=3, pady=3)
        p_frame.columnconfigure(0, weight=1)
        p_frame.columnconfigure(1, weight=1)

        # Restore Live Weather Button
        btn_live = tk.Button(
            content,
            text="🔄 Restore Live Weather",
            font=("Segoe UI", 9, "bold"),
            bg="#065f46",
            fg="#ffffff",
            activebackground="#047857",
            activeforeground="#ffffff",
            bd=0, relief="flat", highlightthickness=0, cursor="hand2",
            command=lambda: [self.return_to_live_weather(), close_modal()]
        )
        btn_live.pack(fill="x", pady=(4, 12))

        # 3. Storage & Favorites
        lbl_s = tk.Label(content, text="DATA & CACHE", font=("Segoe UI", 9, "bold"), bg="#0f172a", fg="#94A3B8")
        lbl_s.pack(anchor="w", pady=(2, 6))

        def clear_cache_click():
            self._clear_cache()
            btn_cache.config(text="✓ Offline Cache Cleared!", bg="#065f46")

        btn_cache = tk.Button(
            content,
            text="🗑 Clear Offline Cache",
            font=("Segoe UI", 9),
            command=clear_cache_click,
            **btn_style
        )
        btn_cache.pack(fill="x", pady=(0, 6))

        def reset_favs_click():
            self._reset_favorites_to_defaults()
            btn_fav.config(text="✓ Indian Favourites Restored!", bg="#065f46")

        btn_fav = tk.Button(
            content,
            text="🔄 Reset Favourites to Indian Metros",
            font=("Segoe UI", 9),
            command=reset_favs_click,
            **btn_style
        )
        btn_fav.pack(fill="x", pady=(0, 8))

    def _on_search_focus_in(self, event):
        if self._placeholder_active:
            self._placeholder_active = False
            self.search_var.set("")
            self.search_entry.config(fg="#FFFFFF")

    def _on_search_focus_out(self, event):
        if not self.search_var.get().strip():
            self._placeholder_active = True
            self.search_var.set("Search City...")
            self.search_entry.config(fg="#94A3B8")

    def _on_search_key(self, event):
        if event.keysym in ("Return", "Escape", "Up", "Down"):
            return
        query = self.search_var.get().strip()
        if len(query) < 2:
            self._close_search_dropdown()
            return

        if self.search_debounce_id:
            self.after_cancel(self.search_debounce_id)
        self.search_debounce_id = self.after(300, lambda: self._fetch_autocomplete(query))

    def _fetch_autocomplete(self, query: str):
        def on_success(results):
            def apply():
                self.search_suggestions = results[:5]
                self.show_search_dropdown = len(results) > 0
                self._render_all_panels()
            self.dispatch_to_main_thread(apply)

        def on_error(err):
            print(f"[SkyCast Search Error]: {err}")

        self.api_client.search_cities_async(query, on_success, on_error)

    def _on_search_enter(self, event):
        query = self.search_var.get().strip()
        if not query or self._placeholder_active:
            return
        # If dropdown has suggestions, pick top one
        if self.search_suggestions:
            self._select_city(self.search_suggestions[0])
            return

        # Direct search lookup
        self.is_loading = True
        self._render_all_panels()

        def on_success(results):
            def apply():
                if results:
                    self._select_city(results[0])
                else:
                    self.show_error_banner(f'City "{query}" not found. Please check spelling.')
                    self.is_loading = False
                    self._render_all_panels()
            self.dispatch_to_main_thread(apply)

        def on_error(err):
            def apply():
                self.show_error_banner(f"Search error: {err}")
                self.is_loading = False
                self._render_all_panels()
            self.dispatch_to_main_thread(apply)

        self.api_client.search_cities_async(query, on_success, on_error)

    def _select_city(self, city_dict: Dict[str, Any]):
        self.is_preview_mode = False
        self.forced_wallpaper = None
        self._close_search_dropdown()
        self.current_city = city_dict
        self.storage.set_last_city(city_dict)
        self.search_var.set("")
        self._placeholder_active = True
        self.search_entry.config(fg="#94A3B8")
        self.focus_set()
        self.load_weather_for_city(city_dict)

    def _close_search_dropdown(self):
        self.show_search_dropdown = False
        self.search_suggestions = []
        self._render_all_panels()

    def _on_canvas_click(self, event):
        """Close dropdown and popovers when clicking outside."""
        cx, cy = event.x, event.y

        if self.show_search_dropdown:
            self._close_search_dropdown()

        if self.show_settings_popover:
            x1, y1, x2, y2 = self.settings_popover_bbox
            if not (x1 <= cx <= x2 and y1 <= cy <= y2):
                gear_x = getattr(self, "_last_gear_x", 0)
                if abs(cx - gear_x) > 20 or abs(cy - 38) > 20:
                    self.show_settings_popover = False
                    self._render_all_panels()

        if self.show_about_popover:
            x1, y1, x2, y2 = self.about_popover_bbox
            if not (x1 <= cx <= x2 and y1 <= cy <= y2):
                logo_x = getattr(self, "_last_logo_x", 0)
                if abs(cx - logo_x) > 55 or abs(cy - 38) > 20:
                    self.show_about_popover = False
                    self._render_all_panels()

    # ========================================================================
    # Weather Data Loading
    # ========================================================================
    def load_weather_for_city(self, city_dict: Dict[str, Any]):
        lat = city_dict.get("latitude") or city_dict.get("lat")
        lon = city_dict.get("longitude") or city_dict.get("lon")
        if lat is None or lon is None:
            return

        self.is_loading = True
        self._render_all_panels()

        def on_success(data):
            def apply():
                self.weather_data = data
                self.storage.save_cache(data)

                # Theme resolution based on real WMO and local day/night
                curr = data.get("current", {})
                wmo = curr.get("weather_code", 0)
                is_day = curr.get("is_day", 1)
                temp_c = curr.get("temperature_2m", 15.0)

                self.current_theme = resolve_theme(wmo, is_day=is_day, temp_c=temp_c)
                self.last_updated_time = time.time()
                anim_name = self._get_anim_for_wmo(wmo, is_day)
                self.animator.set_animation(anim_name)
                clear_panel_cache()
                self.is_loading = False
                self._render_all_panels()
            self.dispatch_to_main_thread(apply)

        def on_error(err):
            def apply():
                cached = self.storage.get_cache()
                if cached:
                    self.weather_data = cached
                    curr = cached.get("current", {})
                    wmo = curr.get("weather_code", 0)
                    is_day = curr.get("is_day", 1)
                    self.current_theme = resolve_theme(wmo, is_day=is_day, temp_c=curr.get("temperature_2m", 15.0))
                    self.animator.set_animation(self._get_anim_for_wmo(wmo, is_day))
                    self.show_error_banner("⚠️ No connection — showing last saved data")
                else:
                    self.show_error_banner(f"Could not load weather: {err}")
                self.is_loading = False
                self._render_all_panels()
            self.dispatch_to_main_thread(apply)

        temp_u = self.units.get("temp", "celsius")
        wind_u = self.units.get("wind", "kmh")
        self.api_client.get_weather_async(lat, lon, temp_u, wind_u, on_success, on_error)

    def _get_anim_for_wmo(self, wmo: int, is_day: int) -> str:
        """Map Open-Meteo WMO weather code & daytime to active canvas particle animation."""
        if wmo in (95, 96, 99):
            return "thunderstorm"
        elif wmo in (51, 53, 55, 56, 57):
            return "drizzle"
        elif wmo in (61, 63, 65, 66, 67, 80, 81, 82):
            return "rain"
        elif wmo in (71, 73, 75, 77, 85, 86):
            return "snow"
        elif wmo in (45, 48):
            return "fog"
        elif is_day == 0 and wmo in (0, 1):
            return "stars"
        else:
            return "clouds"

    def _tick_update_timer(self):
        """1-minute interval ticker for 'Updated X min ago' and 10-minute auto-refresh."""
        if not self.winfo_exists():
            return
        elapsed_mins = int((time.time() - self.last_updated_time) / 60)
        if elapsed_mins >= 10:
            self.refresh_weather()
        else:
            self._render_all_panels()
        self.after(60000, self._tick_update_timer)

    def refresh_weather(self):
        """Trigger an instant manual refresh of live weather data and favorites."""
        self.is_preview_mode = False
        self.forced_wallpaper = None
        self.last_updated_time = time.time()
        self.load_weather_for_city(self.current_city)
        self._load_favorites_weather()

    def _load_favorites_weather(self):
        """Asynchronously load live weather metrics for saved favorite cities."""
        favs = self.storage.get_favorites()
        if not favs:
            self.favorites_weather = []
            return

        results = []
        for f in favs:
            try:
                lat = f.get("latitude", 0.0)
                lon = f.get("longitude", 0.0)
                # Quick fetch
                temp_u = self.units.get("temp", "celsius")
                wind_u = self.units.get("wind", "kmh")
                # Threaded fetch
                def fetch_city(city_entry=f):
                    try:
                        w_data = self.api_client.get_weather_data(city_entry["latitude"], city_entry["longitude"], temp_u, wind_u)
                        curr = w_data.get("current", {})
                        t_val = round(curr.get("temperature_2m", 0))
                        t_sym = "°F" if temp_u == "fahrenheit" else "°C"
                        wmo = curr.get("weather_code", 0)
                        info = get_weather_info(wmo, curr.get("is_day", 1))

                        updated = dict(city_entry)
                        updated["temp"] = f"{t_val}{t_sym}"
                        updated["condition"] = info.get("condition", "Clear")
                        updated["icon"] = get_icon_for_wmo(wmo, curr.get("is_day", 1))

                        def update_fav():
                            # Replace or append in favorites_weather
                            self.favorites_weather = [
                                updated if x.get("name") == updated.get("name") else x
                                for x in self.favorites_weather
                            ]
                            if not any(x.get("name") == updated.get("name") for x in self.favorites_weather):
                                self.favorites_weather.append(updated)
                            self._render_all_panels()
                        self.dispatch_to_main_thread(update_fav)
                    except Exception:
                        pass

                th = threading.Thread(target=fetch_city, daemon=True)
                th.start()
            except Exception:
                pass

    def _on_select_favorite_city(self, city_dict: Dict[str, Any]):
        self._select_city(city_dict)

    def _on_remove_favorite_city(self, city_name: str):
        self.storage.remove_favorite(city_name)
        self.favorites_weather = [f for f in self.favorites_weather if f.get("name") != city_name]
        self._render_all_panels()

    def _on_toggle_current_favorite(self):
        curr_name = self.current_city.get("name", "")
        if not curr_name:
            return
        if self.storage.is_favorite(curr_name):
            self.storage.remove_favorite(curr_name)
        else:
            self.storage.add_favorite(self.current_city)
        self._load_favorites_weather()
        self._render_all_panels()

    def _toggle_units(self):
        cur_temp = self.units.get("temp", "celsius")
        new_temp = "fahrenheit" if cur_temp == "celsius" else "celsius"
        self.storage.set_unit("temp", new_temp)
        self.units = self.storage.get_units()
        self.load_weather_for_city(self.current_city)
        self._load_favorites_weather()

    def show_error_banner(self, message: str):
        self.error_banner_text = message
        if self.error_banner_id:
            self.after_cancel(self.error_banner_id)
        self.error_banner_id = self.after(4500, self._clear_error_banner)
        self._render_all_panels()

    def _clear_error_banner(self):
        self.error_banner_text = None
        self._render_all_panels()

    # ========================================================================
    # Text Drawing with Shadow (Readability Guarantee)
    # ========================================================================
    def _draw_shadow_text(self, x: int, y: int, text: str, font: Any,
                          fill: str = "#FFFFFF",
                          shadow_color: str = "#090D16",
                          offset: Tuple[int, int] = (1, 1),
                          anchor: str = "w",
                          tags: str = "ui_element",
                          width: int = 0):
        """Draw crisp text with a subtle dark shadow for readability on any glass."""
        if shadow_color:
            self.canvas.create_text(
                x + offset[0], y + offset[1],
                text=text, font=font,
                fill=shadow_color,
                anchor=anchor,
                tags=tags,
                width=width
            )
        return self.canvas.create_text(
            x, y,
            text=text, font=font,
            fill=fill,
            anchor=anchor,
            tags=tags,
            width=width
        )

    # ========================================================================
    # Main Frosted Glass Rendering Pipeline
    # ========================================================================
    def _render_all_panels(self):
        w = max(self.canvas.winfo_width(), 800)
        h = max(self.canvas.winfo_height(), 600)

        # Clear existing visual items
        self.canvas.delete("glass_panel")
        self.canvas.delete("ui_element")
        self.canvas.delete("bg_image")
        self.canvas.delete("overlay")
        self.canvas.delete("overlay_glass")
        self._icon_refs.clear()

        # Update typography scale based on width
        is_compact = (w < 950)
        self.fonts["city_title"].config(size=16 if is_compact else 20)
        self.fonts["tile_val"].config(size=22 if is_compact else 26)
        self.fonts["h2"].config(size=12 if is_compact else 13)
        self.fonts["body"].config(size=9 if is_compact else 10)
        self.fonts["body_bold"].config(size=9 if is_compact else 10)
        self.fonts["small"].config(size=8 if is_compact else 9)
        self.fonts["small_bold"].config(size=8 if is_compact else 9)

        # 1. Background image (photo wallpaper if present, else procedural gradient)
        bg_dir = os.path.join(ROOT_DIR, "desktop", "assets", "backgrounds")
        curr = self.weather_data.get("current", {}) if self.weather_data else {}
        wmo = curr.get("weather_code", 0)
        is_day = curr.get("is_day", 1)

        if self.forced_wallpaper:
            bg_candidates = [self.forced_wallpaper]
        elif wmo in (95, 96, 99):
            bg_candidates = ["rain_night.jpg", "cloudy.jpg"]
        elif wmo in (71, 73, 75, 77, 85, 86):
            bg_candidates = ["snow.jpg", "cloudy.jpg"]
        elif wmo in (45, 48):
            bg_candidates = ["fog.jpg", "cloudy.jpg"]
        elif is_day == 0:
            bg_candidates = ["clear_night.jpg", "rain_night.jpg"]
        elif wmo in (61, 63, 65, 66, 67, 80, 81, 82, 51, 53, 55):
            bg_candidates = ["rain_night.jpg", "cloudy.jpg"]
        else:
            bg_candidates = ["partly_cloudy.jpg", "clear_day.jpg", "cloudy.jpg"]

        loaded_bg = None
        for cand in bg_candidates:
            if not cand:
                continue
            p = os.path.join(bg_dir, cand)
            if os.path.isfile(p):
                try:
                    raw_img = Image.open(p).convert("RGB")
                    img_w, img_h = raw_img.size
                    scale = max(w / img_w, h / img_h)
                    new_w, new_h = int(img_w * scale), int(img_h * scale)
                    scaled = raw_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    left = (new_w - w) // 2
                    top = (new_h - h) // 2
                    cropped = scaled.crop((left, top, left + w, top + h))
                    loaded_bg = self._apply_photo_tint(cropped)
                    break
                except Exception:
                    pass

        if loaded_bg:
            self.bg_pil_image = loaded_bg
        else:
            self.bg_pil_image = generate_procedural_background(
                w, h,
                self.current_theme["gradient_top"],
                self.current_theme["gradient_bottom"]
            )
        self.bg_photo = ImageTk.PhotoImage(self.bg_pil_image)
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw", tags="bg_image")

        # 2. Top Navigation Bar
        self._draw_top_bar(w)

        # 3. 3-Column Geometry Calculation
        pad = 16 if is_compact else 20
        gap = 10 if is_compact else 14
        top_y = 74 if is_compact else 78
        avail_h = h - top_y - pad

        avail_w = w - (pad * 2) - (gap * 2)
        col1_w = int(avail_w * 0.37)
        col2_w = int(avail_w * 0.38)
        col3_w = avail_w - col1_w - col2_w

        col1_x = pad
        col2_x = col1_x + col1_w + gap
        col3_x = col2_x + col2_w + gap

        # Row heights: Row 1 = 48%, Row 2 = remaining
        row1_h = int(avail_h * 0.48)
        row2_y = top_y + row1_h + gap
        row2_h = avail_h - row1_h - gap

        # 4. Draw Left Column Hero Weather Card (Real Live Data)
        self._draw_hero_card(col1_x, top_y, col1_w, row1_h, is_compact)

        # 5. Draw Middle Column Forecast Tabs & Mini-Cards & Trend Chart
        self._draw_forecast_card(col2_x, top_y, col2_w, row1_h, is_compact)

        # 6. Draw Lower Span: Overview Grid (6 rich tiles)
        overview_w = col1_w + gap + col2_w
        self._draw_overview_grid(col1_x, row2_y, overview_w, row2_h, is_compact)

        # 7. Draw Right Column: Other Cities Favorites
        is_fav = self.storage.is_favorite(self.current_city.get("name", ""))
        self.other_cities_panel.draw(
            bg_image=self.bg_pil_image,
            x=col3_x, y=top_y,
            width=col3_w, height=avail_h,
            cities_data=self.favorites_weather if self.favorites_weather else self.storage.get_favorites(),
            theme=self.current_theme,
            fonts=self.fonts,
            is_current_favorite=is_fav
        )

        # 8. Autocomplete Dropdown (if active)
        if self.show_search_dropdown and self.search_suggestions:
            self._draw_search_dropdown(w)

        # 9. Notification Error Banner (if any)
        if self.error_banner_text:
            self._draw_notification_banner(w)

        # 10. F2 Preview Badge HUD (if active)
        if self.f2_badge_text:
            self._draw_f2_badge(w)

        # 11. Loading Overlay (if loading)
        if self.is_loading:
            self._draw_loading_overlay(w, h)

        # 12. Settings Popover (if open)
        if self.show_settings_popover:
            self._draw_settings_popover(w)

        # 13. About / Quick Switcher Popover (if open)
        if self.show_about_popover:
            self._draw_about_popover(w)

        # Stacking order: bg_image at bottom, then anim_particle, then glass panels, then ui_element, then overlay
        self.canvas.tag_lower("bg_image")
        if self.canvas.find_withtag("anim_particle"):
            self.canvas.tag_lower("anim_particle")
            self.canvas.tag_raise("anim_particle", "bg_image")
        if self.canvas.find_withtag("glass_panel"):
            self.canvas.tag_raise("glass_panel")
        self.canvas.tag_raise("ui_element")
        self.canvas.tag_raise("overlay_glass")
        self.canvas.tag_raise("overlay")

    # ========================================================================
    # Top Navigation Glass Bar
    # ========================================================================
    def _draw_top_bar(self, w: int):
        pad = 20
        bar_h = 48
        bar_w = w - (pad * 2)

        bar_photo = render_frosted_glass_panel(
            bg_image=self.bg_pil_image,
            x=pad, y=14,
            width=bar_w, height=bar_h,
            radius=24,
            blur_radius=18,
            tint_opacity=0.25,
            dark_overlay_opacity=0.35,
            border_opacity=110
        )
        self.canvas.create_image(pad, 14, image=bar_photo, anchor="nw", tags="glass_panel")

        # Clean Custom Vector Weather Logo (Sun behind Cloud) + Brand Title directly on canvas
        logo_sz = 26
        logo_img = get_weather_icon_image("partly", size=logo_sz)
        self._icon_refs.append(logo_img)
        logo_tag = "btn_brand_logo"
        self._last_logo_x = pad + 20
        self.canvas.create_image(pad + 20, 38, image=logo_img, tags=("ui_element", logo_tag))
        
        # Render "SkyCast" directly on canvas for 100% transparent background
        self._draw_shadow_text(pad + 38, 38, "SkyCast", font=self.fonts["logo"], fill="#FFFFFF", anchor="w", tags=("ui_element", logo_tag))

        self.canvas.tag_bind(logo_tag, "<Button-1>", lambda e: self._toggle_about_popover())
        self.canvas.tag_bind(logo_tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind(logo_tag, "<Leave>", lambda e: self.canvas.config(cursor=""))

        # Pill Search Field
        pill_w = min(max(int(w * 0.32), 220), 340)
        pill_x = w // 2 - (pill_w // 2)
        pill_h = 32
        pill_y = 22

        pill_glass = render_frosted_glass_panel(
            bg_image=self.bg_pil_image,
            x=pill_x, y=pill_y,
            width=pill_w, height=pill_h,
            radius=16,
            blur_radius=14,
            tint_opacity=0.30,
            dark_overlay_opacity=0.45,
            border_opacity=120
        )
        self.canvas.create_image(pill_x, pill_y, image=pill_glass, anchor="nw", tags="glass_panel")

        # Magnifying glass icon inside pill
        self._draw_shadow_text(pill_x + 12, pill_y + 16, "🔍", font=("Segoe UI", 11), fill="#94A3B8", anchor="w")

        # Match tk.Entry background dynamically to the frosted pill color behind it
        is_night = self.current_theme.get("time_phase") in ("night", "dusk")
        try:
            if self.bg_pil_image:
                sample_x = min(max(pill_x + 50, 0), self.bg_pil_image.width - 1)
                sample_y = min(max(pill_y + 16, 0), self.bg_pil_image.height - 1)
                pixel = self.bg_pil_image.getpixel((sample_x, sample_y))
                # Gaussian blur + dark overlay (45% #0F172A) + tint (30% white)
                r1 = int(pixel[0] * 0.55 + 15 * 0.45)
                g1 = int(pixel[1] * 0.55 + 23 * 0.45)
                b1 = int(pixel[2] * 0.55 + 42 * 0.45)
                r2 = int(r1 * 0.70 + 255 * 0.30)
                g2 = int(g1 * 0.70 + 255 * 0.30)
                b2 = int(b1 * 0.70 + 255 * 0.30)
                pill_bg_hex = f"#{min(max(r2, 0), 255):02x}{min(max(g2, 0), 255):02x}{min(max(b2, 0), 255):02x}"
            else:
                pill_bg_hex = "#2c3a4f" if is_night else "#4a6583"
        except Exception:
            pill_bg_hex = "#2c3a4f" if is_night else "#4a6583"

        self.search_entry.config(bg=pill_bg_hex)

        # Reposition Entry Widget
        entry_w = pill_w - 42
        self.canvas.create_window(pill_x + 32, pill_y + 6, window=self.search_entry, anchor="nw", width=entry_w, height=20, tags="ui_element")

        # Button background styling matched to exact slate-blue glass hex color (#4a6583 day / #2c3a4f night)
        glass_btn_bg = "#2c3a4f" if is_night else "#4a6583"
        glass_btn_hover = "#3e526e" if is_night else "#5d7d9f"
        for btn in (self.btn_refresh, self.btn_unit_toggle, self.btn_settings):
            btn.config(bg=glass_btn_bg, activebackground=glass_btn_hover)

        # Settings Icon (tk.Button)
        gear_x = pad + bar_w - 20
        self._last_gear_x = gear_x
        self.canvas.create_window(gear_x - 14, 38, window=self.btn_settings, anchor="center", width=28, height=26, tags="ui_element")

        # Unit Toggle Button (tk.Button)
        unit_x = gear_x - 42
        t_sym = "°F" if self.units.get("temp") == "fahrenheit" else "°C"
        self.btn_unit_toggle.config(text=f"[{t_sym}]")
        self.canvas.create_window(unit_x - 20, 38, window=self.btn_unit_toggle, anchor="center", width=42, height=26, tags="ui_element")

        # Interactive Refresh Button (tk.Button)
        refresh_x = unit_x - 44
        self.canvas.create_window(refresh_x - 14, 38, window=self.btn_refresh, anchor="center", width=28, height=26, tags="ui_element")

        # "Last updated X min ago" rendered directly on canvas for 100% transparent background
        elapsed_mins = int((time.time() - self.last_updated_time) / 60)
        if elapsed_mins <= 0:
            upd_str = "Updated just now"
        elif elapsed_mins == 1:
            upd_str = "Updated 1m ago"
        else:
            upd_str = f"Updated {elapsed_mins}m ago"

        upd_x = refresh_x - 32
        self._draw_shadow_text(upd_x, 38, upd_str, font=self.fonts["small_bold"], fill="#CBD5E1", anchor="e", tags="ui_element")

    def _draw_search_dropdown(self, w: int):
        """Floating autocomplete suggestions card showing City, Region, Country."""
        drop_w = min(max(int(w * 0.44), 380), 480)
        drop_x = w // 2 - (drop_w // 2)
        drop_y = 58
        item_h = 36
        drop_h = len(self.search_suggestions) * item_h + 8

        drop_photo = render_frosted_glass_panel(
            bg_image=self.bg_pil_image,
            x=drop_x, y=drop_y,
            width=drop_w, height=drop_h,
            radius=16,
            blur_radius=20,
            tint_opacity=0.35,
            dark_overlay_opacity=0.60,
            border_opacity=130
        )
        self.canvas.create_image(drop_x, drop_y, image=drop_photo, anchor="nw", tags="overlay_glass")

        for i, s in enumerate(self.search_suggestions):
            sy = drop_y + 4 + i * item_h
            tag = f"sug_item_{i}"

            c_name = s.get("name", "")
            c_admin = s.get("admin1", "")
            c_country = s.get("country", "")
            if c_admin and c_country:
                display_str = f"{c_name}, {c_admin}, {c_country}"
            elif c_country:
                display_str = f"{c_name}, {c_country}"
            else:
                display_str = c_name

            truncated = truncate_text(self.fonts["small_bold"], display_str, drop_w - 32)

            self.canvas.create_text(
                drop_x + 14, sy + item_h // 2,
                text=f"📍 {truncated}",
                font=self.fonts["small_bold"],
                fill="#FFFFFF",
                anchor="w",
                tags=("ui_element", "overlay", tag)
            )

            self.canvas.tag_bind(tag, "<Button-1>", lambda e, item=s: self._select_city(item))
            self.canvas.tag_bind(tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
            self.canvas.tag_bind(tag, "<Leave>", lambda e: self.canvas.config(cursor=""))

    def _get_current_local_time_str(self) -> str:
        """Returns live local clock for the current city using UTC offset."""
        if self.weather_data and "utc_offset_seconds" in self.weather_data:
            try:
                offset_sec = self.weather_data.get("utc_offset_seconds", 0)
                tz = datetime.timezone(datetime.timedelta(seconds=offset_sec))
                now_utc = datetime.datetime.now(datetime.timezone.utc)
                local_dt = now_utc.astimezone(tz)
                return local_dt.strftime("%I:%M %p")
            except Exception:
                pass
        return datetime.datetime.now().strftime("%I:%M %p")

    # ========================================================================
    # Left Column: Hero Current Weather Card (Live Data)
    # ========================================================================
    def _draw_hero_card(self, x: int, y: int, w: int, h: int, is_compact: bool = False):
        glass_photo = render_frosted_glass_panel(
            bg_image=self.bg_pil_image,
            x=x, y=y,
            width=w, height=h,
            radius=20,
            blur_radius=18,
            tint_opacity=0.25,
            dark_overlay_opacity=0.35,
            border_opacity=110
        )
        self.canvas.create_image(x, y, image=glass_photo, anchor="nw", tags="glass_panel")

        pad_x = 16 if is_compact else 22
        avail_card_w = w - (pad_x * 2)

        # 1. Location Pin Inline + City Name (Ellipsis truncation only for excessively long city names)
        c_name = self.current_city.get("name", "Chennai")
        c_country = self.current_city.get("country", "")
        city_display = f"📍 {c_name}, {c_country}" if c_country else f"📍 {c_name}"
        avail_title_w = avail_card_w - 6

        title_font = self.fonts["city_title"]
        if title_font.measure(city_display) > avail_title_w:
            alt_font = tkfont.Font(family="Segoe UI", size=16 if is_compact else 17, weight="bold")
            if alt_font.measure(city_display) <= avail_title_w:
                title_font = alt_font
                final_city_text = city_display
            else:
                final_city_text = truncate_text(alt_font, city_display, avail_title_w)
                title_font = alt_font
        else:
            final_city_text = city_display

        self._draw_shadow_text(
            x + pad_x, y + (22 if is_compact else 26),
            final_city_text,
            title_font,
            fill="#FFFFFF",
            anchor="w"
        )

        # 2. Local Time on its own line below with clear spacing (32px vertical offset)
        local_time_str = self._get_current_local_time_str()

        self._draw_shadow_text(
            x + pad_x, y + (52 if is_compact else 58),
            local_time_str,
            self.fonts["body_bold"],
            fill="#E2E8F0",
            anchor="w"
        )

        # 3. Big Temperature & Condition with real measured width
        curr = self.weather_data.get("current", {}) if self.weather_data else {}
        temp_val = round(curr.get("temperature_2m", 12)) if curr else 12
        temp_sym = "°F" if self.units.get("temp") == "fahrenheit" else "°C"
        temp_str = f"{temp_val}{temp_sym}"

        # Scale temperature font proportionally to card width:
        temp_font_size = max(min(int(w * 0.115), 48), 28)
        self.fonts["temp_huge"].config(size=temp_font_size)

        temp_y = y + (98 if is_compact else 114)
        self._draw_shadow_text(
            x + pad_x, temp_y,
            temp_str,
            self.fonts["temp_huge"],
            fill="#FFFFFF",
            anchor="w"
        )

        # Measure temperature width to place condition cleanly without overlap
        temp_w = self.fonts["temp_huge"].measure(temp_str)
        cond_x = x + pad_x + temp_w + 14
        avail_cond_w = max(w - (cond_x - x) - pad_x, 60)

        # Real condition and feels like
        wmo = curr.get("weather_code", 0)
        info = get_weather_info(wmo, curr.get("is_day", 1))
        cond_raw = curr.get("forced_cond") or info.get("condition", "Clear Sky")
        feels_val = round(curr.get("apparent_temperature", temp_val)) if curr else temp_val
        feels_str = f"Feels like {feels_val}{temp_sym}"

        # If condition text doesn't fit, shrink its font or wrap to 2 lines — NEVER cut off with '...'!
        cond_font = self.fonts["h2"]
        if cond_font.measure(cond_raw) > avail_cond_w:
            cond_font = tkfont.Font(family="Segoe UI", size=10, weight="bold")
            if cond_font.measure(cond_raw) > avail_cond_w:
                words = cond_raw.split()
                if len(words) >= 2:
                    mid = len(words) // 2
                    cond_raw = " ".join(words[:mid]) + "\n" + " ".join(words[mid:])

        self._draw_shadow_text(
            cond_x, temp_y - 12,
            cond_raw,
            cond_font,
            fill="#FFFFFF",
            anchor="w"
        )
        self._draw_shadow_text(
            cond_x, temp_y + 14,
            feels_str,
            self.fonts["body_bold"],
            fill="#E2E8F0",
            anchor="w"
        )

        # 4. Summary Sentence directly under temperature block with bottom padding guarantee
        daily = self.weather_data.get("daily", {}) if self.weather_data else {}
        summary_text = self._generate_weather_summary(curr, daily, cond_raw)
        avail_summary_w = avail_card_w - 6
        summary_y = temp_y + (32 if is_compact else 38)

        self._draw_shadow_text(
            x + pad_x, summary_y,
            summary_text,
            font=self.fonts["body"],
            fill="#F8FAFC",
            anchor="nw",
            width=avail_summary_w
        )

    def _generate_weather_summary(self, curr: Dict[str, Any], daily: Dict[str, Any], cond_name: str) -> str:
        """Intelligently synthesizes a natural one-line atmospheric summary sentence."""
        if curr.get("forced_summary"):
            return curr["forced_summary"]
        if not curr:
            return "Clear skies and moderate temperatures expected throughout the day."
        wind = round(curr.get("wind_speed_10m", 10))
        precip = 0
        if daily and "precipitation_probability_max" in daily:
            probs = daily["precipitation_probability_max"]
            if probs:
                precip = probs[0] or 0

        clean_cond = cond_name.replace("\n", " ").lower()
        if wind < 10:
            w_str = "Gentle breeze"
        elif wind < 25:
            w_str = f"Light winds ({wind} km/h)"
        else:
            w_str = f"Gusty winds ({wind} km/h)"

        if precip > 50:
            r_str = f"High chance of rain ({precip}%)."
        elif precip > 20:
            r_str = f"Slight chance of showers ({precip}%)."
        else:
            r_str = "Clear conditions expected into the evening."

        return f"{w_str} and {clean_cond}. {r_str}"

    # ========================================================================
    # Middle Column: Forecast Tabs, Mini-Cards, and 24-Hour Trend Chart
    # ========================================================================
    def _draw_forecast_card(self, x: int, y: int, w: int, h: int, is_compact: bool = False):
        glass_photo = render_frosted_glass_panel(
            bg_image=self.bg_pil_image,
            x=x, y=y,
            width=w, height=h,
            radius=20,
            blur_radius=18,
            tint_opacity=0.25,
            dark_overlay_opacity=0.35,
            border_opacity=110
        )
        self.canvas.create_image(x, y, image=glass_photo, anchor="nw", tags="glass_panel")

        # Tabs Header: Today | Week | 16 Days (Native tk.Button Widgets)
        tab_y = y + (12 if is_compact else 16)
        tab_x = x + (12 if is_compact else 18)
        tabs_map = [
            ("Today", self.btn_tab_today, 52 if is_compact else 65),
            ("Week", self.btn_tab_week, 48 if is_compact else 60),
            ("16 Days", self.btn_tab_16days, 60 if is_compact else 75)
        ]

        cur_x = tab_x
        tab_gap = 6 if is_compact else 10
        btn_h = 24 if is_compact else 28
        is_night = self.current_theme.get("time_phase") in ("night", "dusk")
        glass_btn_bg = "#2c3a4f" if is_night else "#4a6583"
        glass_btn_hover = "#3e526e" if is_night else "#5d7d9f"

        for name, btn_widget, tw in tabs_map:
            is_active = (name == self.active_tab)
            if is_active:
                btn_widget.config(bg="#0284c7", fg="#ffffff", activebackground="#0369a1")
            else:
                btn_widget.config(bg=glass_btn_bg, fg="#cbd5e1", activebackground=glass_btn_hover)
            self.canvas.create_window(cur_x, tab_y, window=btn_widget, anchor="nw", width=tw, height=btn_h, tags="ui_element")
            cur_x += tw + tab_gap

        # Sub-content depending on active tab
        if self.active_tab == "Today":
            self._draw_today_hourly_and_trend(x, y, w, h, is_compact)
        elif self.active_tab == "Week":
            self._draw_week_forecast(x, y, w, h, is_compact, days_count=7)
        else: # "16 Days"
            self._draw_week_forecast(x, y, w, h, is_compact, days_count=16)

    def _switch_forecast_tab(self, tab_name: str):
        self.active_tab = tab_name
        self._render_all_panels()

    def _draw_today_hourly_and_trend(self, x: int, y: int, w: int, h: int, is_compact: bool):
        """Displays 6 hourly cards with rain chance, plus the 24-hour temperature trend line chart."""
        card_count = 5 if is_compact else 6
        mini_top = y + (44 if is_compact else 50)
        mini_h = 104 if is_compact else 114

        pad_m = 10 if is_compact else 14
        gap_m = 6 if is_compact else 8
        card_w = (w - (pad_m * 2) - (gap_m * (card_count - 1))) // card_count

        hourly = self.weather_data.get("hourly", {}) if self.weather_data else {}
        daily = self.weather_data.get("daily", {}) if self.weather_data else {}
        sr_hour = 6
        ss_hour = 18
        if daily.get("sunrise") and len(daily["sunrise"]) > 0:
            try:
                sr_hour = int(daily["sunrise"][0].split("T")[1][:2])
            except Exception:
                pass
        if daily.get("sunset") and len(daily["sunset"]) > 0:
            try:
                ss_hour = int(daily["sunset"][0].split("T")[1][:2])
            except Exception:
                pass

        h_times = hourly.get("time", [])[:card_count]
        h_temps = hourly.get("temperature_2m", [])[:card_count]
        h_wmos = hourly.get("weather_code", [])[:card_count]
        h_rains = hourly.get("precipitation_probability", [])[:card_count]
        h_is_days = hourly.get("is_day", [])[:card_count]

        temp_sym = "°F" if self.units.get("temp") == "fahrenheit" else "°C"

        for i in range(card_count):
            mx = x + pad_m + i * (card_w + gap_m)
            m_photo = render_frosted_glass_panel(
                bg_image=self.bg_pil_image,
                x=mx, y=mini_top,
                width=card_w, height=mini_h,
                radius=14 if is_compact else 16,
                blur_radius=12,
                tint_opacity=0.20,
                dark_overlay_opacity=0.30,
                border_opacity=85
            )
            self.canvas.create_image(mx, mini_top, image=m_photo, anchor="nw", tags="glass_panel")

            # Time
            time_label = f"{9 + i}:00"
            if i < len(h_times) and "T" in h_times[i]:
                try:
                    time_label = h_times[i].split("T")[1][:5]
                except Exception:
                    pass

            self._draw_shadow_text(
                mx + card_w // 2, mini_top + 13,
                time_label,
                self.fonts["small_bold"],
                fill="#FFFFFF",
                anchor="center"
            )

            # Icon
            wmo = h_wmos[i] if i < len(h_wmos) else 0
            is_d = h_is_days[i] if i < len(h_is_days) else 1
            try:
                hour_val = int(time_label.split(":")[0])
                if hour_val < sr_hour or hour_val >= ss_hour:
                    is_d = 0
            except Exception:
                pass
            icon_kind = get_icon_for_wmo(wmo, is_d)
            icon_sz = min(max(card_w - 14, 20), 28)
            icon_img = get_weather_icon_image(icon_kind, size=icon_sz)
            self._icon_refs.append(icon_img)
            self.canvas.create_image(
                mx + card_w // 2, mini_top + 42,
                image=icon_img,
                tags="ui_element"
            )

            # Rain probability
            rain_val = h_rains[i] if i < len(h_rains) else 0
            self._draw_shadow_text(
                mx + card_w // 2, mini_top + 70,
                f"{rain_val}%",
                self.fonts["small_bold"],
                fill="#38BDF8",
                anchor="center"
            )

            # Temperature
            t_val = round(h_temps[i]) if i < len(h_temps) else 15
            self._draw_shadow_text(
                mx + card_w // 2, mini_top + mini_h - 13,
                f"{t_val}{temp_sym}",
                self.fonts["body_bold"],
                fill="#FFFFFF",
                anchor="center"
            )

        # Draw 24-Hour Temperature Trend Chart
        chart_y = mini_top + mini_h + 10
        chart_h = h - (chart_y - y) - 12
        if chart_h >= 45:
            self._draw_24h_trend_chart(x + pad_m, chart_y, w - (pad_m * 2), chart_h)

    def _draw_24h_trend_chart(self, cx: int, cy: int, cw: int, ch: int):
        """Draws a smooth 24-hour temperature curve with spline line and high/low points."""
        hourly = self.weather_data.get("hourly", {}) if self.weather_data else {}
        temps = hourly.get("temperature_2m", [])[:24]
        if not temps or len(temps) < 4:
            temps = [12, 12, 11, 11, 10, 10, 11, 13, 15, 17, 18, 19, 19, 18, 17, 16, 15, 14, 13, 13, 12, 12, 12, 11]

        min_t = min(temps) - 1
        max_t = max(temps) + 1
        span_t = max(max_t - min_t, 1)

        points = []
        n = len(temps)
        step_x = cw / max(n - 1, 1)

        for i, t in enumerate(temps):
            px = cx + i * step_x
            py = cy + ch - 16 - ((t - min_t) / span_t) * (ch - 24)
            points.extend([px, py])

        # Draw subtle grid horizontal baseline
        self.canvas.create_line(cx, cy + ch - 14, cx + cw, cy + ch - 14, fill="#334155", width=1, tags="ui_element")

        # Smooth spline curve
        self.canvas.create_line(points, smooth=True, fill="#38BDF8", width=2.5, tags="ui_element")

        # Label min and max points
        high_idx = temps.index(max(temps))
        low_idx = temps.index(min(temps))
        temp_sym = "°F" if self.units.get("temp") == "fahrenheit" else "°C"

        hx = cx + high_idx * step_x
        hy = cy + ch - 16 - ((temps[high_idx] - min_t) / span_t) * (ch - 24)
        self.canvas.create_oval(hx - 3, hy - 3, hx + 3, hy + 3, fill="#FBBF24", outline="#FFFFFF", width=1, tags="ui_element")
        hx_label = max(min(hx, cx + cw - 32), cx + 32)
        hy_label = max(hy - 10, cy + 10)
        self._draw_shadow_text(hx_label, hy_label, f"High {round(temps[high_idx])}{temp_sym}", font=self.fonts["chart_label"], fill="#FBBF24", anchor="center")

        lx = cx + low_idx * step_x
        ly = cy + ch - 16 - ((temps[low_idx] - min_t) / span_t) * (ch - 24)
        self.canvas.create_oval(lx - 3, ly - 3, lx + 3, ly + 3, fill="#38BDF8", outline="#FFFFFF", width=1, tags="ui_element")
        lx_label = max(min(lx, cx + cw - 32), cx + 32)
        low_label_y = ly - 12 if ly >= (cy + ch - 26) else min(ly + 10, cy + ch - 22)
        self._draw_shadow_text(lx_label, low_label_y, f"Low {round(temps[low_idx])}{temp_sym}", font=self.fonts["chart_label"], fill="#38BDF8", anchor="center")

        # Time markers at bottom (00:00, 06:00, 12:00, 18:00)
        for hour_step in (0, 6, 12, 18):
            tx = cx + hour_step * step_x
            self._draw_shadow_text(tx, cy + ch - 4, f"{hour_step:02d}:00", font=self.fonts["small"], fill="#94A3B8", anchor="center")

    def _draw_week_forecast(self, x: int, y: int, w: int, h: int, is_compact: bool, days_count: int = 7):
        """Displays daily forecast cards (7 days or extended 16 days)."""
        daily = self.weather_data.get("daily", {}) if self.weather_data else {}
        all_times = daily.get("time", [])[:days_count]
        all_maxs = daily.get("temperature_2m_max", [])[:days_count]
        all_mins = daily.get("temperature_2m_min", [])[:days_count]
        all_wmos = daily.get("weather_code", [])[:days_count]
        all_rains = daily.get("precipitation_probability_max", [])[:days_count]

        visible_count = min(days_count, 6 if not is_compact else 5)
        start_idx = 0

        if days_count == 16 and len(all_times) > visible_count:
            max_pages = (len(all_times) + visible_count - 1) // visible_count
            cur_page = getattr(self, "sixteen_days_page", 0) % max_pages
            start_idx = cur_page * visible_count
            end_idx = min(start_idx + visible_count, len(all_times))

            d_times = all_times[start_idx:end_idx]
            d_maxs = all_maxs[start_idx:end_idx]
            d_mins = all_mins[start_idx:end_idx]
            d_wmos = all_wmos[start_idx:end_idx]
            d_rains = all_rains[start_idx:end_idx]
            visible_count = len(d_times)

            nav_y = y + (12 if is_compact else 16)
            next_tag = "btn_16d_next"
            prev_tag = "btn_16d_prev"
            self._draw_shadow_text(x + w - 18, nav_y + 14, "▶", self.fonts["small_bold"], fill="#38BDF8", anchor="e", tags=("ui_element", next_tag))
            self._draw_shadow_text(x + w - 38, nav_y + 14, "◀", self.fonts["small_bold"], fill="#38BDF8", anchor="e", tags=("ui_element", prev_tag))
            self._draw_shadow_text(x + w - 54, nav_y + 14, f"Page {cur_page+1}/{max_pages}", self.fonts["small"], fill="#94A3B8", anchor="e")

            def next_page():
                self.sixteen_days_page = (cur_page + 1) % max_pages
                self._render_all_panels()

            def prev_page():
                self.sixteen_days_page = (cur_page - 1 + max_pages) % max_pages
                self._render_all_panels()

            self.canvas.tag_bind(next_tag, "<Button-1>", lambda e: next_page())
            self.canvas.tag_bind(next_tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
            self.canvas.tag_bind(next_tag, "<Leave>", lambda e: self.canvas.config(cursor=""))

            self.canvas.tag_bind(prev_tag, "<Button-1>", lambda e: prev_page())
            self.canvas.tag_bind(prev_tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
            self.canvas.tag_bind(prev_tag, "<Leave>", lambda e: self.canvas.config(cursor=""))
        else:
            d_times = all_times[:visible_count]
            d_maxs = all_maxs[:visible_count]
            d_mins = all_mins[:visible_count]
            d_wmos = all_wmos[:visible_count]
            d_rains = all_rains[:visible_count]
        pad_m = 10 if is_compact else 14
        gap_m = 6 if is_compact else 8
        card_w = (w - (pad_m * 2) - (gap_m * (visible_count - 1))) // visible_count
        card_top = y + (46 if is_compact else 54)
        card_h = h - (56 if is_compact else 66)

        temp_sym = "°F" if self.units.get("temp") == "fahrenheit" else "°C"

        for i in range(visible_count):
            mx = x + pad_m + i * (card_w + gap_m)
            m_photo = render_frosted_glass_panel(
                bg_image=self.bg_pil_image,
                x=mx, y=card_top,
                width=card_w, height=card_h,
                radius=14 if is_compact else 16,
                blur_radius=12,
                tint_opacity=0.20,
                dark_overlay_opacity=0.30,
                border_opacity=85
            )
            self.canvas.create_image(mx, card_top, image=m_photo, anchor="nw", tags="glass_panel")

            # Day Name (e.g. Mon, Tue)
            day_name = f"Day {i+1}"
            if i < len(d_times):
                try:
                    dt = datetime.date.fromisoformat(d_times[i])
                    day_name = "Today" if i == 0 else dt.strftime("%a")
                except Exception:
                    pass

            self._draw_shadow_text(
                mx + card_w // 2, card_top + 16,
                day_name,
                self.fonts["small_bold"],
                fill="#FFFFFF",
                anchor="center"
            )

            # Icon
            wmo = d_wmos[i] if i < len(d_wmos) else 0
            icon_kind = get_icon_for_wmo(wmo, is_day=1)
            icon_sz = min(max(card_w - 14, 22), 34)
            icon_img = get_weather_icon_image(icon_kind, size=icon_sz)
            self._icon_refs.append(icon_img)
            self.canvas.create_image(
                mx + card_w // 2, card_top + int(card_h * 0.42),
                image=icon_img,
                tags="ui_element"
            )

            # Max rain chance
            rain_val = d_rains[i] if i < len(d_rains) else 0
            self._draw_shadow_text(
                mx + card_w // 2, card_top + int(card_h * 0.68),
                f"{rain_val}%",
                self.fonts["small_bold"],
                fill="#38BDF8",
                anchor="center"
            )

            # High / Low temps
            max_t = round(d_maxs[i]) if i < len(d_maxs) else 16
            min_t = round(d_mins[i]) if i < len(d_mins) else 8
            self._draw_shadow_text(
                mx + card_w // 2, card_top + card_h - 16,
                f"{max_t}°/{min_t}°",
                self.fonts["body_bold"],
                fill="#FFFFFF",
                anchor="center"
            )

    # ========================================================================
    # Lower Span: Overview Grid (6 rich tiles with real API data)
    # ========================================================================
    def _draw_overview_grid(self, x: int, y: int, w: int, h: int, is_compact: bool = False):
        self._draw_shadow_text(
            x + 5, y + 8,
            "Overview",
            self.fonts["h2"],
            fill="#FFFFFF",
            anchor="w"
        )

        grid_y = y + (26 if is_compact else 30)
        grid_h = h - (26 if is_compact else 30)

        curr = self.weather_data.get("current", {}) if self.weather_data else {}
        daily = self.weather_data.get("daily", {}) if self.weather_data else {}
        aqi_data = self.weather_data.get("air_quality", {}) if self.weather_data else {}

        # 3 Columns x 2 Rows grid
        cols = 3
        rows = 2
        gap_x = 8 if is_compact else 12
        gap_y = 8 if is_compact else 10
        tile_w = (w - gap_x * (cols - 1)) // cols
        tile_h = (grid_h - gap_y * (rows - 1)) // rows

        # --- Row 1, Col 1: Humidity ---
        hum_val = curr.get("relative_humidity_2m", 67)
        dew_pt = round(curr.get("dew_point_2m", 8))
        self._draw_overview_tile_humidity(x, grid_y, tile_w, tile_h, hum_val, dew_pt, is_compact)

        # --- Row 1, Col 2: UV Index ---
        uv_val = round(curr.get("uv_index", 4), 1)
        self._draw_overview_tile_uv(x + tile_w + gap_x, grid_y, tile_w, tile_h, uv_val, is_compact)

        # --- Row 1, Col 3: Visibility ---
        vis_meters = curr.get("visibility", 10000)
        vis_km = round(vis_meters / 1000, 1) if vis_meters >= 1000 else round(vis_meters / 1000, 2)
        self._draw_overview_tile_visibility(x + (tile_w + gap_x) * 2, grid_y, tile_w, tile_h, vis_km, is_compact)

        # --- Row 2, Col 1: Wind & Direction ---
        r2_y = grid_y + tile_h + gap_y
        wind_spd = round(curr.get("wind_speed_10m", 12))
        wind_deg = curr.get("wind_direction_10m", 0)
        self._draw_overview_tile_wind(x, r2_y, tile_w, tile_h, wind_spd, wind_deg, is_compact)

        # --- Row 2, Col 2: Pressure & Cloud Cover ---
        press_val = round(curr.get("surface_pressure", 1013))
        clouds = curr.get("cloud_cover", 40)
        self._draw_overview_tile_pressure(x + tile_w + gap_x, r2_y, tile_w, tile_h, press_val, clouds, is_compact)

        # --- Row 2, Col 3: Air Quality & Solar Times ---
        raw_aqi = aqi_data.get("us_aqi") if aqi_data else None
        if raw_aqi is None or not isinstance(raw_aqi, (int, float)):
            raw_aqi = aqi_data.get("aqi", aqi_data.get("european_aqi", 50)) if aqi_data else 50
        try:
            aqi_val = int(min(max(float(raw_aqi), 0), 500))
        except Exception:
            aqi_val = 50
        pm25_val = aqi_data.get("pm2_5", 12.0) if aqi_data else 12.0
        sunrise_iso = daily.get("sunrise", [""])[0] if daily else ""
        sunset_iso = daily.get("sunset", [""])[0] if daily else ""
        self._draw_overview_tile_aqi(x + (tile_w + gap_x) * 2, r2_y, tile_w, tile_h, aqi_val, pm25_val, sunrise_iso, sunset_iso, is_compact)

    def _draw_overview_tile_humidity(self, tx, ty, tw, th, hum_val, dew_pt, is_compact):
        photo = render_frosted_glass_panel(self.bg_pil_image, tx, ty, tw, th, radius=16, blur_radius=16, tint_opacity=0.25, dark_overlay_opacity=0.35)
        self.canvas.create_image(tx, ty, image=photo, anchor="nw", tags="glass_panel")
        self._draw_shadow_text(tx + 14, ty + 15, "Humidity", self.fonts["body_bold"], fill="#FFFFFF", anchor="w")

        drop_sz = min(max(int(th * 0.44), 36), 56)
        drop_img = get_weather_icon_image("humidity", size=drop_sz)
        self._icon_refs.append(drop_img)
        self.canvas.create_image(tx + tw - 16 - drop_sz // 2, ty + th // 2, image=drop_img, tags="ui_element")

        self._draw_shadow_text(tx + 14, ty + th // 2 + 6, f"{hum_val}%", self.fonts["tile_val"], fill="#FFFFFF", anchor="w")
        self._draw_shadow_text(tx + 14, ty + th - 13, f"Dew point: {dew_pt}°", self.fonts["small_bold"], fill="#38BDF8", anchor="w")

    def _draw_overview_tile_uv(self, tx, ty, tw, th, uv_val, is_compact):
        photo = render_frosted_glass_panel(self.bg_pil_image, tx, ty, tw, th, radius=16, blur_radius=16, tint_opacity=0.25, dark_overlay_opacity=0.35)
        self.canvas.create_image(tx, ty, image=photo, anchor="nw", tags="glass_panel")
        self._draw_shadow_text(tx + 14, ty + 15, "UV Index", self.fonts["body_bold"], fill="#FFFFFF", anchor="w")

        # Vertical multi-color thermometer gradient bar
        bar_x = tx + tw - 28
        bar_y1 = ty + 18
        bar_y2 = ty + th - 18
        bar_w = 10
        self.canvas.create_rectangle(bar_x + 1, bar_y1 + 1, bar_x + bar_w + 1, bar_y2 + 1, fill="#090D16", outline="", tags="ui_element")
        self.canvas.create_rectangle(bar_x, bar_y1, bar_x + bar_w, bar_y2, fill="#1E293B", outline="#475569", tags="ui_element")

        ratio = min(max(uv_val / 11.0, 0.05), 1.0)
        fill_y = bar_y2 - int((bar_y2 - bar_y1) * ratio)
        fill_col = "#10B981" if uv_val < 3 else ("#F59E0B" if uv_val < 6 else ("#EF4444" if uv_val < 8 else "#8B5CF6"))
        self.canvas.create_rectangle(bar_x + 1, fill_y, bar_x + bar_w - 1, bar_y2 - 1, fill=fill_col, outline="", tags="ui_element")

        uv_cat = "Low" if uv_val < 3 else ("Moderate" if uv_val < 6 else ("Very High" if uv_val < 8 else "Extreme"))
        self._draw_shadow_text(tx + 14, ty + th // 2 + 6, f"{uv_val}", self.fonts["tile_val"], fill="#FFFFFF", anchor="w")
        self._draw_shadow_text(tx + 14, ty + th - 13, uv_cat, self.fonts["small_bold"], fill=fill_col, anchor="w")

    def _draw_overview_tile_visibility(self, tx, ty, tw, th, vis_km, is_compact):
        photo = render_frosted_glass_panel(self.bg_pil_image, tx, ty, tw, th, radius=16, blur_radius=16, tint_opacity=0.25, dark_overlay_opacity=0.35)
        self.canvas.create_image(tx, ty, image=photo, anchor="nw", tags="glass_panel")
        self._draw_shadow_text(tx + 14, ty + 15, "Visibility", self.fonts["body_bold"], fill="#FFFFFF", anchor="w")

        vis_sz = min(max(int(th * 0.44), 36), 56)
        vis_img = get_weather_icon_image("visibility", size=vis_sz)
        self._icon_refs.append(vis_img)
        self.canvas.create_image(tx + tw - 16 - vis_sz // 2, ty + th // 2, image=vis_img, tags="ui_element")

        self._draw_shadow_text(tx + 14, ty + th // 2 + 6, f"{vis_km} km", self.fonts["tile_val"], fill="#FFFFFF", anchor="w")
        vis_status = "Clear & unobstructed" if vis_km >= 10 else ("Haze affecting range" if vis_km >= 5 else "Dense fog / mist")
        self._draw_shadow_text(tx + 14, ty + th - 13, vis_status, self.fonts["small_bold"], fill="#CBD5E1", anchor="w")

    def _draw_overview_tile_wind(self, tx, ty, tw, th, wind_spd, wind_deg, is_compact):
        photo = render_frosted_glass_panel(self.bg_pil_image, tx, ty, tw, th, radius=16, blur_radius=16, tint_opacity=0.25, dark_overlay_opacity=0.35)
        self.canvas.create_image(tx, ty, image=photo, anchor="nw", tags="glass_panel")
        self._draw_shadow_text(tx + 14, ty + 15, "Wind", self.fonts["body_bold"], fill="#FFFFFF", anchor="w")

        wind_sz = min(max(int(th * 0.44), 36), 56)
        wind_img = get_weather_icon_image("wind", size=wind_sz)
        self._icon_refs.append(wind_img)
        self.canvas.create_image(tx + tw - 16 - wind_sz // 2, ty + th // 2, image=wind_img, tags="ui_element")

        # Cardinal direction
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        idx = int((wind_deg + 22.5) / 45.0) % 8
        cardinal = directions[idx]
        wind_unit = self.units.get("wind", "kmh")
        disp_unit = "km/h" if wind_unit == "kmh" else wind_unit

        self._draw_shadow_text(tx + 14, ty + th // 2 + 6, f"{wind_spd} {disp_unit}", self.fonts["tile_val"], fill="#FFFFFF", anchor="w")
        self._draw_shadow_text(tx + 14, ty + th - 13, f"Blowing from {cardinal}", self.fonts["small_bold"], fill="#CBD5E1", anchor="w")

    def _draw_overview_tile_pressure(self, tx, ty, tw, th, press_val, clouds, is_compact):
        photo = render_frosted_glass_panel(self.bg_pil_image, tx, ty, tw, th, radius=16, blur_radius=16, tint_opacity=0.25, dark_overlay_opacity=0.35)
        self.canvas.create_image(tx, ty, image=photo, anchor="nw", tags="glass_panel")
        self._draw_shadow_text(tx + 14, ty + 15, "Pressure", self.fonts["body_bold"], fill="#FFFFFF", anchor="w")

        baro_sz = min(max(int(th * 0.44), 36), 56)
        baro_img = get_weather_icon_image("barometer", size=baro_sz)
        self._icon_refs.append(baro_img)
        self.canvas.create_image(tx + tw - 16 - baro_sz // 2, ty + th // 2, image=baro_img, tags="ui_element")

        self._draw_shadow_text(tx + 14, ty + th // 2 + 6, f"{press_val} hPa", self.fonts["tile_val"], fill="#FFFFFF", anchor="w")
        self._draw_shadow_text(tx + 14, ty + th - 13, f"Cloud cover: {clouds}%", self.fonts["small_bold"], fill="#38BDF8", anchor="w")

    def _draw_overview_tile_aqi(self, tx, ty, tw, th, aqi_val, pm25_val, sunrise_iso, sunset_iso, is_compact):
        photo = render_frosted_glass_panel(self.bg_pil_image, tx, ty, tw, th, radius=16, blur_radius=16, tint_opacity=0.25, dark_overlay_opacity=0.35)
        self.canvas.create_image(tx, ty, image=photo, anchor="nw", tags="glass_panel")
        self._draw_shadow_text(tx + 14, ty + 15, "Air Quality", self.fonts["body_bold"], fill="#FFFFFF", anchor="w")

        # Compact diamond icon positioned cleanly in upper right corner (size 24px)
        aqi_sz = 22 if is_compact else 24
        aqi_img = get_weather_icon_image("aqi", size=aqi_sz)
        self._icon_refs.append(aqi_img)
        self.canvas.create_image(tx + tw - 16 - aqi_sz // 2, ty + 18, image=aqi_img, tags="ui_element")

        # Resolve AQI rating level & category (0-500 US/Indian standard scale)
        try:
            val_int = int(min(max(float(aqi_val or 50), 0), 500))
        except Exception:
            val_int = 50
        aqi_level = get_aqi_level(val_int)
        cat_name = aqi_level.get("label", aqi_level.get("category", "Good"))
        col = aqi_level.get("color", "#10B981")

        # Display integer AQI value (f"{val_int} AQI") in exact same 26pt bold font as other 5 overview cards
        val_str = f"{val_int} AQI"
        self._draw_shadow_text(tx + 14, ty + th // 2 + 3, val_str, self.fonts["tile_val"], fill="#FFFFFF", anchor="w")

        # Category label cleanly aligned beside the AQI value
        val_w = self.fonts["tile_val"].measure(val_str)
        cat_display = "Sensitive" if "Sensitive" in cat_name else ("V.Unhealthy" if "Very" in cat_name else cat_name)
        status_x = tx + 14 + val_w + 8
        if status_x + self.fonts["small_bold"].measure(cat_display) <= tx + tw - 12:
            self._draw_shadow_text(status_x, ty + th // 2 + 6, cat_display, self.fonts["small_bold"], fill=col, anchor="w")
        else:
            self._draw_shadow_text(tx + tw - 14, ty + th // 2 + 6, cat_display, self.fonts["small_bold"], fill=col, anchor="e")

        # Bottom Subtitle: PM2.5: {pm25} µg/m³ and solar times
        pm_str = f"PM2.5: {pm25_val} µg/m³" if pm25_val is not None else "PM2.5: -- µg/m³"

        sun_short = ""
        if "T" in sunrise_iso and "T" in sunset_iso:
            try:
                sr = sunrise_iso.split("T")[1][:5]
                ss = sunset_iso.split("T")[1][:5]
                sun_short = f"☀️{sr} 🌙{ss}"
            except Exception:
                pass

        pm_w = self.fonts["small_bold"].measure(pm_str)
        sun_w = self.fonts["small_bold"].measure(sun_short) if sun_short else 0

        self._draw_shadow_text(tx + 14, ty + th - 13, pm_str, self.fonts["small_bold"], fill="#38BDF8", anchor="w")
        if sun_short and (pm_w + sun_w + 36 <= tw):
            self._draw_shadow_text(tx + tw - 14, ty + th - 13, sun_short, self.fonts["small_bold"], fill="#CBD5E1", anchor="e")

    # ========================================================================
    # Loading Spinner Overlay & Error Notification Banner
    # ========================================================================
    def _draw_loading_overlay(self, w: int, h: int):
        card_w = 280
        card_h = 80
        cx = w // 2 - card_w // 2
        cy = h // 2 - card_h // 2

        photo = render_frosted_glass_panel(self.bg_pil_image, cx, cy, card_w, card_h, radius=18, blur_radius=22, tint_opacity=0.35, dark_overlay_opacity=0.55)
        self.canvas.create_image(cx, cy, image=photo, anchor="nw", tags="overlay_glass")

        # Animated spinning arc indicator
        spinner_angle = getattr(self, "_spinner_angle", 0)
        self._spinner_angle = (spinner_angle + 30) % 360
        self.canvas.create_arc(
            cx + 20, cy + 24, cx + 54, cy + 58,
            start=spinner_angle, extent=280,
            style="arc", outline="#38BDF8", width=3,
            tags="overlay"
        )

        self._draw_shadow_text(
            cx + 68, cy + 28,
            "Updating SkyCast...",
            self.fonts["body_bold"],
            fill="#FFFFFF",
            anchor="w",
            tags="overlay"
        )
        self._draw_shadow_text(
            cx + 68, cy + 50,
            "Fetching live Open-Meteo metrics",
            self.fonts["small"],
            fill="#38BDF8",
            anchor="w",
            tags="overlay"
        )

    def _draw_notification_banner(self, w: int):
        banner_w = min(w - 40, 520)
        bx = w // 2 - banner_w // 2
        by = 72
        bh = 38

        banner_photo = render_frosted_glass_panel(
            self.bg_pil_image, bx, by, banner_w, bh,
            radius=16, blur_radius=18, tint_opacity=0.35, dark_overlay_opacity=0.60, border_opacity=130
        )
        self.canvas.create_image(bx, by, image=banner_photo, anchor="nw", tags="overlay_glass")

        display_text = self.error_banner_text
        if not display_text.startswith("⚠️"):
            display_text = f"⚠️  {display_text}"

        self._draw_shadow_text(
            bx + banner_w // 2, by + bh // 2,
            display_text,
            self.fonts["small_bold"],
            fill="#FBBF24",
            anchor="center",
            tags="overlay"
        )
        self.canvas.tag_bind("overlay", "<Button-1>", lambda e: self._clear_error_banner())

    def show_f2_badge(self, text: str):
        """Displays on-screen F2 preview mode badge HUD."""
        self.f2_badge_text = text
        if self.f2_badge_id:
            self.after_cancel(self.f2_badge_id)
        self.f2_badge_id = self.after(3500, self._clear_f2_badge)
        self._render_all_panels()

    def _clear_f2_badge(self):
        self.f2_badge_text = None
        self._render_all_panels()

    def _draw_f2_badge(self, w: int):
        card_w = min(w - 60, 480)
        cx = w // 2 - card_w // 2
        cy = 72
        ch = 36
        photo = render_frosted_glass_panel(
            self.bg_pil_image, cx, cy, card_w, ch,
            radius=18, blur_radius=16, tint_opacity=0.35, dark_overlay_opacity=0.60
        )
        self.canvas.create_image(cx, cy, image=photo, anchor="nw", tags="overlay_glass")
        self._draw_shadow_text(
            cx + card_w // 2, cy + ch // 2,
            self.f2_badge_text,
            self.fonts["small_bold"],
            fill="#38BDF8",
            anchor="center",
            tags="overlay"
        )

    def _apply_photo_tint(self, base_img: Image.Image) -> Image.Image:
        """Applies dynamic time-of-day x weather color tinting over background image."""
        bw, bh = base_img.size
        curr = self.weather_data.get("current", {}) if self.weather_data else {}
        is_day = curr.get("is_day", 1)
        wmo = curr.get("weather_code", 0)

        if wmo in (95, 96, 99):
            tint = (30, 27, 75, 75)       # Electric storm violet
        elif wmo in (71, 73, 75, 77, 85, 86):
            tint = (224, 242, 254, 45)     # Ice blue snow
        elif wmo in (45, 48):
            tint = (148, 163, 184, 80)     # Misty fog slate
        elif is_day == 0:
            tint = (15, 23, 42, 100)       # Deep obsidian night
        else:
            tint = (56, 189, 248, 25)      # Crisp sky daylight

        overlay = Image.new("RGBA", (bw, bh), tint)
        return Image.alpha_composite(base_img.convert("RGBA"), overlay).convert("RGB")

    def _fade_to_background(self, target_img: Image.Image, duration_ms: int = 1200, steps: int = 12):
        """Performs a smooth 1-1.5 second cross-fade between background photos."""
        if self.bg_pil_image is None or self.is_fading:
            self.bg_pil_image = target_img
            clear_panel_cache()
            self._render_all_panels()
            return

        self.is_fading = True
        old_img = self.bg_pil_image.copy()
        step_interval = duration_ms // steps

        def step_fade(current_step=1):
            if not self.winfo_exists():
                return
            alpha = current_step / steps
            try:
                blended = Image.blend(old_img, target_img, alpha)
                self.bg_pil_image = blended
                self.bg_photo = ImageTk.PhotoImage(blended)
                self.canvas.itemconfig("bg_image", image=self.bg_photo)
            except Exception:
                pass

            if current_step < steps:
                self.after(step_interval, lambda: step_fade(current_step + 1))
            else:
                self.bg_pil_image = target_img
                self.is_fading = False
                clear_panel_cache()
                self._render_all_panels()

        step_fade(1)

    def apply_preset(self, p: Dict[str, Any]):
        """Applies an atmospheric weather preset and updates UI immediately."""
        self.is_preview_mode = True
        self.show_f2_badge(f"🎮 [Preview]: {p['label']}")
        self.forced_wallpaper = p["wallpaper"]
        self.current_theme = resolve_theme(p["wmo"], is_day=p["is_day"], temp_c=float(p["temp"]))
        self.animator.set_animation(p["anim"])

        if not self.weather_data:
            self.weather_data = {}
        if "current" not in self.weather_data:
            self.weather_data["current"] = {}
        curr = self.weather_data["current"]
        curr["temperature_2m"] = p["temp"]
        curr["apparent_temperature"] = p["apparent"]
        curr["weather_code"] = p["wmo"]
        curr["is_day"] = p["is_day"]
        curr["forced_cond"] = p["cond"]
        curr["forced_summary"] = p["summary"]

        clear_panel_cache()
        self._render_all_panels()

    def _apply_preview_by_label(self, label: str):
        """Finds preset by label and applies it."""
        for p in PREVIEW_PRESETS:
            if p["label"] == label:
                self.apply_preset(p)
                return

    def return_to_live_weather(self):
        """Exits preview mode and returns to live API weather data."""
        self.is_preview_mode = False
        self.forced_wallpaper = None
        self.f2_badge_text = None
        if self.f2_badge_id:
            self.after_cancel(self.f2_badge_id)
            self.f2_badge_id = None
        clear_panel_cache()
        self.refresh_weather()

    def _toggle_preview_mode(self):
        """F2 preview mode: cycles through 8 diverse atmospheric weather presets."""
        curr_idx = getattr(self, "_preview_idx", 0)
        p = PREVIEW_PRESETS[curr_idx % len(PREVIEW_PRESETS)]
        self._preview_idx = curr_idx + 1
        self.apply_preset(p)

    def _toggle_settings_popover(self):
        """Toggles the frosted glass Settings popover menu."""
        self.show_settings_popover = not self.show_settings_popover
        if self.show_settings_popover:
            self.show_about_popover = False
        self._render_all_panels()

    def _draw_settings_popover(self, w: int):
        """Draws frosted glass settings popover menu with interactive controls."""
        pop_w = 310
        pop_h = 415
        pad = 20
        bar_w = w - (pad * 2)
        gear_x = pad + bar_w - 24
        pop_x = min(gear_x - pop_w + 16, w - pop_w - 16)
        pop_y = 62
        self.settings_popover_bbox = (pop_x, pop_y, pop_x + pop_w, pop_y + pop_h)

        glass_photo = render_frosted_glass_panel(
            bg_image=self.bg_pil_image,
            x=pop_x, y=pop_y,
            width=pop_w, height=pop_h,
            radius=18,
            blur_radius=22,
            tint_opacity=0.38,
            dark_overlay_opacity=0.65,
            border_opacity=140
        )
        self.canvas.create_image(pop_x, pop_y, image=glass_photo, anchor="nw", tags="overlay_glass")

        # Header Title & Close Button
        self._draw_shadow_text(pop_x + 18, pop_y + 22, "⚙  Settings & Controls", font=self.fonts["h2"], fill="#FFFFFF", anchor="w", tags="overlay")
        close_tag = "btn_close_settings"
        self._draw_shadow_text(pop_x + pop_w - 18, pop_y + 22, "✕", font=self.fonts["body_bold"], fill="#94A3B8", anchor="e", tags=("overlay", close_tag))
        self.canvas.tag_bind(close_tag, "<Button-1>", lambda e: self._toggle_settings_popover())
        self.canvas.tag_bind(close_tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind(close_tag, "<Leave>", lambda e: self.canvas.config(cursor=""))

        # Section 1: Temperature Units
        sec1_y = pop_y + 54
        self._draw_shadow_text(pop_x + 18, sec1_y, "TEMPERATURE UNIT", font=self.fonts["small_bold"], fill="#94A3B8", anchor="w", tags="overlay")

        cur_temp = self.units.get("temp", "celsius")
        btn_c_tag = "pop_btn_c"
        btn_f_tag = "pop_btn_f"

        b_w = (pop_w - 36 - 10) // 2
        b_h = 28
        b_y = sec1_y + 12

        # Draw °C button
        c_active = (cur_temp == "celsius")
        c_fill = "#0284C7" if c_active else "#1E293B"
        c_outline = "#38BDF8" if c_active else "#475569"
        c_text_col = "#FFFFFF" if c_active else "#CBD5E1"
        self.canvas.create_rectangle(pop_x + 18, b_y, pop_x + 18 + b_w, b_y + b_h, fill=c_fill, outline=c_outline, width=1.5 if c_active else 1, tags=("overlay", btn_c_tag))
        self._draw_shadow_text(pop_x + 18 + b_w // 2, b_y + b_h // 2, "°C  Celsius", font=self.fonts["small_bold"], fill=c_text_col, anchor="center", tags=("overlay", btn_c_tag))

        # Draw °F button
        f_x = pop_x + 18 + b_w + 10
        f_active = (cur_temp == "fahrenheit")
        f_fill = "#0284C7" if f_active else "#1E293B"
        f_outline = "#38BDF8" if f_active else "#475569"
        f_text_col = "#FFFFFF" if f_active else "#CBD5E1"
        self.canvas.create_rectangle(f_x, b_y, f_x + b_w, b_y + b_h, fill=f_fill, outline=f_outline, width=1.5 if f_active else 1, tags=("overlay", btn_f_tag))
        self._draw_shadow_text(f_x + b_w // 2, b_y + b_h // 2, "°F  Fahrenheit", font=self.fonts["small_bold"], fill=f_text_col, anchor="center", tags=("overlay", btn_f_tag))

        self.canvas.tag_bind(btn_c_tag, "<Button-1>", lambda e: self._set_temp_unit("celsius"))
        self.canvas.tag_bind(btn_c_tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind(btn_c_tag, "<Leave>", lambda e: self.canvas.config(cursor=""))

        self.canvas.tag_bind(btn_f_tag, "<Button-1>", lambda e: self._set_temp_unit("fahrenheit"))
        self.canvas.tag_bind(btn_f_tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind(btn_f_tag, "<Leave>", lambda e: self.canvas.config(cursor=""))

        # Section 2: Quick Theme & Weather Preview (F2 Themes)
        sec2_y = b_y + b_h + 18
        self._draw_shadow_text(pop_x + 18, sec2_y, "WEATHER THEME PREVIEWS (F2)", font=self.fonts["small_bold"], fill="#94A3B8", anchor="w", tags="overlay")

        themes = [
            ("☀️ Clear Day", "Clear — Day"),
            ("🌙 Clear Night", "Clear — Night"),
            ("🌧️ Rain", "Rain — Day"),
            ("⛈️ Thunder", "Thunderstorm — Night"),
            ("❄️ Snow", "Snow — Day"),
            ("🌫️ Fog", "Fog — Dawn"),
        ]

        th_cols = 3
        th_gap = 6
        th_w = (pop_w - 36 - (th_gap * (th_cols - 1))) // th_cols
        th_h = 28
        grid_y = sec2_y + 12

        for i, (btn_lbl, preset_key) in enumerate(themes):
            col_i = i % th_cols
            row_i = i // th_cols
            bx = pop_x + 18 + col_i * (th_w + th_gap)
            by = grid_y + row_i * (th_h + th_gap)
            t_tag = f"pop_theme_{i}"

            self.canvas.create_rectangle(bx, by, bx + th_w, by + th_h, fill="#1E293B", outline="#475569", width=1, tags=("overlay", t_tag))
            self._draw_shadow_text(bx + th_w // 2, by + th_h // 2, btn_lbl, font=self.fonts["small"], fill="#E2E8F0", anchor="center", tags=("overlay", t_tag))

            self.canvas.tag_bind(t_tag, "<Button-1>", lambda e, pkey=preset_key: self._apply_preview_by_label(pkey))
            self.canvas.tag_bind(t_tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
            self.canvas.tag_bind(t_tag, "<Leave>", lambda e: self.canvas.config(cursor=""))

        # Live Reset Button below theme grid
        live_y = grid_y + 2 * (th_h + th_gap) + 2
        live_tag = "pop_live_reset"
        is_preview = getattr(self, "is_preview_mode", False)
        live_fill = "#065F46" if not is_preview else "#1E293B"
        live_outline = "#10B981" if not is_preview else "#64748B"
        live_txt = "✓ Live Weather Active" if not is_preview else "🔄 Restore Live Weather"
        self.canvas.create_rectangle(pop_x + 18, live_y, pop_x + pop_w - 18, live_y + 26, fill=live_fill, outline=live_outline, width=1, tags=("overlay", live_tag))
        self._draw_shadow_text(pop_x + pop_w // 2, live_y + 13, live_txt, font=self.fonts["small_bold"], fill="#FFFFFF" if not is_preview else "#38BDF8", anchor="center", tags=("overlay", live_tag))
        self.canvas.tag_bind(live_tag, "<Button-1>", lambda e: self.return_to_live_weather())
        self.canvas.tag_bind(live_tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind(live_tag, "<Leave>", lambda e: self.canvas.config(cursor=""))

        # Section 3: Storage & Favorites Management
        sec3_y = live_y + 26 + 16
        self._draw_shadow_text(pop_x + 18, sec3_y, "STORAGE & FAVORITES", font=self.fonts["small_bold"], fill="#94A3B8", anchor="w", tags="overlay")

        cache_y = sec3_y + 12
        cache_tag = "pop_clear_cache"
        if self.cache_cleared_notice:
            c_fill = "#065F46"
            c_text = "✓ Offline Cache Cleared!"
            c_col = "#34D399"
        else:
            c_fill = "#1E293B"
            c_text = "🗑  Clear Offline Cache"
            c_col = "#F87171"

        self.canvas.create_rectangle(pop_x + 18, cache_y, pop_x + pop_w - 18, cache_y + 26, fill=c_fill, outline="#475569", width=1, tags=("overlay", cache_tag))
        self._draw_shadow_text(pop_x + pop_w // 2, cache_y + 13, c_text, font=self.fonts["small_bold"], fill=c_col, anchor="center", tags=("overlay", cache_tag))

        self.canvas.tag_bind(cache_tag, "<Button-1>", lambda e: self._clear_cache())
        self.canvas.tag_bind(cache_tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind(cache_tag, "<Leave>", lambda e: self.canvas.config(cursor=""))

        # Reset Favorites to Default Indian Metros
        fav_y = cache_y + 26 + 8
        fav_tag = "pop_reset_favs"
        if self.favs_reset_notice:
            f_fill = "#065F46"
            f_text = "✓ Indian Favourites Restored!"
            f_col = "#34D399"
        else:
            f_fill = "#1E293B"
            f_text = "🔄  Reset Favourites to Defaults"
            f_col = "#38BDF8"

        self.canvas.create_rectangle(pop_x + 18, fav_y, pop_x + pop_w - 18, fav_y + 26, fill=f_fill, outline="#475569", width=1, tags=("overlay", fav_tag))
        self._draw_shadow_text(pop_x + pop_w // 2, fav_y + 13, f_text, font=self.fonts["small_bold"], fill=f_col, anchor="center", tags=("overlay", fav_tag))

        self.canvas.tag_bind(fav_tag, "<Button-1>", lambda e: self._reset_favorites_to_defaults())
        self.canvas.tag_bind(fav_tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind(fav_tag, "<Leave>", lambda e: self.canvas.config(cursor=""))

    def _toggle_about_popover(self):
        """Toggles the frosted glass About / Info popover."""
        self.show_about_popover = not self.show_about_popover
        if self.show_about_popover:
            self.show_settings_popover = False
        self._render_all_panels()

    def _draw_about_popover(self, w: int):
        """Draws the About SkyCast popover menu when clicking the brand logo."""
        pop_w = 310
        pop_h = 246
        pad = 20
        pop_x = pad + 10
        pop_y = 62
        self.about_popover_bbox = (pop_x, pop_y, pop_x + pop_w, pop_y + pop_h)

        glass_photo = render_frosted_glass_panel(
            bg_image=self.bg_pil_image,
            x=pop_x, y=pop_y,
            width=pop_w, height=pop_h,
            radius=18,
            blur_radius=22,
            tint_opacity=0.38,
            dark_overlay_opacity=0.65,
            border_opacity=140
        )
        self.canvas.create_image(pop_x, pop_y, image=glass_photo, anchor="nw", tags="overlay_glass")

        # Header Title & Close Button
        logo_sz = 22
        logo_img = get_weather_icon_image("partly", size=logo_sz)
        self._icon_refs.append(logo_img)
        self.canvas.create_image(pop_x + 24, pop_y + 22, image=logo_img, tags="overlay")
        self._draw_shadow_text(pop_x + 40, pop_y + 22, "About SkyCast", font=self.fonts["h2"], fill="#FFFFFF", anchor="w", tags="overlay")

        close_tag = "btn_close_about"
        self._draw_shadow_text(pop_x + pop_w - 18, pop_y + 22, "✕", font=self.fonts["body_bold"], fill="#94A3B8", anchor="e", tags=("overlay", close_tag))
        self.canvas.tag_bind(close_tag, "<Button-1>", lambda e: self._toggle_about_popover())
        self.canvas.tag_bind(close_tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind(close_tag, "<Leave>", lambda e: self.canvas.config(cursor=""))

        # App Info
        self._draw_shadow_text(pop_x + 18, pop_y + 54, "SkyCast Desktop Edition v2.0", font=self.fonts["body_bold"], fill="#38BDF8", anchor="w", tags="overlay")
        self._draw_shadow_text(pop_x + 18, pop_y + 74, "Real-time atmospheric weather dashboard", font=self.fonts["small"], fill="#CBD5E1", anchor="w", tags="overlay")
        self._draw_shadow_text(pop_x + 18, pop_y + 90, "built with Python Tkinter & Pillow.", font=self.fonts["small"], fill="#CBD5E1", anchor="w", tags="overlay")

        # Technical Details
        c_name = self.current_city.get("name", "Chennai")
        items = [
            ("API Source", "Open-Meteo (Zero Secrets)"),
            ("Rendering", "Frosted Glassmorphism Canvas"),
            ("Animations", "30 FPS Particle Engine"),
            ("Home City", f"{c_name}, India"),
        ]

        dy = pop_y + 116
        for lbl, val in items:
            self._draw_shadow_text(pop_x + 18, dy, f"• {lbl}:", font=self.fonts["small_bold"], fill="#94A3B8", anchor="w", tags="overlay")
            self._draw_shadow_text(pop_x + 104, dy, val, font=self.fonts["small"], fill="#FFFFFF", anchor="w", tags="overlay")
            dy += 20

        # Shortcut hint
        hint_y = pop_y + pop_h - 18
        self._draw_shadow_text(pop_x + pop_w // 2, hint_y, "Tip: Press [F2] or click ⚙ to switch themes", font=self.fonts["small_bold"], fill="#FBBF24", anchor="center", tags="overlay")

    def _set_temp_unit(self, new_temp: str):
        """Sets temperature unit preference and refreshes weather data."""
        if self.units.get("temp") != new_temp:
            self.storage.set_unit("temp", new_temp)
            self.units = self.storage.get_units()
            self.load_weather_for_city(self.current_city)
            self._load_favorites_weather()
        self._render_all_panels()

    def _clear_cache(self):
        """Clears local settings offline weather cache and shows visual confirmation."""
        self.storage.save_cache(None)
        self.cache_cleared_notice = True
        self._render_all_panels()
        self.after(2500, self._reset_cache_notice)

    def _reset_cache_notice(self):
        """Resets the cache cleared confirmation state."""
        self.cache_cleared_notice = False
        if self.show_settings_popover:
            self._render_all_panels()

    def _reset_favorites_to_defaults(self):
        """Resets saved favorite cities back to default Indian cities."""
        self.storage.reset_favorites_to_defaults()
        self.favorites_weather = []
        self.favs_reset_notice = True
        self._load_favorites_weather()
        self._render_all_panels()
        self.after(2500, self._reset_favs_notice)

    def _reset_favs_notice(self):
        """Resets the favorites reset confirmation state."""
        self.favs_reset_notice = False
        if self.show_settings_popover:
            self._render_all_panels()

def main():
    try:
        app = SkyCastMainWindow()
        app.mainloop()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
