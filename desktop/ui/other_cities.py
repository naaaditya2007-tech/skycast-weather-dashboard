"""
SkyCast Desktop UI — Other Cities Component (Right Column)
----------------------------------------------------------
Displays saved favorite cities matching the design reference screenshot:
- Header: 'Other Cities' on left, 'See all' on right
- Stacked frosted glass cards showing Country, City, Condition text, and Icon
- Smooth hover and click selection
"""

import tkinter as tk
from typing import Dict, Any, List, Callable, Optional
from desktop.ui.panels import render_frosted_glass_panel
from desktop.ui.icons import get_weather_icon_image

def truncate_text(font: tk.font.Font, text: str, max_w: int) -> str:
    """Safely truncate text with an ellipsis if it exceeds max_w in pixels."""
    if font.measure(text) <= max_w:
        return text
    ell = "..."
    ell_w = font.measure(ell)
    avail = max_w - ell_w
    if avail <= 0:
        return ell
    trimmed = text
    while trimmed and font.measure(trimmed) > avail:
        trimmed = trimmed[:-1]
    return trimmed + ell

# Placeholder initial cities from design reference
PLACEHOLDER_OTHER_CITIES = [
    {"country": "China", "city": "Beijing", "condition": "Cloudy", "icon": "cloud", "temp": "12°C"},
    {"country": "Japan", "city": "Tokyo", "condition": "Sunny", "icon": "sun", "temp": "18°C"},
    {"country": "Brazil", "city": "Brasília", "condition": "Rainy", "icon": "rain", "temp": "24°C"},
    {"country": "Germany", "city": "Berlin", "condition": "Snowy", "icon": "snow", "temp": "3°C"},
    {"country": "Australia", "city": "Canberra", "condition": "Windy", "icon": "wind", "temp": "19°C"}
]

