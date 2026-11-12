"""
SkyCast Desktop UI Panel & Glassmorphism Renderer
-------------------------------------------------
Uses Pillow (PIL) to generate semi-transparent frosted cards and rounded outlines.
Maintains an internal image cache so that generated `ImageTk.PhotoImage` objects
are never prematurely garbage collected by Python.
"""

from PIL import Image, ImageDraw, ImageTk
from typing import Tuple, Dict

# Global cache to prevent Python garbage collection of Tkinter PhotoImages
_IMAGE_CACHE: Dict[str, ImageTk.PhotoImage] = {}

def get_gradient_image(width: int, height: int,
                       color_top: Tuple[int, int, int],
                       color_bottom: Tuple[int, int, int]) -> ImageTk.PhotoImage:
    """
    Generate a full-screen vertical linear gradient image.
    Uses linear interpolation (LERP) between color_top and color_bottom.
    """
    w = max(int(width), 10)
    h = max(int(height), 10)
    key = f"grad_{w}_{h}_{color_top}_{color_bottom}"
    if key in _IMAGE_CACHE:
        return _IMAGE_CACHE[key]

    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)

    r1, g1, b1 = color_top
    r2, g2, b2 = color_bottom

    for y in range(h):
        factor = y / max(h - 1, 1)
        r = int(r1 + (r2 - r1) * factor)
        g = int(g1 + (g2 - g1) * factor)
        b = int(b1 + (b2 - b1) * factor)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    photo = ImageTk.PhotoImage(img)
    _IMAGE_CACHE[key] = photo

    # Keep cache bound to prevent memory bloating on continuous resize
    if len(_IMAGE_CACHE) > 35:
        _IMAGE_CACHE.pop(next(iter(_IMAGE_CACHE)))
    return photo

def create_glass_card(width: int, height: int, radius: int = 16,
                      fill_rgba: Tuple[int, int, int, int] = (255, 255, 255, 28),
                      border_rgba: Tuple[int, int, int, int] = (255, 255, 255, 75)) -> ImageTk.PhotoImage:
    """
    Create a translucent rounded rectangle with glassmorphism style.
    Renders cleanly onto an RGBA canvas before conversion to ImageTk.PhotoImage.
    """
    w = max(int(width), 20)
    h = max(int(height), 20)
    key = f"glass_{w}_{h}_{radius}_{fill_rgba}_{border_rgba}"
    if key in _IMAGE_CACHE:
        return _IMAGE_CACHE[key]

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw rounded rectangle with translucent glass fill and outline
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
