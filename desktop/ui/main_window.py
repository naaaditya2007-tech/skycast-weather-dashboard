"""
SkyCast Desktop UI — Main Application Window (Stage 3)
------------------------------------------------------
Faithfully replicates the reference design layout and frosted-glass aesthetic:
- 3-Column Desktop Layout:
  1. Top: Full-width rounded glass navigation bar (Hamburger, SkyCast, Pill Search, °C/°F, Settings Gear).
  2. Left Column: Large Hero Weather Card (City, local time, large temp, condition, feels like, summary).
  3. Middle Column: Forecast Card with Today / Week / 16 Days tabs above horizontal mini-cards.
  4. Lower Span: 'Overview' grid of frosted tiles (Humidity, UV Index with gradient bar, Visibility, Wind, Pressure, AQI, etc.).
  5. Right Column: 'Other Cities' vertical stacked cards with country, city, condition, and weather icon.
- True Optical Frosted Glass:
  Uses Pillow to crop background, apply Gaussian blur, composite translucent white tint (15-20%),
  and mask with anti-aliased rounded rectangle. Panels render once and re-render ONLY on resize/theme changes.
- Windows DPI-Awareness:
  Enforces crisp rendering on high-DPI displays.
- Window geometry: 1100x750 default, minsize 800x600.
"""

import sys
import os
import time
import queue
import tkinter as tk
from tkinter import font as tkfont
from typing import Dict, Any, List, Optional
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

