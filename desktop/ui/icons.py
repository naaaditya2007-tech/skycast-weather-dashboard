"""
SkyCast Desktop UI — Weather & Metric Vector Icons Generator
-----------------------------------------------------------
Generates crisp, high-contrast, soft-colored vector icons rendered with Pillow:
- Crisp white & soft pastel colors designed specifically for frosted glass.
- Eliminates ugly black monochrome emoji silhouettes.
- Caches PhotoImage instances keyed by (icon_name, size).
"""

from typing import Dict, Tuple
from PIL import Image, ImageDraw, ImageTk

_ICON_CACHE: Dict[Tuple[str, int], ImageTk.PhotoImage] = {}

def get_weather_icon_image(icon_name: str, size: int = 32) -> ImageTk.PhotoImage:
    """Return a cached PhotoImage for the given weather icon and pixel size."""
    cache_key = (icon_name.lower(), size)
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    # Render at 2x resolution and downsample with LANCZOS for super-smooth anti-aliasing
    scale = 2
    canvas_size = size * scale
    img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = 4 * scale
    w = canvas_size

    name = icon_name.lower()

    if "sun" in name or "clear" in name:
        # Golden Sun
        cx, cy = w // 2, w // 2
        r = int(w * 0.28)
        # Corona rays
        for angle in range(0, 360, 45):
            import math
            rad = math.radians(angle)
            r1 = r + 4 * scale
            r2 = r + 9 * scale
            x1 = cx + int(math.cos(rad) * r1)
            y1 = cy + int(math.sin(rad) * r1)
            x2 = cx + int(math.cos(rad) * r2)
            y2 = cy + int(math.sin(rad) * r2)
            draw.line([(x1, y1), (x2, y2)], fill=(251, 191, 36, 220), width=max(2 * scale, 2))
        # Sun core
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(251, 191, 36, 255), outline=(254, 240, 138, 255), width=scale)

    elif "partly" in name:
        # Sun peeking behind white cloud
        # Sun behind (top right)
        sx, sy = int(w * 0.64), int(w * 0.38)
        sr = int(w * 0.22)
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(251, 191, 36, 255))
        # Sun rays
        for angle in (-45, 0, 45, 90):
            import math
            rad = math.radians(angle)
            r1 = sr + 3 * scale
            r2 = sr + 7 * scale
            draw.line([(sx + int(math.cos(rad) * r1), sy + int(math.sin(rad) * r1)),
                       (sx + int(math.cos(rad) * r2), sy + int(math.sin(rad) * r2))],
                      fill=(251, 191, 36, 220), width=max(2 * scale, 2))
        # Cloud in foreground
        _draw_cloud(draw, w, scale, offset_y=int(w * 0.12), fill=(255, 255, 255, 245))

    elif "cloud" in name or "overcast" in name:
        # Soft layered white/slate clouds
        _draw_cloud(draw, w, scale, offset_y=-int(w * 0.05), fill=(203, 213, 225, 180), scale_factor=0.85)
        _draw_cloud(draw, w, scale, offset_y=int(w * 0.06), fill=(255, 255, 255, 250))

    elif "rain" in name or "drizzle" in name or "shower" in name:
        # Cloud with cyan/blue raindrops
        _draw_cloud(draw, w, scale, offset_y=-int(w * 0.06), fill=(241, 245, 249, 250))
        # Rain streaks
        rain_color = (56, 189, 248, 240)
        drops = [(int(w * 0.32), int(w * 0.70)), (int(w * 0.50), int(w * 0.74)), (int(w * 0.68), int(w * 0.70))]
        for dx, dy in drops:
            draw.line([(dx, dy), (dx - 3 * scale, dy + 8 * scale)], fill=rain_color, width=max(2 * scale, 2))

    elif "thunder" in name or "storm" in name:
        # Dark storm cloud with yellow lightning bolt
        _draw_cloud(draw, w, scale, offset_y=-int(w * 0.08), fill=(148, 163, 184, 250))
        # Lightning
        pts = [
            (int(w * 0.52), int(w * 0.58)),
            (int(w * 0.42), int(w * 0.74)),
            (int(w * 0.50), int(w * 0.74)),
            (int(w * 0.44), int(w * 0.94)),
            (int(w * 0.62), int(w * 0.70)),
            (int(w * 0.53), int(w * 0.70))
        ]
        draw.polygon(pts, fill=(250, 204, 21, 255))

    elif "snow" in name:
        # Cloud with soft white snowflake crystals
        _draw_cloud(draw, w, scale, offset_y=-int(w * 0.06), fill=(241, 245, 249, 250))
        # Snow crystals
        for sx, sy in [(int(w * 0.32), int(w * 0.74)), (int(w * 0.52), int(w * 0.80)), (int(w * 0.70), int(w * 0.74))]:
            draw.ellipse([sx - 2 * scale, sy - 2 * scale, sx + 2 * scale, sy + 2 * scale], fill=(255, 255, 255, 250))

    elif "wind" in name:
        # Elegant flowing wind streaks
        color = (199, 210, 254, 230)
        lw = max(2 * scale, 2)
        # Line 1
        draw.arc([int(w * 0.15), int(w * 0.30), int(w * 0.75), int(w * 0.55)], start=180, end=0, fill=color, width=lw)
        draw.arc([int(w * 0.65), int(w * 0.30), int(w * 0.85), int(w * 0.45)], start=0, end=270, fill=color, width=lw)
        # Line 2
        draw.arc([int(w * 0.22), int(w * 0.55), int(w * 0.85), int(w * 0.78)], start=180, end=0, fill=color, width=lw)

    elif "humidity" in name or "drop" in name:
        # Glossy cyan water droplet
        cx = w // 2
        top_y = int(w * 0.16)
        r = int(w * 0.28)
        cy = int(w * 0.60)
        # Teardrop body
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(56, 189, 248, 240))
        pts = [(cx, top_y), (cx - r + 3 * scale, cy), (cx + r - 3 * scale, cy)]
        draw.polygon(pts, fill=(56, 189, 248, 240))
        # Gloss highlight
        draw.ellipse([cx - int(r * 0.55), cy - int(r * 0.45), cx - int(r * 0.15), cy - int(r * 0.15)], fill=(255, 255, 255, 180))

    elif "visibility" in name or "haze" in name or "fog" in name:
        # Layered misty haze horizontal pill lines
        color = (226, 232, 240, 230)
        lw = max(3 * scale, 3)
        y_lines = [int(w * 0.35), int(w * 0.50), int(w * 0.65), int(w * 0.80)]
        widths = [(0.20, 0.80), (0.12, 0.88), (0.24, 0.76), (0.32, 0.68)]
        for yl, (x1f, x2f) in zip(y_lines, widths):
            draw.line([(int(w * x1f), yl), (int(w * x2f), yl)], fill=color, width=lw)

    else:
        # Generic cloud
        _draw_cloud(draw, w, scale, offset_y=0, fill=(255, 255, 255, 240))

    # Downsample cleanly to target size
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(img)
    _ICON_CACHE[cache_key] = photo
    return photo

