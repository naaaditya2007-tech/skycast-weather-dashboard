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

        # Build embedded search entry widget
        self._build_search_widget()

        # Load initial live weather
        self.load_weather_for_city(self.current_city)
        self._load_favorites_weather()

    def _init_fonts(self):
        """Configure crisp typography for high-DPI monitors."""
        self.fonts = {
            "logo": tkfont.Font(family="Segoe UI", size=15, weight="bold"),
            "city_title": tkfont.Font(family="Segoe UI", size=19, weight="bold"),
            "temp_huge": tkfont.Font(family="Segoe UI", size=48, weight="bold"),
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
        """Close dropdown when clicking outside search field."""
        if self.show_search_dropdown:
            self._close_search_dropdown()

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
                clear_panel_cache()
                self.is_loading = False
                self._render_all_panels()
            self.dispatch_to_main_thread(apply)

        def on_error(err):
            def apply():
                cached = self.storage.get_cache()
                if cached:
                    self.weather_data = cached
                    self.show_error_banner("Offline Mode — Displaying cached weather.")
                else:
                    self.show_error_banner(f"Could not load weather: {err}")
                self.is_loading = False
                self._render_all_panels()
            self.dispatch_to_main_thread(apply)

        temp_u = self.units.get("temp", "celsius")
        wind_u = self.units.get("wind", "kmh")
        self.api_client.get_weather_async(lat, lon, temp_u, wind_u, on_success, on_error)

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
        self._icon_refs.clear()

        # Update typography scale based on width
        is_compact = (w < 950)
        self.fonts["city_title"].config(size=16 if is_compact else 20)
        self.fonts["h2"].config(size=12 if is_compact else 13)
        self.fonts["body"].config(size=9 if is_compact else 10)
        self.fonts["body_bold"].config(size=9 if is_compact else 10)
        self.fonts["small"].config(size=8 if is_compact else 9)
        self.fonts["small_bold"].config(size=8 if is_compact else 9)

        # 1. Background image (photo wallpaper if present, else procedural gradient)
        bg_dir = os.path.join(ROOT_DIR, "desktop", "assets", "backgrounds")
        bg_candidates = [self.forced_wallpaper] if self.forced_wallpaper else ["partly_cloudy.jpg", "cloudy.jpg", "rain_night.jpg", "clear.jpg"]
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
                    dark_full = Image.new("RGBA", (w, h), (15, 23, 42, int(255 * 0.15)))
                    loaded_bg = Image.alpha_composite(cropped.convert("RGBA"), dark_full).convert("RGB")
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

        # 10. Loading Overlay (if loading)
        if self.is_loading:
            self._draw_loading_overlay(w, h)

        # Stacking order
        self.canvas.tag_lower("bg_image")
        self.canvas.tag_raise("glass_panel", "bg_image")
        self.canvas.tag_raise("ui_element", "glass_panel")
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

        # Hamburger + Brand Logo
        self._draw_shadow_text(pad + 20, 38, "☰", font=("Segoe UI", 14), fill="#FFFFFF", anchor="w")
        self._draw_shadow_text(pad + 48, 38, "SkyCast", font=self.fonts["logo"], fill="#FFFFFF", anchor="w")

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

        # Reposition Entry Widget
        entry_w = pill_w - 42
        self.canvas.create_window(pill_x + 32, pill_y + 6, window=self.search_entry, anchor="nw", width=entry_w, height=20, tags="ui_element")

        # Unit Toggle Button (°C / °F)
        gear_x = pad + bar_w - 28
        self._draw_shadow_text(gear_x, 38, "⚙", font=("Segoe UI", 16), fill="#FFFFFF", anchor="e")

        unit_x = gear_x - 45
        t_sym = "°F" if self.units.get("temp") == "fahrenheit" else "°C"
        unit_tag = "btn_unit_toggle"
        self._draw_shadow_text(unit_x, 38, f"[{t_sym}]", font=self.fonts["body_bold"], fill="#38BDF8", anchor="e", tags=("ui_element", unit_tag))

        self.canvas.tag_bind(unit_tag, "<Button-1>", lambda e: self._toggle_units())
        self.canvas.tag_bind(unit_tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind(unit_tag, "<Leave>", lambda e: self.canvas.config(cursor=""))

    def _draw_search_dropdown(self, w: int):
        """Floating autocomplete suggestions card."""
        pill_w = min(max(int(w * 0.32), 220), 340)
        pill_x = w // 2 - (pill_w // 2)
        drop_y = 58
        item_h = 36
        drop_h = len(self.search_suggestions) * item_h + 8

        drop_photo = render_frosted_glass_panel(
            bg_image=self.bg_pil_image,
            x=pill_x, y=drop_y,
            width=pill_w, height=drop_h,
            radius=16,
            blur_radius=20,
            tint_opacity=0.35,
            dark_overlay_opacity=0.60,
            border_opacity=130
        )
        self.canvas.create_image(pill_x, drop_y, image=drop_photo, anchor="nw", tags=("glass_panel", "overlay"))

        for i, s in enumerate(self.search_suggestions):
            sy = drop_y + 4 + i * item_h
            tag = f"sug_item_{i}"

            display_str = s.get("display_name") or f"{s.get('name')}, {s.get('country')}"
            truncated = truncate_text(self.fonts["small_bold"], display_str, pill_w - 24)

            self.canvas.create_text(
                pill_x + 14, sy + item_h // 2,
                text=f"📍 {truncated}",
                font=self.fonts["small_bold"],
                fill="#FFFFFF",
                anchor="w",
                tags=("ui_element", "overlay", tag)
            )

            self.canvas.tag_bind(tag, "<Button-1>", lambda e, item=s: self._select_city(item))
            self.canvas.tag_bind(tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
            self.canvas.tag_bind(tag, "<Leave>", lambda e: self.canvas.config(cursor=""))

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
        c_name = self.current_city.get("name", "London")
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
        local_time_str = datetime.datetime.now().strftime("%I:%M %p")
        if self.weather_data and "current" in self.weather_data:
            t_iso = self.weather_data["current"].get("time", "")
            if "T" in t_iso:
                try:
                    dt = datetime.datetime.fromisoformat(t_iso)
                    local_time_str = dt.strftime("%I:%M %p")
                except Exception:
                    pass

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
        cond_raw = info.get("condition", "Clear Sky")
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

        # Tabs Header: Today | Week | 16 Days
        tab_y = y + (12 if is_compact else 16)
        tab_x = x + (12 if is_compact else 18)
        tabs = [
            ("Today", 52 if is_compact else 65),
            ("Week", 48 if is_compact else 60),
            ("16 Days", 60 if is_compact else 75)
        ]

        cur_x = tab_x
        tab_gap = 6 if is_compact else 10
        for name, tw in tabs:
            is_active = (name == self.active_tab)
            t_tag = f"tab_btn_{name.replace(' ', '_')}"
            if is_active:
                tab_pill = render_frosted_glass_panel(
                    bg_image=self.bg_pil_image,
                    x=cur_x, y=tab_y,
                    width=tw, height=24 if is_compact else 28,
                    radius=12 if is_compact else 14,
                    blur_radius=10,
                    tint_opacity=0.40,
                    dark_overlay_opacity=0.30,
                    border_opacity=130
                )
                self.canvas.create_image(cur_x, tab_y, image=tab_pill, anchor="nw", tags="glass_panel")
                self._draw_shadow_text(
                    cur_x + tw // 2, tab_y + (12 if is_compact else 14),
                    name,
                    self.fonts["small_bold"],
                    fill="#FFFFFF",
                    anchor="center",
                    tags=("ui_element", t_tag)
                )
            else:
                self._draw_shadow_text(
                    cur_x + tw // 2, tab_y + (12 if is_compact else 14),
                    name,
                    self.fonts["small_bold"],
                    fill="#CBD5E1",
                    anchor="center",
                    tags=("ui_element", t_tag)
                )

            self.canvas.tag_bind(t_tag, "<Button-1>", lambda e, tname=name: self._switch_forecast_tab(tname))
            self.canvas.tag_bind(t_tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
            self.canvas.tag_bind(t_tag, "<Leave>", lambda e: self.canvas.config(cursor=""))
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
        self._draw_shadow_text(hx, hy - 10, f"High {round(temps[high_idx])}{temp_sym}", font=self.fonts["chart_label"], fill="#FBBF24", anchor="center")

        lx = cx + low_idx * step_x
        ly = cy + ch - 16 - ((temps[low_idx] - min_t) / span_t) * (ch - 24)
        self.canvas.create_oval(lx - 3, ly - 3, lx + 3, ly + 3, fill="#38BDF8", outline="#FFFFFF", width=1, tags="ui_element")
        self._draw_shadow_text(lx, ly + 10, f"Low {round(temps[low_idx])}{temp_sym}", font=self.fonts["chart_label"], fill="#38BDF8", anchor="center")

        # Time markers at bottom (00:00, 06:00, 12:00, 18:00)
        for hour_step in (0, 6, 12, 18):
            tx = cx + hour_step * step_x
            self._draw_shadow_text(tx, cy + ch - 4, f"{hour_step:02d}:00", font=self.fonts["small"], fill="#94A3B8", anchor="center")

    def _draw_week_forecast(self, x: int, y: int, w: int, h: int, is_compact: bool, days_count: int = 7):
        """Displays daily forecast cards (7 days or extended 16 days)."""
        daily = self.weather_data.get("daily", {}) if self.weather_data else {}
        d_times = daily.get("time", [])[:days_count]
        d_maxs = daily.get("temperature_2m_max", [])[:days_count]
        d_mins = daily.get("temperature_2m_min", [])[:days_count]
        d_wmos = daily.get("weather_code", [])[:days_count]
        d_rains = daily.get("precipitation_probability_max", [])[:days_count]

        # Limit displayed columns to fit comfortably
        visible_count = min(days_count, 6 if not is_compact else 5)
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
        aqi_val = aqi_data.get("european_aqi", 35) if aqi_data else 35
        sunrise_iso = daily.get("sunrise", [""])[0] if daily else ""
        sunset_iso = daily.get("sunset", [""])[0] if daily else ""
        self._draw_overview_tile_aqi(x + (tile_w + gap_x) * 2, r2_y, tile_w, tile_h, aqi_val, sunrise_iso, sunset_iso, is_compact)

    def _draw_overview_tile_humidity(self, tx, ty, tw, th, hum_val, dew_pt, is_compact):
        photo = render_frosted_glass_panel(self.bg_pil_image, tx, ty, tw, th, radius=16, blur_radius=16, tint_opacity=0.25, dark_overlay_opacity=0.35)
        self.canvas.create_image(tx, ty, image=photo, anchor="nw", tags="glass_panel")
        self._draw_shadow_text(tx + 14, ty + 15, "Humidity", self.fonts["body_bold"], fill="#FFFFFF", anchor="w")

        drop_sz = min(max(int(th * 0.44), 36), 56)
        drop_img = get_weather_icon_image("humidity", size=drop_sz)
        self._icon_refs.append(drop_img)
        self.canvas.create_image(tx + tw - 16 - drop_sz // 2, ty + th // 2, image=drop_img, tags="ui_element")

        self._draw_shadow_text(tx + 14, ty + th // 2 + 6, f"{hum_val}%", self.fonts["temp_huge"], fill="#FFFFFF", anchor="w")
        self._draw_shadow_text(tx + 14, ty + th - 13, f"Dew point: {dew_pt}°", self.fonts["small_bold"], fill="#CBD5E1", anchor="w")

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
        self._draw_shadow_text(tx + 14, ty + th // 2 + 6, f"{uv_val}", self.fonts["temp_huge"], fill="#FFFFFF", anchor="w")
        self._draw_shadow_text(tx + 14, ty + th - 13, uv_cat, self.fonts["small_bold"], fill=fill_col, anchor="w")

    def _draw_overview_tile_visibility(self, tx, ty, tw, th, vis_km, is_compact):
        photo = render_frosted_glass_panel(self.bg_pil_image, tx, ty, tw, th, radius=16, blur_radius=16, tint_opacity=0.25, dark_overlay_opacity=0.35)
        self.canvas.create_image(tx, ty, image=photo, anchor="nw", tags="glass_panel")
        self._draw_shadow_text(tx + 14, ty + 15, "Visibility", self.fonts["body_bold"], fill="#FFFFFF", anchor="w")

        vis_sz = min(max(int(th * 0.44), 36), 56)
        vis_img = get_weather_icon_image("visibility", size=vis_sz)
        self._icon_refs.append(vis_img)
        self.canvas.create_image(tx + tw - 16 - vis_sz // 2, ty + th // 2, image=vis_img, tags="ui_element")

        self._draw_shadow_text(tx + 14, ty + th // 2 + 6, f"{vis_km} km", self.fonts["h2"], fill="#FFFFFF", anchor="w")
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

        self._draw_shadow_text(tx + 14, ty + th // 2 + 6, f"{wind_spd} {wind_unit}", self.fonts["h2"], fill="#FFFFFF", anchor="w")
        self._draw_shadow_text(tx + 14, ty + th - 13, f"Blowing from {cardinal}", self.fonts["small_bold"], fill="#CBD5E1", anchor="w")

    def _draw_overview_tile_pressure(self, tx, ty, tw, th, press_val, clouds, is_compact):
        photo = render_frosted_glass_panel(self.bg_pil_image, tx, ty, tw, th, radius=16, blur_radius=16, tint_opacity=0.25, dark_overlay_opacity=0.35)
        self.canvas.create_image(tx, ty, image=photo, anchor="nw", tags="glass_panel")
        self._draw_shadow_text(tx + 14, ty + 15, "Pressure", self.fonts["body_bold"], fill="#FFFFFF", anchor="w")

        baro_sz = min(max(int(th * 0.44), 36), 56)
        baro_img = get_weather_icon_image("barometer", size=baro_sz)
        self._icon_refs.append(baro_img)
        self.canvas.create_image(tx + tw - 16 - baro_sz // 2, ty + th // 2, image=baro_img, tags="ui_element")

        self._draw_shadow_text(tx + 14, ty + th // 2 + 6, f"{press_val} hPa", self.fonts["h2"], fill="#FFFFFF", anchor="w")
        self._draw_shadow_text(tx + 14, ty + th - 13, f"Cloud cover: {clouds}%", self.fonts["small_bold"], fill="#CBD5E1", anchor="w")

    def _draw_overview_tile_aqi(self, tx, ty, tw, th, aqi_val, sunrise_iso, sunset_iso, is_compact):
        photo = render_frosted_glass_panel(self.bg_pil_image, tx, ty, tw, th, radius=16, blur_radius=16, tint_opacity=0.25, dark_overlay_opacity=0.35)
        self.canvas.create_image(tx, ty, image=photo, anchor="nw", tags="glass_panel")
        self._draw_shadow_text(tx + 14, ty + 15, "Air Quality", self.fonts["body_bold"], fill="#FFFFFF", anchor="w")

        aqi_sz = min(max(int(th * 0.44), 36), 56)
        aqi_img = get_weather_icon_image("aqi", size=aqi_sz)
        self._icon_refs.append(aqi_img)
        self.canvas.create_image(tx + tw - 16 - aqi_sz // 2, ty + th // 2, image=aqi_img, tags="ui_element")

        aqi_level = get_aqi_level(aqi_val)
        cat_name = aqi_level.get("category", "Good")
        col = aqi_level.get("color", "#10B981")

        self._draw_shadow_text(tx + 14, ty + th // 2 + 6, f"{aqi_val} AQI", self.fonts["h2"], fill="#FFFFFF", anchor="w")

        # Sunrise / sunset formatting
        sun_str = ""
        if "T" in sunrise_iso and "T" in sunset_iso:
            try:
                sr = sunrise_iso.split("T")[1][:5]
                ss = sunset_iso.split("T")[1][:5]
                sun_str = f"☀️ {sr} • 🌙 {ss}"
            except Exception:
                pass

        caption = sun_str if sun_str and tw > 210 else f"Quality: {cat_name}"
        self._draw_shadow_text(tx + 14, ty + th - 13, caption, self.fonts["small_bold"], fill=col if "Quality" in caption else "#CBD5E1", anchor="w")

    # ========================================================================
    # Loading Spinner Overlay & Error Notification Banner
    # ========================================================================
    def _draw_loading_overlay(self, w: int, h: int):
        card_w = 260
        card_h = 75
        cx = w // 2 - card_w // 2
        cy = h // 2 - card_h // 2

        photo = render_frosted_glass_panel(self.bg_pil_image, cx, cy, card_w, card_h, radius=18, blur_radius=22, tint_opacity=0.35, dark_overlay_opacity=0.55)
        self.canvas.create_image(cx, cy, image=photo, anchor="nw", tags=("glass_panel", "overlay"))

        self._draw_shadow_text(
            cx + card_w // 2, cy + 26,
            "⚡ Updating SkyCast...",
            self.fonts["body_bold"],
            fill="#FFFFFF",
            anchor="center",
            tags="overlay"
        )
        self._draw_shadow_text(
            cx + card_w // 2, cy + 50,
            "Fetching live Open-Meteo metrics",
            self.fonts["small"],
            fill="#38BDF8",
            anchor="center",
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
        self.canvas.create_image(bx, by, image=banner_photo, anchor="nw", tags=("glass_panel", "overlay"))

        self._draw_shadow_text(
            bx + banner_w // 2, by + bh // 2,
            f"⚠️  {self.error_banner_text}",
            self.fonts["small_bold"],
            fill="#FBBF24",
            anchor="center",
            tags="overlay"
        )
        self.canvas.tag_bind("overlay", "<Button-1>", lambda e: self._clear_error_banner())

    def _toggle_preview_mode(self):
        """Hidden preview mode (F2) to cycle through weather x time phases."""
        themes_cycle = [
            ("clear", "day"), ("clear", "evening"), ("clear", "night"),
            ("rain", "day"), ("thunderstorm", "night"), ("snow", "day"), ("fog", "dawn")
        ]
        curr_idx = getattr(self, "_preview_idx", 0)
        w_type, phase = themes_cycle[curr_idx % len(themes_cycle)]
        self._preview_idx = curr_idx + 1

        self.current_theme = resolve_theme(0, forced_theme=f"{w_type}-{phase}")
        clear_panel_cache()
        self._render_all_panels()

def main():
    try:
        app = SkyCastMainWindow()
        app.mainloop()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
