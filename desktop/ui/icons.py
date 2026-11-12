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

def get_icon_for_wmo(code: int, is_day: int = 1) -> str:
    """Map WMO weather code to icon name."""
    if code == 0:
        return "sun" if is_day else "clear_night"
    elif code in (1, 2):
        return "partly" if is_day else "partly_night"
    elif code == 3:
        return "cloud"
    elif code in (45, 48):
        return "fog"
    elif code in (51, 53, 55, 56, 57):
        return "drizzle"
    elif code in (61, 63, 65, 66, 67, 80, 81, 82):
        return "rain"
    elif code in (71, 73, 75, 77, 85, 86):
        return "snow"
    elif code in (95, 96, 99):
        return "thunder"
    return "cloud"

def clear_icon_cache():
    """Clear cached icon PhotoImages (e.g. between Tk root instances)."""
    _ICON_CACHE.clear()

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
        # Elegant flowing wind streaks with dark contrast backing and bright foreground
        shadow_color = (15, 23, 42, 220)
        fore_color = (255, 255, 255, 255)
        sw = max(3 * scale, 3)
        fw = max(2 * scale, 2)
        so = 1 * scale

        # Shadow passes
        draw.arc([int(w * 0.15) + so, int(w * 0.30) + so, int(w * 0.75) + so, int(w * 0.55) + so], start=180, end=0, fill=shadow_color, width=sw)
        draw.arc([int(w * 0.65) + so, int(w * 0.30) + so, int(w * 0.85) + so, int(w * 0.45) + so], start=0, end=270, fill=shadow_color, width=sw)
        draw.arc([int(w * 0.22) + so, int(w * 0.55) + so, int(w * 0.85) + so, int(w * 0.78) + so], start=180, end=0, fill=shadow_color, width=sw)

        # Foreground crisp white passes
        draw.arc([int(w * 0.15), int(w * 0.30), int(w * 0.75), int(w * 0.55)], start=180, end=0, fill=fore_color, width=fw)
        draw.arc([int(w * 0.65), int(w * 0.30), int(w * 0.85), int(w * 0.45)], start=0, end=270, fill=fore_color, width=fw)
        draw.arc([int(w * 0.22), int(w * 0.55), int(w * 0.85), int(w * 0.78)], start=180, end=0, fill=fore_color, width=fw)

    elif "humidity" in name or "drop" in name:
        # Glossy cyan water droplet with dark outline and white reflection
        cx = w // 2
        top_y = int(w * 0.16)
        r = int(w * 0.28)
        cy = int(w * 0.60)
        # Shadow/dark stroke backing
        draw.ellipse([cx - r - scale, cy - r - scale, cx + r + scale, cy + r + scale], fill=(15, 23, 42, 180))
        pts_s = [(cx, top_y - scale), (cx - r - scale, cy), (cx + r + scale, cy)]
        draw.polygon(pts_s, fill=(15, 23, 42, 180))
        # Teardrop body
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(56, 189, 248, 255))
        pts = [(cx, top_y), (cx - r + 3 * scale, cy), (cx + r - 3 * scale, cy)]
        draw.polygon(pts, fill=(56, 189, 248, 255))
        # Gloss highlight
        draw.ellipse([cx - int(r * 0.55), cy - int(r * 0.45), cx - int(r * 0.15), cy - int(r * 0.15)], fill=(255, 255, 255, 220))

    elif "visibility" in name or "haze" in name or "fog" in name:
        # Layered misty haze horizontal pill lines with dark backing
        shadow_col = (15, 23, 42, 200)
        fore_col = (255, 255, 255, 255)
        sw = max(4 * scale, 4)
        fw = max(3 * scale, 3)
        y_lines = [int(w * 0.35), int(w * 0.50), int(w * 0.65), int(w * 0.80)]
        widths = [(0.20, 0.80), (0.12, 0.88), (0.24, 0.76), (0.32, 0.68)]
        so = 1 * scale
        for yl, (x1f, x2f) in zip(y_lines, widths):
            draw.line([(int(w * x1f) + so, yl + so), (int(w * x2f) + so, yl + so)], fill=shadow_col, width=sw)
        for yl, (x1f, x2f) in zip(y_lines, widths):
            draw.line([(int(w * x1f), yl), (int(w * x2f), yl)], fill=fore_col, width=fw)

    elif "barometer" in name or "pressure" in name:
        # Pressure Gauge / Barometer Dial
        cx, cy = w // 2, w // 2
        r = int(w * 0.38)
        so = 1 * scale
        # Outer dial ring
        draw.ellipse([cx - r + so, cy - r + so, cx + r + so, cy + r + so], outline=(15, 23, 42, 200), width=max(3 * scale, 3))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255, 255), width=max(2 * scale, 2))
        # Needle pointing up-right
        draw.line([(cx + so, cy + so), (int(cx + r * 0.6) + so, int(cy - r * 0.6) + so)], fill=(15, 23, 42, 200), width=max(3 * scale, 3))
        draw.line([(cx, cy), (int(cx + r * 0.6), int(cy - r * 0.6))], fill=(245, 158, 11, 255), width=max(2 * scale, 2))
        # Center pivot
        draw.ellipse([cx - 3 * scale, cy - 3 * scale, cx + 3 * scale, cy + 3 * scale], fill=(255, 255, 255, 255))

    elif "compass" in name or "wind_dir" in name:
        # Wind Direction Compass
        cx, cy = w // 2, w // 2
        r = int(w * 0.38)
        so = 1 * scale
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255, 180), width=max(2 * scale, 2))
        # North Pointer
        pts_n = [(cx, cy - r + 3 * scale), (cx - 4 * scale, cy), (cx + 4 * scale, cy)]
        draw.polygon(pts_n, fill=(239, 68, 68, 255))
        # South Pointer
        pts_s = [(cx, cy + r - 3 * scale), (cx - 4 * scale, cy), (cx + 4 * scale, cy)]
        draw.polygon(pts_s, fill=(226, 232, 240, 255))

    elif "sunrise" in name or "sunset" in name:
        # Solar Horizon
        cx, cy = w // 2, int(w * 0.58)
        r = int(w * 0.28)
        so = 1 * scale
        # Horizon line
        draw.line([(int(w * 0.15), cy + so), (int(w * 0.85), cy + so)], fill=(15, 23, 42, 200), width=max(3 * scale, 3))
        draw.line([(int(w * 0.15), cy), (int(w * 0.85), cy)], fill=(255, 255, 255, 255), width=max(2 * scale, 2))
        # Half Sun rising
        draw.pieslice([cx - r, cy - r, cx + r, cy + r], start=180, end=360, fill=(251, 191, 36, 255))

    elif "aqi" in name or "leaf" in name:
        # Eco Air Quality Leaf / Shield
        cx, cy = w // 2, w // 2
        r = int(w * 0.32)
        so = 1 * scale
        # Soft leaf / shield shape
        pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        draw.polygon([(p[0] + so, p[1] + so) for p in pts], fill=(15, 23, 42, 180))
        draw.polygon(pts, fill=(52, 211, 153, 255))
        draw.line([(cx, cy - r), (cx, cy + r)], fill=(255, 255, 255, 200), width=scale)

    elif "star" in name:
        # Golden 5-Point Star
        cx, cy = w // 2, w // 2
        r_out = int(w * 0.40)
        r_in = int(w * 0.18)
        import math
        pts = []
        for i in range(10):
            r = r_out if i % 2 == 0 else r_in
            ang = math.radians(-90 + i * 36)
            pts.append((cx + int(r * math.cos(ang)), cy + int(r * math.sin(ang))))
        so = 1 * scale
        draw.polygon([(p[0] + so, p[1] + so) for p in pts], fill=(15, 23, 42, 200))
        draw.polygon(pts, fill=(251, 191, 36, 255), outline=(254, 240, 138, 255))

    else:
        # Generic cloud
        _draw_cloud(draw, w, scale, offset_y=0, fill=(255, 255, 255, 240))

    # Downsample cleanly to target size
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(img)
    _ICON_CACHE[cache_key] = photo
    return photo

