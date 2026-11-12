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

# Placeholder initial cities from design reference
PLACEHOLDER_OTHER_CITIES = [
    {"country": "China", "city": "Beijing", "condition": "Cloudy", "icon": "🌧️", "temp": "12°C"},
    {"country": "Japan", "city": "Tokyo", "condition": "Sunny", "icon": "🌤️", "temp": "18°C"},
    {"country": "Brazil", "city": "Brasília", "condition": "Rainy", "icon": "☀️", "temp": "24°C"},
    {"country": "Germany", "city": "Berlin", "condition": "Snowy", "icon": "🌨️", "temp": "3°C"},
    {"country": "Australia", "city": "Canberra", "condition": "Windy", "icon": "🌤️", "temp": "19°C"}
]

class OtherCitiesPanel:
    def __init__(self, canvas: tk.Canvas, on_select_city: Optional[Callable[[str], None]] = None):
        self.canvas = canvas
        self.on_select_city = on_select_city

    def draw(self, bg_image, x: int, y: int, width: int, height: int,
             cities_data: List[Dict[str, Any]],
             theme: Dict[str, Any],
             fonts: Dict[str, Any]):
        """Render the 'Other Cities' right-column stacked cards."""
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
            font=fonts["body"],
            fill=theme["accent"],
            anchor="e",
            tags=("ui_element", see_all_tag)
        )

        cards = cities_data if cities_data else PLACEHOLDER_OTHER_CITIES
        card_count = min(len(cards), 5)
        top_offset = y + 36
        available_h = height - 42
        gap = 10
        card_h = max((available_h - gap * (card_count - 1)) // card_count, 60)

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
                border_opacity=70
            )
            card_tag = f"other_city_card_{i}"
            self.canvas.create_image(x, cy, image=glass_photo, anchor="nw", tags=("glass_panel", card_tag))

            # Country label (small, muted)
            self.canvas.create_text(
                x + 18, cy + 18,
                text=c.get("country", ""),
                font=fonts["small"],
                fill=theme["text_muted"],
                anchor="w",
                tags=("ui_element", card_tag)
            )

            # City name (bold, medium)
            self.canvas.create_text(
                x + 18, cy + 36,
                text=c.get("city") or c.get("name", ""),
                font=fonts["body_bold"],
                fill=theme["text_primary"],
                anchor="w",
                tags=("ui_element", card_tag)
            )

            # Condition text (small)
            self.canvas.create_text(
                x + 18, cy + card_h - 14,
                text=c.get("condition", "Clear"),
                font=fonts["small"],
                fill=theme["text_muted"],
                anchor="w",
                tags=("ui_element", card_tag)
            )

            # Weather Icon on right
            self.canvas.create_text(
                x + width - 24, cy + card_h // 2,
                text=c.get("icon", "🌤️"),
                font=fonts["icon_large"],
                anchor="e",
                tags=("ui_element", card_tag)
            )

            # Click binding
            city_name = c.get("city") or c.get("name", "")
            if self.on_select_city:
                self.canvas.tag_bind(card_tag, "<Button-1>", lambda e, name=city_name: self.on_select_city(name))
                self.canvas.tag_bind(card_tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
                self.canvas.tag_bind(card_tag, "<Leave>", lambda e: self.canvas.config(cursor=""))