class OtherCitiesPanel:
    def __init__(self, canvas: tk.Canvas,
                 on_select_city: Optional[Callable[[Dict[str, Any]], None]] = None,
                 on_remove_city: Optional[Callable[[str], None]] = None,
                 on_add_current_city: Optional[Callable[[], None]] = None):
        self.canvas = canvas
        self.on_select_city = on_select_city
        self.on_remove_city = on_remove_city
        self.on_add_current_city = on_add_current_city
        self._icon_refs: List[Any] = []

        btn_style = {
            "bd": 0,
            "relief": "flat",
            "highlightthickness": 0,
            "bg": "#3b4d66",
            "fg": "#38BDF8",
            "activebackground": "#526b8a",
            "activeforeground": "#ffffff",
            "cursor": "hand2"
        }
        self.lbl_header = tk.Label(
            self.canvas,
            text="Other Cities",
            font=("Segoe UI", 13, "bold"),
            bg="#1e293b",
            fg="#FFFFFF",
            bd=0,
            relief="flat",
            highlightthickness=0
        )
        self.btn_fav = tk.Button(
            self.canvas,
            text="+ Add Fav",
            font=("Segoe UI", 9, "bold"),
            command=self._on_fav_click,
            **btn_style
        )

    def _on_fav_click(self):
        if self.on_add_current_city:
            self.on_add_current_city()

    def draw(self, bg_image, x: int, y: int, width: int, height: int,
             cities_data: List[Dict[str, Any]],
             theme: Dict[str, Any],
             fonts: Dict[str, Any],
             is_current_favorite: bool = False):
        """Render the 'Other Cities' right-column stacked cards with live data."""
        self._icon_refs.clear()

        # Section Header (tk.Label)
        self.canvas.create_window(
            x + 5, y + 14,
            window=self.lbl_header,
            anchor="w",
            tags="ui_element"
        )

        # Header Action Button: Add/Favorite Toggle (tk.Button)
        btn_text = "★ Saved" if is_current_favorite else "+ Add Fav"
        self.btn_fav.config(
            text=btn_text,
            fg="#FBBF24" if is_current_favorite else "#38BDF8",
            bg="#2a374a" if is_current_favorite else "#3b4d66"
        )
        self.canvas.create_window(
            x + width - 6, y + 14,
            window=self.btn_fav,
            anchor="e",
            height=26,
            tags="ui_element"
        )

        # Empty State
        if not cities_data:
            empty_h = 160
            glass_photo = render_frosted_glass_panel(
                bg_image=bg_image,
                x=x, y=y + 40,
                width=width, height=empty_h,
                radius=18,
                blur_radius=18,
                tint_opacity=0.25,
                dark_overlay_opacity=0.35,
                border_opacity=110
            )
            self.canvas.create_image(x, y + 40, image=glass_photo, anchor="nw", tags="glass_panel")

            star_img = get_weather_icon_image("star", size=36)
            self._icon_refs.append(star_img)
            self.canvas.create_image(x + width // 2, y + 78, image=star_img, tags="ui_element")

            self.canvas.create_text(
                x + width // 2, y + 118,
                text="No Saved Cities",
                font=fonts["body_bold"],
                fill="#FFFFFF",
                anchor="center",
                tags="ui_element"
            )
            self.canvas.create_text(
                x + width // 2, y + 142,
                text="Click '+ Add Fav' to pin\nfavorite cities here.",
                font=fonts["small"],
                fill="#CBD5E1",
                anchor="center",
                justify="center",
                tags="ui_element"
            )
            return

        cards = cities_data[:5]
        card_count = len(cards)
        top_offset = y + 36
        available_h = height - 42
        gap = 8
        card_h = max((available_h - gap * (card_count - 1)) // card_count, 54)

        for i, c in enumerate(cards):
            cy = top_offset + i * (card_h + gap)

            # Frosted Glass Card
            glass_photo = render_frosted_glass_panel(
                bg_image=bg_image,
                x=x, y=cy,
                width=width, height=card_h,
                radius=16,
                blur_radius=18,
                tint_opacity=0.25,
                dark_overlay_opacity=0.35,
                border_opacity=110
            )
            card_tag = f"other_city_card_{i}"
            self.canvas.create_image(x, cy, image=glass_photo, anchor="nw", tags=("glass_panel", card_tag))

            max_text_w = max(width - 76, 80)
            pad_top = max((card_h - 42) // 2, 8)

            # Country label (Line 1)
            country_raw = c.get("country", "")
            country_text = truncate_text(fonts["small_bold"], country_raw, max_text_w)
            self.canvas.create_text(x + 17, cy + pad_top + 1, text=country_text, font=fonts["small_bold"], fill="#090D16", anchor="w", tags=("ui_element", card_tag))
            self.canvas.create_text(x + 16, cy + pad_top, text=country_text, font=fonts["small_bold"], fill="#CBD5E1", anchor="w", tags=("ui_element", card_tag))

            # City name + Temp (Line 2)
            city_name = c.get("name") or c.get("city", "")
            temp_str = c.get("temp", "")
            display_title = f"{city_name}  {temp_str}".strip() if temp_str else city_name
            city_text = truncate_text(fonts["body_bold"], display_title, max_text_w)
            self.canvas.create_text(x + 17, cy + pad_top + 18, text=city_text, font=fonts["body_bold"], fill="#090D16", anchor="w", tags=("ui_element", card_tag))
            self.canvas.create_text(x + 16, cy + pad_top + 17, text=city_text, font=fonts["body_bold"], fill="#FFFFFF", anchor="w", tags=("ui_element", card_tag))

            # Condition text (Line 3)
            cond_raw = c.get("condition", "Clear")
            cond_text = truncate_text(fonts["small_bold"], cond_raw, max_text_w)
            self.canvas.create_text(x + 17, cy + pad_top + 35, text=cond_text, font=fonts["small_bold"], fill="#090D16", anchor="w", tags=("ui_element", card_tag))
            self.canvas.create_text(x + 16, cy + pad_top + 34, text=cond_text, font=fonts["small_bold"], fill="#38BDF8", anchor="w", tags=("ui_element", card_tag))

            # Weather Icon on right
            icon_kind = c.get("icon") or cond_raw
            icon_size = min(max(card_h - 18, 28), 36)
            icon_img = get_weather_icon_image(str(icon_kind), size=icon_size)
            self._icon_refs.append(icon_img)

            self.canvas.create_image(
                x + width - 24 - icon_size // 2, cy + card_h // 2,
                image=icon_img,
                tags=("ui_element", card_tag)
            )

            # High-contrast Remove '✕' button on top-right of card with drop shadow
            remove_tag = f"remove_fav_{i}"
            self.canvas.create_text(
                x + width - 13, cy + 13,
                text="✕",
                font=("Segoe UI", 10, "bold"),
                fill="#090D16",
                anchor="center",
                tags=("ui_element", remove_tag)
            )
            self.canvas.create_text(
                x + width - 14, cy + 12,
                text="✕",
                font=("Segoe UI", 10, "bold"),
                fill="#CBD5E1",
                anchor="center",
                tags=("ui_element", remove_tag)
            )

            # Bindings: Click card to load weather; Click ✕ to remove
            if self.on_select_city:
                self.canvas.tag_bind(card_tag, "<Button-1>", lambda e, city_dict=c: self.on_select_city(city_dict))
                self.canvas.tag_bind(card_tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
                self.canvas.tag_bind(card_tag, "<Leave>", lambda e: self.canvas.config(cursor=""))

            if self.on_remove_city:
                self.canvas.tag_bind(remove_tag, "<Button-1>", lambda e, name=city_name: self.on_remove_city(name))
                self.canvas.tag_bind(remove_tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
                self.canvas.tag_bind(remove_tag, "<Leave>", lambda e: self.canvas.config(cursor=""))
                self.canvas.tag_bind(card_tag, "<Leave>", lambda e: self.canvas.config(cursor=""))