def _draw_cloud(draw: ImageDraw.ImageDraw, w: int, scale: int, offset_y: int = 0,
                fill: Tuple[int, int, int, int] = (255, 255, 255, 255),
                scale_factor: float = 1.0):
    """Draw a smooth puffy cloud shape with dark contrast backing for glass."""
    cy = int(w * 0.54) + offset_y
    r_main = int(w * 0.20 * scale_factor)
    r_left = int(w * 0.15 * scale_factor)
    r_right = int(w * 0.14 * scale_factor)
    
    cx = w // 2
    base_h = int(r_main * 0.9)
    so = 1 * scale

    # Dark shadow backing pass
    shadow_fill = (15, 23, 42, 140)
    draw.rounded_rectangle([cx - int(r_main * 1.5) + so, cy + so, cx + int(r_main * 1.5) + so, cy + base_h + so],
                           radius=int(base_h // 2), fill=shadow_fill)
    draw.ellipse([cx - r_main + so, cy - int(r_main * 0.8) + so, cx + r_main + so, cy + r_main + so], fill=shadow_fill)
    draw.ellipse([cx - int(r_main * 1.5) + so, cy - int(r_left * 0.4) + so, cx - int(r_main * 0.1) + so, cy + r_left + int(r_left * 0.4) + so], fill=shadow_fill)
    draw.ellipse([cx + int(r_main * 0.2) + so, cy - int(r_right * 0.3) + so, cx + int(r_main * 1.5) + so, cy + r_right + int(r_right * 0.4) + so], fill=shadow_fill)

    # Foreground crisp cloud pass
    draw.rounded_rectangle([cx - int(r_main * 1.5), cy, cx + int(r_main * 1.5), cy + base_h],
                           radius=int(base_h // 2), fill=fill)
    # 3 Puffs
    draw.ellipse([cx - r_main, cy - int(r_main * 0.8), cx + r_main, cy + r_main], fill=fill)
    draw.ellipse([cx - int(r_main * 1.5), cy - int(r_left * 0.4), cx - int(r_main * 0.1), cy + r_left + int(r_left * 0.4)], fill=fill)
    draw.ellipse([cx + int(r_main * 0.2), cy - int(r_right * 0.3), cx + int(r_main * 1.5), cy + r_right + int(r_right * 0.4)], fill=fill)
