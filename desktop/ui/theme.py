"""
SkyCast Desktop UI Theme Engine
-------------------------------
Provides atmospheric gradients, glassmorphism RGBA color specifications,
text colors, and accent highlights for all weather conditions and day/night cycles.
"""

from typing import Dict, Any, Tuple

THEMES: Dict[str, Dict[str, Any]] = {
    # Clear Sky (Day: Royal Blue to Amber Sun; Night: Deep Midnight to Indigo)
    "clear_day": {
        "gradient_top": (25, 42, 86),
        "gradient_bottom": (230, 126, 34),
        "glass_fill": (255, 255, 255, 28),
        "glass_border": (255, 255, 255, 80),
        "card_fill": (255, 255, 255, 18),
        "card_border": (255, 255, 255, 55),
        "text_primary": "#FFFFFF",
        "text_secondary": "#FDE68A",
        "text_muted": "#CBD5E1",
        "accent": "#F1C40F",
        "badge_bg": "#D97706"
    },
    "clear_night": {
        "gradient_top": (10, 15, 30),
        "gradient_bottom": (24, 44, 89),
        "glass_fill": (255, 255, 255, 20),
        "glass_border": (255, 255, 255, 55),
        "card_fill": (255, 255, 255, 12),
        "card_border": (255, 255, 255, 40),
        "text_primary": "#F8FAFC",
        "text_secondary": "#93C5FD",
        "text_muted": "#64748B",
        "accent": "#60A5FA",
        "badge_bg": "#1E3A8A"
    },
    # Cloudy & Overcast
    "cloudy_day": {
        "gradient_top": (30, 50, 92),
        "gradient_bottom": (70, 130, 180),
        "glass_fill": (255, 255, 255, 26),
        "glass_border": (255, 255, 255, 75),
        "card_fill": (255, 255, 255, 16),
        "card_border": (255, 255, 255, 50),
        "text_primary": "#FFFFFF",
        "text_secondary": "#BAE6FD",
        "text_muted": "#CBD5E1",
        "accent": "#38BDF8",
        "badge_bg": "#0284C7"
    },
    "cloudy_night": {
        "gradient_top": (13, 20, 36),
        "gradient_bottom": (33, 44, 66),
        "glass_fill": (255, 255, 255, 20),
        "glass_border": (255, 255, 255, 50),
        "card_fill": (255, 255, 255, 12),
        "card_border": (255, 255, 255, 38),
        "text_primary": "#E2E8F0",
        "text_secondary": "#94A3B8",
        "text_muted": "#64748B",
        "accent": "#7DD3FC",
        "badge_bg": "#1E293B"
    },
    # Drizzle
    "drizzle_day": {
        "gradient_top": (22, 38, 62),
        "gradient_bottom": (54, 94, 134),
        "glass_fill": (255, 255, 255, 24),
        "glass_border": (255, 255, 255, 70),
        "card_fill": (255, 255, 255, 15),
        "card_border": (255, 255, 255, 48),
        "text_primary": "#FFFFFF",
        "text_secondary": "#A5F3FC",
        "text_muted": "#CBD5E1",
        "accent": "#22D3EE",
        "badge_bg": "#0E7490"
    },
    "drizzle_night": {
        "gradient_top": (12, 22, 38),
        "gradient_bottom": (28, 48, 70),
        "glass_fill": (255, 255, 255, 20),
        "glass_border": (255, 255, 255, 50),
        "card_fill": (255, 255, 255, 12),
        "card_border": (255, 255, 255, 38),
        "text_primary": "#E2E8F0",
        "text_secondary": "#67E8F9",
        "text_muted": "#64748B",
        "accent": "#22D3EE",
        "badge_bg": "#155E75"
    },
    # Rain
    "rain_day": {
        "gradient_top": (15, 28, 48),
        "gradient_bottom": (35, 65, 95),
        "glass_fill": (255, 255, 255, 24),
        "glass_border": (255, 255, 255, 65),
        "card_fill": (255, 255, 255, 15),
        "card_border": (255, 255, 255, 45),
        "text_primary": "#FFFFFF",
        "text_secondary": "#93C5FD",
        "text_muted": "#CBD5E1",
        "accent": "#38BDF8",
        "badge_bg": "#0369A1"
    },
    "rain_night": {
        "gradient_top": (10, 18, 32),
        "gradient_bottom": (22, 40, 62),
        "glass_fill": (255, 255, 255, 18),
        "glass_border": (255, 255, 255, 48),
        "card_fill": (255, 255, 255, 10),
        "card_border": (255, 255, 255, 35),
        "text_primary": "#E2E8F0",
        "text_secondary": "#60A5FA",
        "text_muted": "#64748B",
        "accent": "#38BDF8",
        "badge_bg": "#075985"
    },
    # Snow
    "snow_day": {
        "gradient_top": (20, 35, 55),
        "gradient_bottom": (75, 110, 145),
        "glass_fill": (255, 255, 255, 35),
        "glass_border": (255, 255, 255, 95),
        "card_fill": (255, 255, 255, 22),
        "card_border": (255, 255, 255, 65),
        "text_primary": "#FFFFFF",
        "text_secondary": "#E0F2FE",
        "text_muted": "#CBD5E1",
        "accent": "#BAE6FD",
        "badge_bg": "#0284C7"
    },
    "snow_night": {
        "gradient_top": (14, 24, 38),
        "gradient_bottom": (38, 62, 88),
        "glass_fill": (255, 255, 255, 25),
        "glass_border": (255, 255, 255, 70),
        "card_fill": (255, 255, 255, 15),
        "card_border": (255, 255, 255, 48),
        "text_primary": "#F0F9FF",
        "text_secondary": "#BAE6FD",
        "text_muted": "#64748B",
        "accent": "#7DD3FC",
        "badge_bg": "#0369A1"
    },
    # Thunderstorm
    "thunderstorm_day": {
        "gradient_top": (18, 14, 40),
        "gradient_bottom": (48, 28, 80),
        "glass_fill": (255, 255, 255, 22),
        "glass_border": (200, 180, 255, 75),
        "card_fill": (255, 255, 255, 14),
        "card_border": (200, 180, 255, 45),
        "text_primary": "#FFFFFF",
        "text_secondary": "#E9D5FF",
        "text_muted": "#CBD5E1",
        "accent": "#FBBF24",
        "badge_bg": "#6B21A8"
    },
    "thunderstorm_night": {
        "gradient_top": (10, 8, 25),
        "gradient_bottom": (32, 18, 55),
        "glass_fill": (255, 255, 255, 18),
        "glass_border": (180, 160, 240, 60),
        "card_fill": (255, 255, 255, 10),
        "card_border": (180, 160, 240, 38),
        "text_primary": "#F3E8FF",
        "text_secondary": "#D8B4FE",
        "text_muted": "#64748B",
        "accent": "#F59E0B",
        "badge_bg": "#581C87"
    },
    # Fog
    "fog_day": {
        "gradient_top": (40, 50, 60),
        "gradient_bottom": (90, 105, 120),
        "glass_fill": (255, 255, 255, 25),
        "glass_border": (255, 255, 255, 65),
        "card_fill": (255, 255, 255, 15),
        "card_border": (255, 255, 255, 45),
        "text_primary": "#FFFFFF",
        "text_secondary": "#E2E8F0",
        "text_muted": "#94A3B8",
        "accent": "#E2E8F0",
        "badge_bg": "#475569"
    },
    "fog_night": {
        "gradient_top": (18, 22, 28),
        "gradient_bottom": (40, 48, 56),
        "glass_fill": (255, 255, 255, 20),
        "glass_border": (255, 255, 255, 50),
        "card_fill": (255, 255, 255, 12),
        "card_border": (255, 255, 255, 35),
        "text_primary": "#E2E8F0",
        "text_secondary": "#94A3B8",
        "text_muted": "#64748B",
        "accent": "#CBD5E1",
        "badge_bg": "#334155"
    }
}

DEFAULT_THEME = THEMES["cloudy_day"]

def get_theme(theme_key: str) -> Dict[str, Any]:
    """Retrieve theme styling dictionary by condition key with automatic fallback."""
    return THEMES.get(theme_key, DEFAULT_THEME)