from shared.weather_codes import resolve_theme, get_aqi_level, get_uv_level
from desktop.storage import StorageManager
from desktop.api_client import WeatherApiClient
from desktop.ui.panels import (
    generate_procedural_background,
    render_frosted_glass_panel,
    clear_panel_cache
)
from desktop.ui.animations import WeatherAnimator
from desktop.ui.icons import get_weather_icon_image
from desktop.ui.other_cities import OtherCitiesPanel, PLACEHOLDER_OTHER_CITIES, truncate_text

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
        self.last_city = self.storage.get_last_city()
        self.current_theme = resolve_theme(2, is_day=1, temp_c=26.0) # Partly cloudy daytime theme default
        self.bg_pil_image: Optional[Image.Image] = None
        self.bg_photo: Optional[ImageTk.PhotoImage] = None
        self.forced_wallpaper: Optional[str] = None
        self._icon_refs: List[Any] = []
        self.resize_debounce_id: Optional[str] = None

        # Build Full Canvas
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.canvas.pack(fill="both", expand=True)

        # Initialize Fonts
        self._init_fonts()

        # Components
        self.animator = WeatherAnimator(self.canvas)
        self.other_cities_panel = OtherCitiesPanel(self.canvas, on_select_city=self._on_select_other_city)

        # Window Resize Binding
        self.bind("<Configure>", self._on_resize)
        self.bind("<F2>", lambda e: self._toggle_preview_mode())

        # Render initial layout
        self.after(50, self._render_all_panels)

    def _init_fonts(self):
        """Configure crisp typography for high-DPI monitors."""
        self.fonts = {
            "logo": tkfont.Font(family="Segoe UI", size=15, weight="bold"),
            "city_title": tkfont.Font(family="Segoe UI", size=20, weight="bold"),
            "temp_huge": tkfont.Font(family="Segoe UI", size=52, weight="bold"),
            "h2": tkfont.Font(family="Segoe UI", size=13, weight="bold"),
            "h3": tkfont.Font(family="Segoe UI", size=11, weight="bold"),
            "body": tkfont.Font(family="Segoe UI", size=10),
            "body_bold": tkfont.Font(family="Segoe UI", size=10, weight="bold"),
            "small": tkfont.Font(family="Segoe UI", size=8),
            "small_bold": tkfont.Font(family="Segoe UI", size=8, weight="bold"),
            "icon_large": tkfont.Font(family="Segoe UI Emoji", size=32),
            "icon_huge": tkfont.Font(family="Segoe UI Emoji", size=48),
            "icon_mid": tkfont.Font(family="Segoe UI Emoji", size=20)
        }

    def _poll_queue(self):
        """Safely execute any tasks dispatched from background threads."""
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
                self.after(50, self._poll_queue)
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

    def _render_all_panels(self):
        """
        Main Frosted Glass Rendering Pipeline:
        1. Generates full-window background (procedural gradient or wallpaper).
        2. Crops, blurs, and tints each panel using Pillow (frosted glass effect).
        3. Places all glass panels once on the Canvas.
        4. Overlays text, icons, tabs, and overview tiles.
        """
        w = max(self.canvas.winfo_width(), 800)
        h = max(self.canvas.winfo_height(), 600)

        # Clear existing elements
        self.canvas.delete("glass_panel")
        self.canvas.delete("ui_element")
        self.canvas.delete("bg_image")
        self._icon_refs.clear()

        # 1. Update font sizes adaptively based on window width
        is_compact = (w < 950)
        self.fonts["city_title"].config(size=16 if is_compact else 20)
        self.fonts["temp_huge"].config(size=40 if is_compact else 52)
        self.fonts["icon_huge"].config(size=36 if is_compact else 48)
        self.fonts["h2"].config(size=12 if is_compact else 13)
        self.fonts["body"].config(size=9 if is_compact else 10)
        self.fonts["body_bold"].config(size=9 if is_compact else 10)
        self.fonts["small"].config(size=8 if is_compact else 9)
        self.fonts["small_bold"].config(size=8 if is_compact else 9)

        # 1. Load background wallpaper photo if present in assets/backgrounds, else fallback to gradient
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        bg_dir = os.path.join(root_dir, "desktop", "assets", "backgrounds")
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
                    
                    # Add dark readability overlay (15% dark tint) for crystal clear contrast
                    dark_full = Image.new("RGBA", (w, h), (15, 23, 42, int(255 * 0.15)))
                    loaded_bg = Image.alpha_composite(cropped.convert("RGBA"), dark_full).convert("RGB")
                    break
                except Exception as ex:
                    print(f"[SkyCast] Could not load background photo {cand}: {ex}")

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

        # 2. Draw Top Navigation Glass Bar
        self._draw_top_bar(w)

        # 3. Calculate 3-Column Coordinates
        pad = 16 if is_compact else 20
        gap = 10 if is_compact else 14
        top_y = 74 if is_compact else 78
        avail_h = h - top_y - pad

        # Column widths matching reference screenshot (Left ~37%, Middle ~38%, Right ~25%)
        avail_w = w - (pad * 2) - (gap * 2)
        col1_w = int(avail_w * 0.37)
        col2_w = int(avail_w * 0.38)
        col3_w = avail_w - col1_w - col2_w

        col1_x = pad
        col2_x = col1_x + col1_w + gap
        col3_x = col2_x + col2_w + gap

        # Row 1 Height (Hero & Forecast tabs)
        row1_h = int(avail_h * 0.45)
        row2_y = top_y + row1_h + gap
        row2_h = avail_h - row1_h - gap

        # 4. Draw Left Column Hero Weather Card
        self._draw_hero_card(col1_x, top_y, col1_w, row1_h, is_compact)

        # 5. Draw Middle Column Forecast Mini-Cards
        self._draw_forecast_card(col2_x, top_y, col2_w, row1_h, is_compact)

        # 6. Draw Lower Span: Overview Grid
        overview_w = col1_w + gap + col2_w
        self._draw_overview_grid(col1_x, row2_y, overview_w, row2_h, is_compact)

        # 7. Draw Right Column: Other Cities Stacked Cards
        self.other_cities_panel.draw(
            bg_image=self.bg_pil_image,
            x=col3_x, y=top_y,
            width=col3_w, height=avail_h,
            cities_data=PLACEHOLDER_OTHER_CITIES,
            theme=self.current_theme,
            fonts=self.fonts
        )

        # Ensure correct layer stacking:
        # Background (bottom) -> Particles -> Glass Panels -> UI Text / Controls (top)
        self.canvas.tag_lower("bg_image")
        self.canvas.tag_raise("glass_panel", "bg_image")
        self.canvas.tag_raise("ui_element", "glass_panel")

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
    # Top Navigation Glass Bar
    # ========================================================================
    def _draw_top_bar(self, w: int):
        pad = 20
        bar_h = 48
        bar_w = w - (pad * 2)

        # Frosted glass background
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

        # Left: Hamburger menu icon + App Name
        self._draw_shadow_text(pad + 20, 38, "☰", font=("Segoe UI", 14), fill="#FFFFFF", anchor="w")
        self._draw_shadow_text(pad + 48, 38, "SkyCast", font=self.fonts["logo"], fill="#FFFFFF", anchor="w")

        # Center: Pill Search Field
        pill_w = min(max(int(w * 0.28), 200), 320)
        pill_x = w // 2 - (pill_w // 2)
        pill_h = 32
        pill_y = 22

        # Draw Search Pill outline & glass
        pill_glass = render_frosted_glass_panel(
            bg_image=self.bg_pil_image,
            x=pill_x, y=pill_y,
            width=pill_w, height=pill_h,
            radius=16,
            blur_radius=14,
            tint_opacity=0.28,
            dark_overlay_opacity=0.40,
            border_opacity=110
        )
        self.canvas.create_image(pill_x, pill_y, image=pill_glass, anchor="nw", tags="glass_panel")
        self._draw_shadow_text(pill_x + 14, pill_y + pill_h // 2, "🔍  Search City...", font=self.fonts["body_bold"], fill="#F1F5F9", anchor="w")

        # Right: Unit Toggle (°C/°F) and Settings Gear (⚙)
        gear_x = pad + bar_w - 30
        self._draw_shadow_text(gear_x, 38, "⚙", font=("Segoe UI", 16), fill="#FFFFFF", anchor="e")

        unit_x = gear_x - 45
        t_sym = "°F" if self.units.get("temp") == "fahrenheit" else "°C"
        self._draw_shadow_text(unit_x, 38, f"[{t_sym}]", font=self.fonts["body_bold"], fill="#FFFFFF", anchor="e")

    # ========================================================================
    # Left Column: Hero Current Weather Card
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

        # Scale temperature font proportionally to card width so it never overflows
        temp_font_size = max(min(int(w * 0.115), 48), 28)
        self.fonts["temp_huge"].config(size=temp_font_size)

        # 1. Location Pin Inline + City Name (Ellipsis truncation if long)
        city_name = "Lagos, Nigeria"
        full_city = f"📍 {city_name}"
        avail_title_w = avail_card_w - 6
        display_city = truncate_text(self.fonts["city_title"], full_city, avail_title_w)

        self._draw_shadow_text(
            x + pad_x, y + (22 if is_compact else 26),
            display_city,
            self.fonts["city_title"],
            fill="#FFFFFF",
            anchor="w"
        )

        # 2. Local Time on its own line below with clear spacing (30-32px separation)
        self._draw_shadow_text(
            x + pad_x, y + (52 if is_compact else 58),
            "8:15 AM",
            self.fonts["body_bold"],
            fill="#E2E8F0",
            anchor="w"
        )

        # 3. Big Temperature & Condition with measured real gap
        temp_sym = "°F" if self.units.get("temp") == "fahrenheit" else "°C"
        temp_str = f"26{temp_sym}"
        temp_y = y + (98 if is_compact else 114)
        self._draw_shadow_text(
            x + pad_x, temp_y,
            temp_str,
            self.fonts["temp_huge"],
            fill="#FFFFFF",
            anchor="w"
        )

        # Measure real temperature width to place condition cleanly without overlap
        temp_w = self.fonts["temp_huge"].measure(temp_str)
        cond_x = x + pad_x + temp_w + 14

        avail_cond_w = max(w - (cond_x - x) - pad_x, 60)
        cond_text = truncate_text(self.fonts["h2"], "Partly Sunny", avail_cond_w)
        feels_like_text = truncate_text(self.fonts["body_bold"], f"Feels like 28{temp_sym}", avail_cond_w)

        # White condition text, light grey feels like text with shadow
        self._draw_shadow_text(
            cond_x, temp_y - 12,
            cond_text,
            self.fonts["h2"],
            fill="#FFFFFF",
            anchor="w"
        )
        self._draw_shadow_text(
            cond_x, temp_y + 12,
            feels_like_text,
            self.fonts["body_bold"],
            fill="#E2E8F0",
            anchor="w"
        )

        # 4. Summary Sentence directly under temperature block (no dead space, word-wrapped)
        summary_y = temp_y + (30 if is_compact else 36)
        summary_text = (
            "Light winds and a warm morning. Slight chance of rain in the evening. "
            "Humidity remains high with clear skies expected into Tuesday."
        )
        avail_summary_w = avail_card_w - 6
        self._draw_shadow_text(
            x + pad_x, summary_y,
            summary_text,
            font=self.fonts["body"],
            fill="#F8FAFC",
            anchor="nw",
            width=avail_summary_w
        )

    # ========================================================================
    # Middle Column: Forecast Tabs & Horizontal Mini-Cards (5-6 cards)
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
                    anchor="center"
                )
            else:
                self._draw_shadow_text(
                    cur_x + tw // 2, tab_y + (12 if is_compact else 14),
                    name,
                    self.fonts["small_bold"],
                    fill="#CBD5E1",
                    anchor="center"
                )
            cur_x += tw + tab_gap

        # Show 5-6 cards per row with balanced vertical distribution
        card_count = 5 if is_compact else 6
        mini_top = y + (46 if is_compact else 54)
        mini_h = h - (56 if is_compact else 66)

        pad_m = 10 if is_compact else 14
        gap_m = 6 if is_compact else 8
        card_w = (w - (pad_m * 2) - (gap_m * (card_count - 1))) // card_count

        sample_hours = [
            {"time": "9:00", "icon": "sun", "temp": "26°C", "rain": "0%"},
            {"time": "10:00", "icon": "partly", "temp": "27°C", "rain": "5%"},
            {"time": "11:00", "icon": "rain", "temp": "28°C", "rain": "25%"},
            {"time": "12:00", "icon": "rain", "temp": "29°C", "rain": "60%"},
            {"time": "13:00", "icon": "thunder", "temp": "28°C", "rain": "80%"},
            {"time": "14:00", "icon": "cloud", "temp": "27°C", "rain": "20%"}
        ][:card_count]

        for i, h_item in enumerate(sample_hours):
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

            # 1. Time (top)
            self._draw_shadow_text(
                mx + card_w // 2, mini_top + (14 if is_compact else 18),
                h_item["time"],
                self.fonts["small_bold"],
                fill="#FFFFFF",
                anchor="center"
            )

            # 2. Soft Colored Vector Icon (upper middle)
            icon_sz = min(max(card_w - 14, 22), 32 if is_compact else 36)
            icon_img = get_weather_icon_image(h_item["icon"], size=icon_sz)
            self._icon_refs.append(icon_img)
            self.canvas.create_image(
                mx + card_w // 2, mini_top + int(mini_h * 0.42),
                image=icon_img,
                tags="ui_element"
            )

            # 3. Rain probability badge (lower middle)
            self._draw_shadow_text(
                mx + card_w // 2, mini_top + int(mini_h * 0.68),
                h_item["rain"],
                self.fonts["small_bold"],
                fill="#38BDF8",
                anchor="center"
            )

            # 4. Temperature (bottom)
            self._draw_shadow_text(
                mx + card_w // 2, mini_top + mini_h - (14 if is_compact else 18),
                h_item["temp"],
                self.fonts["body_bold"],
                fill="#FFFFFF",
                anchor="center"
            )

    # ========================================================================
    # Lower Span: Overview Grid
    # ========================================================================
    def _draw_overview_grid(self, x: int, y: int, w: int, h: int, is_compact: bool = False):
        # Header: 'Overview'
        self._draw_shadow_text(
            x + 5, y + 8,
            "Overview",
            self.fonts["h2"],
            fill="#FFFFFF",
            anchor="w"
        )

        grid_y = y + (26 if is_compact else 30)
        grid_h = h - (26 if is_compact else 30)

        # 3 Primary Tiles (Humidity, UV Index, Visibility)
        cols = 3
        gap = 8 if is_compact else 12
        tile_w = (w - gap * (cols - 1)) // cols

        # Tile 1: Humidity
        t1_x = x
        t1_photo = render_frosted_glass_panel(
            self.bg_pil_image, t1_x, grid_y, tile_w, grid_h,
            radius=16, blur_radius=18, tint_opacity=0.25, dark_overlay_opacity=0.35, border_opacity=110
        )
        self.canvas.create_image(t1_x, grid_y, image=t1_photo, anchor="nw", tags="glass_panel")

        self._draw_shadow_text(t1_x + 14, grid_y + 16, "Humidity", self.fonts["body_bold"], fill="#FFFFFF", anchor="w")
        
        # Soft colored droplet
        drop_sz = min(max(int(grid_h * 0.40), 38), 64)
        drop_img = get_weather_icon_image("humidity", size=drop_sz)
        self._icon_refs.append(drop_img)
        self.canvas.create_image(t1_x + tile_w // 2, grid_y + grid_h // 2 - 4, image=drop_img, tags="ui_element")

        self._draw_shadow_text(t1_x + 14, grid_y + grid_h - 15, "67%", self.fonts["h2"], fill="#FFFFFF", anchor="w")
        if tile_w >= 165:
            self._draw_shadow_text(t1_x + tile_w - 12, grid_y + grid_h - 15, "Moisture in air", self.fonts["small_bold"], fill="#E2E8F0", anchor="e")

        # Tile 2: UV Index
        t2_x = t1_x + tile_w + gap
        t2_photo = render_frosted_glass_panel(
            self.bg_pil_image, t2_x, grid_y, tile_w, grid_h,
            radius=16, blur_radius=18, tint_opacity=0.25, dark_overlay_opacity=0.35, border_opacity=110
        )
        self.canvas.create_image(t2_x, grid_y, image=t2_photo, anchor="nw", tags="glass_panel")

        self._draw_shadow_text(t2_x + 14, grid_y + 16, "UV Index", self.fonts["body_bold"], fill="#FFFFFF", anchor="w")

        # Vertical multi-color gradient thermometer bar
        bar_x = t2_x + tile_w // 2 - 6
        bar_y1 = grid_y + (30 if is_compact else 38)
        bar_y2 = grid_y + grid_h - (34 if is_compact else 42)
        bar_w = 12
        # Dark shadow backing bar
        self.canvas.create_rectangle(bar_x + 1, bar_y1 + 1, bar_x + bar_w + 1, bar_y2 + 1, fill="#090D16", outline="", tags="ui_element")
        self.canvas.create_rectangle(bar_x, bar_y1, bar_x + bar_w, bar_y2, fill="#1E293B", outline="#475569", tags="ui_element")
        # Gradient active indicator
        fill_y = bar_y1 + int((bar_y2 - bar_y1) * 0.45)
        self.canvas.create_rectangle(bar_x + 1, fill_y, bar_x + bar_w - 1, bar_y2 - 1, fill="#F59E0B", outline="", tags="ui_element")

        self._draw_shadow_text(t2_x + tile_w // 2, grid_y + grid_h - 15, "4 (Moderate)", self.fonts["h2"], fill="#FFFFFF", anchor="center")

        # Tile 3: Visibility
        t3_x = t2_x + tile_w + gap
        t3_photo = render_frosted_glass_panel(
            self.bg_pil_image, t3_x, grid_y, tile_w, grid_h,
            radius=16, blur_radius=18, tint_opacity=0.25, dark_overlay_opacity=0.35, border_opacity=110
        )
        self.canvas.create_image(t3_x, grid_y, image=t3_photo, anchor="nw", tags="glass_panel")

        self._draw_shadow_text(t3_x + 14, grid_y + 16, "Visibility", self.fonts["body_bold"], fill="#FFFFFF", anchor="w")

        # Soft colored mist/haze icon
        vis_sz = min(max(int(grid_h * 0.40), 38), 64)
        vis_img = get_weather_icon_image("visibility", size=vis_sz)
        self._icon_refs.append(vis_img)
        self.canvas.create_image(t3_x + tile_w // 2, grid_y + grid_h // 2 - 4, image=vis_img, tags="ui_element")

        self._draw_shadow_text(t3_x + 14, grid_y + grid_h - 15, "10 km", self.fonts["h2"], fill="#FFFFFF", anchor="w")
        if tile_w >= 165:
            self._draw_shadow_text(t3_x + tile_w - 12, grid_y + grid_h - 15, "Haze present", self.fonts["small_bold"], fill="#E2E8F0", anchor="e")

    # ========================================================================
    # Handlers & Preview Mode
    # ========================================================================
    def _on_select_other_city(self, city_name: str):
        print(f"[SkyCast] Selected city from right column: {city_name}")

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
        print(f"[SkyCast Preview] Switched to forced theme: {w_type} x {phase}")

def main():
    try:
        app = SkyCastMainWindow()
        app.mainloop()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error launching Stage 3: {e}")

if __name__ == "__main__":
    main()
