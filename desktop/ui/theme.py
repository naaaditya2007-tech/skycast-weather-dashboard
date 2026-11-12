"""
Color themes and atmospheric styles for SkyCast Desktop.
Provides gradient definitions, glass overlay colors, and accents for each weather condition.
"""

THEMES = {
    "sunny_day": {
        "gradient_top": (25, 42, 86),       # Deep royal twilight blue
        "gradient_bottom": (243, 156, 18),  # Warm amber horizon
        "glass_fill": (255, 255, 255, 30),
        "glass_border": (255, 255, 255, 80),
        "text_primary": "#FFFFFF",
        "text_secondary": "#F39C12",
        "accent": "#F1C40F",
        "badge_bg": "#E67E22"
    },
    "sunny_night": {
        "gradient_top": (10, 15, 30),
        "gradient_bottom": (24, 44, 89),
        "glass_fill": (255, 255, 255, 20),
        "glass_border": (255, 255, 255, 50),
        "text_primary": "#F0F4F8",
        "text_secondary": "#829AB1",
        "accent": "#64B5F6",
        "badge_bg": "#1E3A8A"
    },
    "partly_cloudy_day": {
        "gradient_top": (30, 50, 92),
        "gradient_bottom": (70, 130, 180),
        "glass_fill": (255, 255, 255, 28),
        "glass_border": (255, 255, 255, 75),
        "text_primary": "#FFFFFF",
        "text_secondary": "#BEE3F8",
        "accent": "#63B3ED",
        "badge_bg": "#2B6CB0"
    },
    "partly_cloudy_night": {
        "gradient_top": (13, 20, 36),
        "gradient_bottom": (33, 44, 66),
        "glass_fill": (255, 255, 255, 22),
        "glass_border": (255, 255, 255, 55),
        "text_primary": "#E2E8F0",
        "text_secondary": "#94A3B8",
        "accent": "#7DD3FC",
        "badge_bg": "#1E293B"
    },
    "cloudy": {
        "gradient_top": (26, 36, 48),
        "gradient_bottom": (65, 84, 104),
        "glass_fill": (255, 255, 255, 25),
        "glass_border": (255, 255, 255, 60),
        "text_primary": "#F8FAFC",
        "text_secondary": "#CBD5E1",
        "accent": "#94A3B8",
        "badge_bg": "#334155"
    },
    "rainy": {
        "gradient_top": (15, 28, 48),
        "gradient_bottom": (35, 65, 95),
        "glass_fill": (255, 255, 255, 25),
        "glass_border": (255, 255, 255, 65),
        "text_primary": "#FFFFFF",
        "text_secondary": "#93C5FD",
        "accent": "#38BDF8",
        "badge_bg": "#0369A1"
    },
    "thunderstorm": {
        "gradient_top": (15, 12, 35),
        "gradient_bottom": (45, 25, 75),
        "glass_fill": (255, 255, 255, 22),
        "glass_border": (200, 180, 255, 80),
        "text_primary": "#FFFFFF",
        "text_secondary": "#D8B4FE",
        "accent": "#FBBF24",
        "badge_bg": "#581C87"
    },
    "snow": {
        "gradient_top": (20, 35, 55),
        "gradient_bottom": (75, 110, 145),
        "glass_fill": (255, 255, 255, 35),
        "glass_border": (255, 255, 255, 90),
        "text_primary": "#FFFFFF",
        "text_secondary": "#E2E8F0",
        "accent": "#BAE6FD",
        "badge_bg": "#0284C7"
    },
    "fog_day": {
        "gradient_top": (40, 50, 60),
        "gradient_bottom": (90, 105, 120),
        "glass_fill": (255, 255, 255, 25),
        "glass_border": (255, 255, 255, 60),
        "text_primary": "#FFFFFF",
        "text_secondary": "#E2E8F0",
        "accent": "#CBD5E1",
        "badge_bg": "#475569"
    },
    "fog_night": {
        "gradient_top": (15, 20, 25),
        "gradient_bottom": (35, 45, 55),
        "glass_fill": (255, 255, 255, 20),
        "glass_border": (255, 255, 255, 50),
        "text_primary": "#E2E8F0",
        "text_secondary": "#94A3B8",
        "accent": "#94A3B8",
        "badge_bg": "#1E293B"
    }
}

DEFAULT_THEME = THEMES["partly_cloudy_day"]

def get_theme(theme_name: str) -> dict:
    """Returns the theme dictionary with fallback."""
    return THEMES.get(theme_name, DEFAULT_THEME)
