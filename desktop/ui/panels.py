"""
SkyCast Desktop UI — Frosted Glass Panel Renderer
-------------------------------------------------
Implements true optical frosted glass using Pillow (PIL):
1. Crops the panel's exact bounding box from the underlying full background image.
2. Applies a Gaussian blur (ImageFilter.GaussianBlur) to simulate frosted diffusion.
3. Composites a translucent white tint (15-20% opacity) for glass highlights.
4. Masks with an anti-aliased rounded rectangle.
5. Strokes a subtle thin translucent border outline.
6. Converts to ImageTk.PhotoImage and caches references to prevent Python GC.

Panels are rendered once and re-rendered ONLY on window resize or theme changes.
"""

from PIL import Image, ImageDraw, ImageFilter, ImageTk
from typing import Tuple, Dict, Any, Optional

# Global cache mapping keys to PhotoImage instances to prevent Python garbage collection
_PANEL_CACHE: Dict[str, ImageTk.PhotoImage] = {}
_BG_CACHE: Dict[str, ImageTk.PhotoImage] = {}

def generate_procedural_background(width: int, height: int,
                                   color_top: Tuple[int, int, int],
                                   color_bottom: Tuple[int, int, int],
                                   accent_color: Optional[Tuple[int, int, int]] = None) -> Image.Image:
    """
    Generate an atmospheric high-resolution procedural background PIL Image.
    Uses linear interpolation across vertical scanlines with subtle atmospheric curve.
    """
    w = max(int(width), 20)
    h = max(int(height), 20)

    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)

    r1, g1, b1 = color_top
    r2, g2, b2 = color_bottom

    for y in range(h):
        # Smooth cosine-based atmospheric interpolation
        factor = y / max(h - 1, 1)
        r = int(r1 + (r2 - r1) * factor)
        g = int(g1 + (g2 - g1) * factor)
        b = int(b1 + (b2 - b1) * factor)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    return img

def render_frosted_glass_panel(bg_image: Image.Image,
                               x: int, y: int,
                               width: int, height: int,
                               radius: int = 18,
                               blur_radius: int = 16,
                               tint_opacity: float = 0.18,
                               border_opacity: int = 85) -> ImageTk.PhotoImage:
    """
    Creates an authentic frosted glass panel:
    1. Crops background under (x, y, x + width, y + height).
    2. Blurs the cropped patch with GaussianBlur.
    3. Overlays white tint at 15-20% opacity.
    4. Masks with rounded rectangle.
    5. Adds a thin, lighter 1px border.
    """
    w = max(int(width), 10)
    h = max(int(height), 10)
    x = max(int(x), 0)
    y = max(int(y), 0)

    # Unique cache key for this panel geometry
    cache_key = f"glass_{x}_{y}_{w}_{h}_{radius}_{blur_radius}_{tint_opacity}"
    if cache_key in _PANEL_CACHE:
        return _PANEL_CACHE[cache_key]

    # Ensure crop coordinates stay within background boundaries
    bg_w, bg_h = bg_image.size
    crop_x2 = min(x + w, bg_w)
    crop_y2 = min(y + h, bg_h)

    # Crop matching region from background
    cropped = bg_image.crop((x, y, crop_x2, crop_y2))
    if cropped.size != (w, h):
        cropped = cropped.resize((w, h), Image.Resampling.LANCZOS)

    # 1. Apply Gaussian diffusion
    blurred = cropped.filter(ImageFilter.GaussianBlur(blur_radius)).convert("RGBA")

    # 2. Translucent white glass tint overlay (15-20% opacity)
    alpha_tint = int(255 * tint_opacity)
    tint_layer = Image.new("RGBA", (w, h), (255, 255, 255, alpha_tint))
    tinted = Image.alpha_composite(blurred, tint_layer)

    # 3. Create anti-aliased rounded rectangle mask
    mask = Image.new("L", (w, h), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
    tinted.putalpha(mask)

    # 4. Stroke thin lighter border
    draw_panel = ImageDraw.Draw(tinted)
    draw_panel.rounded_rectangle(
        [0, 0, w - 1, h - 1],
        radius=radius,
        outline=(255, 255, 255, border_opacity),
        width=1
    )

    # 5. Convert to PhotoImage and cache
    photo = ImageTk.PhotoImage(tinted)
    _PANEL_CACHE[cache_key] = photo

    # Bound cache size to prevent memory leak on continuous resize
    if len(_PANEL_CACHE) > 60:
        _PANEL_CACHE.pop(next(iter(_PANEL_CACHE)))

    return photo

def clear_panel_cache():
    """Clear cached PhotoImages when theme or background changes."""
    _PANEL_CACHE.clear()
    _BG_CACHE.clear()

# Backward-compatibility aliases
get_gradient_image = generate_procedural_background
create_glass_card = render_frosted_glass_panel

