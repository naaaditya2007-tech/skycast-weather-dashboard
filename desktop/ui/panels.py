"""
Custom Glassmorphism and UI Panel Renderer for Tkinter Canvas.
Uses Pillow (PIL) to generate semi-transparent frosted cards and rounded outlines.
"""

from PIL import Image, ImageDraw, ImageTk
import tkinter as tk
from typing import Tuple, Dict

_IMAGE_CACHE: Dict[str, ImageTk.PhotoImage] = {}

def get_gradient_image(width: int, height: int,
                       color_top: Tuple[int, int, int],
                       color_bottom: Tuple[int, int, int]) -> ImageTk.PhotoImage:
    """Generate a vertical linear gradient image."""
    key = f"grad_{width}_{height}_{color_top}_{color_bottom}"
    if key in _IMAGE_CACHE:
        return _IMAGE_CACHE[key]

    img = Image.new("RGB", (max(width, 10), max(height, 10)))
    draw = ImageDraw.Draw(img)

    r1, g1, b1 = color_top
    r2, g2, b2 = color_bottom

    for y in range(height):
        factor = y / max(height - 1, 1)
        r = int(r1 + (r2 - r1) * factor)
        g = int(g1 + (g2 - g1) * factor)
        b = int(b1 + (b2 - b1) * factor)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    photo = ImageTk.PhotoImage(img)
    _IMAGE_CACHE[key] = photo
    # Keep cache reasonably sized
    if len(_IMAGE_CACHE) > 30:
        _IMAGE_CACHE.pop(next(iter(_IMAGE_CACHE)))
    return photo

def create_glass_card(width: int, height: int, radius: int = 16,
                      fill_rgba: Tuple[int, int, int, int] = (255, 255, 255, 28),
                      border_rgba: Tuple[int, int, int, int] = (255, 255, 255, 75)) -> ImageTk.PhotoImage:
    """Creates a transparent rounded rectangle with glassmorphism style."""
    w = max(int(width), 20)
    h = max(int(height), 20)
    key = f"glass_{w}_{h}_{radius}_{fill_rgba}_{border_rgba}"
    if key in _IMAGE_CACHE:
        return _IMAGE_CACHE[key]

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded rectangle with translucent fill
    draw.rounded_rectangle(
        [0, 0, w - 1, h - 1],
        radius=radius,
        fill=fill_rgba,
        outline=border_rgba,
        width=1
    )

    photo = ImageTk.PhotoImage(img)
    _IMAGE_CACHE[key] = photo
    return photo