def _draw_cloud(draw: ImageDraw.ImageDraw, w: int, scale: int, offset_y: int = 0,
                fill: Tuple[int, int, int, int] = (255, 255, 255, 245),
                scale_factor: float = 1.0):
    """Draw a smooth puffy cloud shape."""
    cy = int(w * 0.54) + offset_y
    r_main = int(w * 0.20 * scale_factor)
    r_left = int(w * 0.15 * scale_factor)
    r_right = int(w * 0.14 * scale_factor)
    
    cx = w // 2
    # Bottom rounded bar
    base_h = int(r_main * 0.9)
    draw.rounded_rectangle([cx - int(r_main * 1.5), cy, cx + int(r_main * 1.5), cy + base_h],
                           radius=int(base_h // 2), fill=fill)
    # 3 Puffs
    draw.ellipse([cx - r_main, cy - int(r_main * 0.8), cx + r_main, cy + r_main], fill=fill)
    draw.ellipse([cx - int(r_main * 1.5), cy - int(r_left * 0.4), cx - int(r_main * 0.1), cy + r_left + int(r_left * 0.4)], fill=fill)
    draw.ellipse([cx + int(r_main * 0.2), cy - int(r_right * 0.3), cx + int(r_main * 1.5), cy + r_right + int(r_right * 0.4)], fill=fill)
