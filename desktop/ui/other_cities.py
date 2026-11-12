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
    def __init__(self, canvas: tk.Canvas, on_select_city: Optional[Callable[[str], None]] = None):
        self.canvas = canvas
        self.on_select_city = on_select_city
        self._icon_refs: List[Any] = []

    def draw(self, bg_image, x: int, y: int, width: int, height: int,
             cities_data: List[Dict[str, Any]],
             theme: Dict[str, Any],
             fonts: Dict[str, Any]):
        """Render the 'Other Cities' right-column stacked cards."""
        self._icon_refs.clear()

        # Section Header
        self.canvas.create_text(
            x + 5, y + 14,
            text="Other Cities",
            font=fonts["h2"],
            fill=theme["text_primary"],
            anchor="w",
            tags="ui_element"
        )

        see_all_tag = "btn_see_all"
        self.canvas.create_text(
            x + width - 5, y + 14,
            text="See all",
            font=fonts["body_bold"],
            fill=theme.get("accent", "#38BDF8"),
            anchor="e",
            tags=("ui_element", see_all_tag)
        )

        cards = cities_data if cities_data else PLACEHOLDER_OTHER_CITIES
        card_count = min(len(cards), 5)
        top_offset = y + 36
        available_h = height - 42
        gap = 8
        card_h = max((available_h - gap * (card_count - 1)) // card_count, 54)

        for i in range(card_count):
            c = cards[i]
            cy = top_offset + i * (card_h + gap)

            # Frosted Glass Card
            glass_photo = render_frosted_glass_panel(
                bg_image=bg_image,
                x=x, y=cy,
                width=width, height=card_h,
                radius=16,
                blur_radius=14,
                tint_opacity=theme.get("glass_tint_opacity", 0.18),
                border_opacity=75
            )
            card_tag = f"other_city_card_{i}"
            self.canvas.create_image(x, cy, image=glass_photo, anchor="nw", tags=("glass_panel", card_tag))

            max_text_w = max(width - 65, 80)

            # Country label (high contrast, crisp light silver with subtle shadow)
            country_raw = c.get("country", "")
            country_text = truncate_text(fonts["small_bold"], country_raw, max_text_w)
            self.canvas.create_text(x + 17, cy + 16, text=country_text, font=fonts["small_bold"], fill="#090D16", anchor="w", tags=("ui_element", card_tag))
            self.canvas.create_text(x + 16, cy + 15, text=country_text, font=fonts["small_bold"], fill="#F1F5F9", anchor="w", tags=("ui_element", card_tag))

            # City name (bold, bright white with subtle shadow)
            city_raw = c.get("city") or c.get("name", "")
            city_text = truncate_text(fonts["body_bold"], city_raw, max_text_w)
            self.canvas.create_text(x + 17, cy + 33, text=city_text, font=fonts["body_bold"], fill="#090D16", anchor="w", tags=("ui_element", card_tag))
            self.canvas.create_text(x + 16, cy + 32, text=city_text, font=fonts["body_bold"], fill="#FFFFFF", anchor="w", tags=("ui_element", card_tag))

            # Condition text (light grey with subtle shadow, replacing pale blue)
            cond_raw = c.get("condition", "Clear")
            cond_text = truncate_text(fonts["small_bold"], cond_raw, max_text_w)
            self.canvas.create_text(x + 17, cy + card_h - 12, text=cond_text, font=fonts["small_bold"], fill="#090D16", anchor="w", tags=("ui_element", card_tag))
            self.canvas.create_text(x + 16, cy + card_h - 13, text=cond_text, font=fonts["small_bold"], fill="#E2E8F0", anchor="w", tags=("ui_element", card_tag))

            # Weather Icon on right (soft colored Pillow vector icon)
            icon_kind = c.get("icon") or cond_raw
            icon_size = min(max(card_h - 18, 28), 38)
            icon_img = get_weather_icon_image(icon_kind, size=icon_size)
            self._icon_refs.append(icon_img)

            self.canvas.create_image(
                x + width - 16 - icon_size // 2, cy + card_h // 2,
                image=icon_img,
                tags=("ui_element", card_tag)
            )

            # Click binding
            city_name = c.get("city") or c.get("name", "")
            if self.on_select_city:
                self.canvas.tag_bind(card_tag, "<Button-1>", lambda e, name=city_name: self.on_select_city(name))
                self.canvas.tag_bind(card_tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
                self.canvas.tag_bind(card_tag, "<Leave>", lambda e: self.canvas.config(cursor=""))
                self.canvas.tag_bind(card_tag, "<Leave>", lambda e: self.canvas.config(cursor=""))
