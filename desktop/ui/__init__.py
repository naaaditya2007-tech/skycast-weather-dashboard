"""Desktop UI package for SkyCast."""
from .main_window import SkyCastApp
from .theme import get_theme, THEMES
from .panels import get_gradient_image, create_glass_card
from .animations import WeatherAnimator

__all__ = ["SkyCastApp", "get_theme", "THEMES", "get_gradient_image", "create_glass_card", "WeatherAnimator"]
