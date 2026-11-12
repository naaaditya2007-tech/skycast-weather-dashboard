"""
SkyCast Desktop UI — Atmospheric Particle Animation Engine (Stage 5)
--------------------------------------------------------------------
Renders dynamic weather particle effects directly on the Tkinter Canvas:
- Drizzle (fine, gentle mist drops)
- Rain with splashes (angled falling drops that trigger expanding ripple splashes at the bottom)
- Thunderstorm with lightning (heavy driving rain + multi-segment branching lightning bolt + flash)
- Snow (swirling snowflakes with sinusoidal horizontal drift and varied flutter)
- Fog haze (translucent horizontal misty cloud bands floating across the horizon)
- Stars on clear nights (twinkling star field with pulsing glow and occasional starburst crosses)
- Drifting clouds (layered cumulus puffs gliding smoothly across the horizon)

Guarantees:
- ~30 FPS loop via `canvas.after(33)`
- Strictly layered ABOVE `bg_image` but BELOW `glass_panel`, ensuring realistic depth behind frosted glass
- Minimal CPU overhead: does not touch or re-render glass panels or UI text elements
"""

import random
import math
import tkinter as tk
from typing import List, Dict, Any, Optional, Tuple

class WeatherAnimator:
    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self.animation_type = "none"
        self.is_running = False
        self.particles: List[Dict[str, Any]] = []
        self.splashes: List[Dict[str, Any]] = []
        self.clouds: List[Dict[str, Any]] = []
        self.stars: List[Dict[str, Any]] = []
        self.fog_bands: List[Dict[str, Any]] = []
        self.lightning_flash = 0
        self.lightning_bolt: Optional[List[Tuple[int, int]]] = None
        self.lightning_bolt_life = 0
        self._after_id: Optional[str] = None

    def set_animation(self, anim_type: str):
        """Switch active animation mode cleanly without interrupting frame loop."""
        norm_type = (anim_type or "").lower().strip()
        # Aliases
        if norm_type in ("clear_night", "stars_night", "clear-night"):
            norm_type = "stars"
        elif norm_type in ("heavy_rain", "shower", "rain_day", "rain_night"):
            norm_type = "rain"
        elif norm_type in ("thunder", "storm", "thunderstorm_day", "thunderstorm_night"):
            norm_type = "thunderstorm"
        elif norm_type in ("snow_day", "snow_night", "blizzard"):
            norm_type = "snow"
        elif norm_type in ("haze", "mist", "fog_day", "fog_night"):
            norm_type = "fog"
        elif norm_type in ("overcast", "partly_cloudy"):
            norm_type = "clouds"

        if self.animation_type == norm_type and self.is_running:
            return

        self.clear()
        self.animation_type = norm_type

        w = max(self.canvas.winfo_width(), 1100)
        h = max(self.canvas.winfo_height(), 750)

        # 1. Rain (with bottom splashes)
        if norm_type == "rain":
            self.particles = [
                {
                    "x": random.randint(-50, w + 100),
                    "y": random.randint(-80, h),
                    "len": random.randint(14, 24),
                    "speed": random.uniform(14, 21),
                    "width": random.choice([1, 1, 2]),
                    "slant": random.uniform(2.5, 4.0),
                    "color": random.choice(["#7DD3FC", "#93C5FD", "#BAE6FD", "#38BDF8"])
                }
                for _ in range(95)
            ]
            self.splashes = []

        # 2. Drizzle (fine, gentle mist)
        elif norm_type == "drizzle":
            self.particles = [
                {
                    "x": random.randint(0, w + 50),
                    "y": random.randint(-40, h),
                    "len": random.randint(8, 14),
                    "speed": random.uniform(7, 11),
                    "width": 1,
                    "slant": random.uniform(0.8, 1.8),
                    "color": random.choice(["#A5F3FC", "#BAE6FD", "#E0F2FE"])
                }
                for _ in range(60)
            ]
            self.splashes = []

        # 3. Thunderstorm (driving rain + lightning bolts + flash)
        elif norm_type == "thunderstorm":
            self.particles = [
                {
                    "x": random.randint(-80, w + 150),
                    "y": random.randint(-80, h),
                    "len": random.randint(18, 30),
                    "speed": random.uniform(18, 27),
                    "width": random.choice([2, 2, 3]),
                    "slant": random.uniform(4.0, 6.5),
                    "color": random.choice(["#93C5FD", "#60A5FA", "#E0E7FF"])
                }
                for _ in range(130)
            ]
            self.splashes = []
            self.lightning_flash = 0
            self.lightning_bolt = None
            self.lightning_bolt_life = 0

        # 4. Snow (swirling snowflakes with sinusoidal flutter)
        elif norm_type == "snow":
            self.particles = [
                {
                    "base_x": random.randint(0, w),
                    "x": 0,
                    "y": random.randint(-40, h),
                    "radius": random.uniform(1.6, 4.2),
                    "speed": random.uniform(1.2, 2.7),
                    "drift_freq": random.uniform(0.015, 0.04),
                    "drift_amp": random.uniform(14, 30),
                    "angle": random.uniform(0, math.pi * 2),
                    "color": random.choice(["#FFFFFF", "#F8FAFC", "#F1F5F9", "#E2E8F0"])
                }
                for _ in range(75)
            ]

        # 5. Fog / Haze (drifting horizontal mist bands)
        elif norm_type == "fog":
            self.fog_bands = [
                {
                    "x": random.randint(-300, w),
                    "y": random.randint(40, h - 100),
                    "w": random.randint(280, 520),
                    "h": random.randint(45, 90),
                    "speed": random.uniform(0.25, 0.65),
                    "stipple": random.choice(["gray25", "gray12"]),
                    "color": random.choice(["#94A3B8", "#CBD5E1", "#E2E8F0"])
                }
                for _ in range(9)
            ]

        # 6. Stars (Clear Night twinkling starfield)
        elif norm_type == "stars":
            self.stars = [
                {
                    "x": random.randint(15, w - 15),
                    "y": random.randint(15, h - 80),
                    "base_r": random.uniform(0.9, 2.4),
                    "phase": random.uniform(0, math.pi * 2),
                    "freq": random.uniform(0.03, 0.09),
                    "color": random.choice(["#FFFFFF", "#F8FAFC", "#FDE68A", "#BAE6FD"]),
                    "has_cross": random.random() < 0.22  # 22% of stars have shimmering crosshairs
                }
                for _ in range(75)
            ]

        # 7. Drifting Clouds
        elif norm_type == "clouds":
            self.clouds = [
                {
                    "x": random.randint(-200, w),
                    "y": random.randint(30, int(h * 0.45)),
                    "speed": random.uniform(0.35, 0.85),
                    "size": random.randint(90, 160)
                }
                for _ in range(6)
            ]

        # Start animation frame loop if not already cycling
        if not self.is_running:
            self.is_running = True
            self._tick()

    def clear(self):
        """Clean all particle elements from Canvas."""
        self.canvas.delete("anim_particle")
        self.canvas.delete("lightning_overlay")
        self.particles.clear()
        self.splashes.clear()
        self.clouds.clear()
        self.stars.clear()
        self.fog_bands.clear()
        self.lightning_flash = 0
        self.lightning_bolt = None
        self.lightning_bolt_life = 0

    def stop(self):
        """Halt the animation timer loop."""
        self.is_running = False
        if self._after_id:
            try:
                self.canvas.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        self.clear()

    def trigger_lightning(self, w: int, h: int):
        """Manually or probabilistically generates an atmospheric lightning bolt + flash."""
        self.lightning_flash = 4
        self.lightning_bolt_life = 8
        
        # Generate branching lightning bolt
        start_x = random.randint(int(w * 0.25), int(w * 0.75))
        curr_x, curr_y = start_x, 0
        bolt_points = [(curr_x, curr_y)]
        branches = []
        
        target_y = random.randint(int(h * 0.5), int(h * 0.78))
        segments = random.randint(7, 11)
        step_y = target_y // segments

        for i in range(segments):
            curr_x += random.randint(-35, 35)
            curr_y += step_y
            bolt_points.append((curr_x, curr_y))
            if random.random() < 0.35 and i > 2:
                b_x, b_y = curr_x, curr_y
                branch_pts = [(b_x, b_y)]
                for _ in range(3):
                    b_x += random.randint(-25, 25)
                    b_y += step_y // 2
                    branch_pts.append((b_x, b_y))
                branches.append(branch_pts)
                
        self.lightning_bolt = (bolt_points, branches)

    def _tick(self):
        if not self.is_running:
            return

        w = max(self.canvas.winfo_width(), 1100)
        h = max(self.canvas.winfo_height(), 750)

        # Clear existing particle elements for this frame
        self.canvas.delete("anim_particle")

        # -------------------------------------------------------------
        # 1. Rain (with Splash Ripples)
        # -------------------------------------------------------------
        if self.animation_type == "rain":
            for p in self.particles:
                p["y"] += p["speed"]
                p["x"] -= p["slant"]
                if p["y"] > h - 10:
                    # Spawn splash ripple when hitting floor
                    if len(self.splashes) < 35 and random.random() < 0.65:
                        self.splashes.append({
                            "x": p["x"],
                            "y": h - random.randint(4, 18),
                            "r": 1.5,
                            "max_r": random.uniform(6, 11),
                            "life": 4,
                            "color": p["color"]
                        })
                    p["y"] = random.randint(-50, -10)
                    p["x"] = random.randint(0, w + 80)

                self.canvas.create_line(
                    p["x"], p["y"],
                    p["x"] - p["slant"], p["y"] + p["len"],
                    fill=p["color"],
                    width=p["width"],
                    tags="anim_particle"
                )

            # Update & draw splashes
            surviving_splashes = []
            for s in self.splashes:
                s["r"] += (s["max_r"] - s["r"]) * 0.35
                s["life"] -= 1
                r = s["r"]
                self.canvas.create_oval(
                    s["x"] - r * 1.6, s["y"] - r * 0.5,
                    s["x"] + r * 1.6, s["y"] + r * 0.5,
                    outline=s["color"],
                    width=1,
                    tags="anim_particle"
                )
                if s["life"] > 0:
                    surviving_splashes.append(s)
            self.splashes = surviving_splashes

        # -------------------------------------------------------------
        # 2. Drizzle (Fine Mist)
        # -------------------------------------------------------------
        elif self.animation_type == "drizzle":
            for p in self.particles:
                p["y"] += p["speed"]
                p["x"] -= p["slant"]
                if p["y"] > h:
                    p["y"] = random.randint(-30, -5)
                    p["x"] = random.randint(0, w + 40)

                self.canvas.create_line(
                    p["x"], p["y"],
                    p["x"] - p["slant"], p["y"] + p["len"],
                    fill=p["color"],
                    width=p["width"],
                    tags="anim_particle"
                )

        # -------------------------------------------------------------
        # 3. Thunderstorm (Heavy Rain + Lightning Bolt & Flash)
        # -------------------------------------------------------------
        elif self.animation_type == "thunderstorm":
            for p in self.particles:
                p["y"] += p["speed"]
                p["x"] -= p["slant"]
                if p["y"] > h - 10:
                    if len(self.splashes) < 45 and random.random() < 0.7:
                        self.splashes.append({
                            "x": p["x"],
                            "y": h - random.randint(4, 20),
                            "r": 2.0,
                            "max_r": random.uniform(7, 13),
                            "life": 4,
                            "color": p["color"]
                        })
                    p["y"] = random.randint(-60, -10)
                    p["x"] = random.randint(0, w + 120)

                self.canvas.create_line(
                    p["x"], p["y"],
                    p["x"] - p["slant"], p["y"] + p["len"],
                    fill=p["color"],
                    width=p["width"],
                    tags="anim_particle"
                )

            # Draw splashes
            surviving_splashes = []
            for s in self.splashes:
                s["r"] += (s["max_r"] - s["r"]) * 0.4
                s["life"] -= 1
                r = s["r"]
                self.canvas.create_oval(
                    s["x"] - r * 1.8, s["y"] - r * 0.5,
                    s["x"] + r * 1.8, s["y"] + r * 0.5,
                    outline=s["color"],
                    width=1.5,
                    tags="anim_particle"
                )
                if s["life"] > 0:
                    surviving_splashes.append(s)
            self.splashes = surviving_splashes

            # Lightning Flash & Bolt logic
            self.canvas.delete("lightning_overlay")
            
            # Random spontaneous lightning strike (~1.5% chance per frame)
            if random.random() < 0.015 and self.lightning_flash == 0:
                self.trigger_lightning(w, h)

            # Render flash
            if self.lightning_flash > 0:
                self.lightning_flash -= 1
                stipple_pat = "gray50" if self.lightning_flash >= 2 else "gray25"
                self.canvas.create_rectangle(
                    0, 0, w, h,
                    fill="#FFFFFF",
                    stipple=stipple_pat,
                    tags="lightning_overlay"
                )

            # Render bolt
            if self.lightning_bolt and self.lightning_bolt_life > 0:
                self.lightning_bolt_life -= 1
                main_bolt, branches = self.lightning_bolt
                for i in range(len(main_bolt) - 1):
                    p1 = main_bolt[i]
                    p2 = main_bolt[i + 1]
                    self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill="#FFFFFF", width=3, tags="anim_particle")
                    self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill="#38BDF8", width=1.5, tags="anim_particle")
                for branch in branches:
                    for i in range(len(branch) - 1):
                        p1 = branch[i]
                        p2 = branch[i + 1]
                        self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill="#E0F2FE", width=1.5, tags="anim_particle")
            else:
                self.lightning_bolt = None

        # -------------------------------------------------------------
        # 4. Snow (Swirling Snowflakes)
        # -------------------------------------------------------------
        elif self.animation_type == "snow":
            for p in self.particles:
                p["y"] += p["speed"]
                p["angle"] += p["drift_freq"]
                p["x"] = p["base_x"] + math.sin(p["angle"]) * p["drift_amp"]

                if p["y"] > h + 10:
                    p["y"] = -15
                    p["base_x"] = random.randint(0, w)

                r = p["radius"]
                self.canvas.create_oval(
                    p["x"] - r, p["y"] - r,
                    p["x"] + r, p["y"] + r,
                    fill=p["color"],
                    outline="",
                    tags="anim_particle"
                )

        # -------------------------------------------------------------
        # 5. Fog Haze (Floating Horizontal Mist Bands)
        # -------------------------------------------------------------
        elif self.animation_type == "fog":
            for f in self.fog_bands:
                f["x"] += f["speed"]
                if f["x"] - f["w"] > w:
                    f["x"] = -f["w"] * 1.2
                    f["y"] = random.randint(40, h - 100)

                # Soft rounded haze ellipse
                self.canvas.create_oval(
                    f["x"], f["y"],
                    f["x"] + f["w"], f["y"] + f["h"],
                    fill=f["color"],
                    stipple=f["stipple"],
                    outline="",
                    tags="anim_particle"
                )

        # -------------------------------------------------------------
        # 6. Stars (Clear Night Twinkling Field)
        # -------------------------------------------------------------
        elif self.animation_type == "stars":
            for s in self.stars:
                s["phase"] += s["freq"]
                pulse = (math.sin(s["phase"]) + 1.0) / 2.0  # 0.0 to 1.0
                r = s["base_r"] * (0.6 + pulse * 0.7)

                self.canvas.create_oval(
                    s["x"] - r, s["y"] - r,
                    s["x"] + r, s["y"] + r,
                    fill=s["color"],
                    outline="",
                    tags="anim_particle"
                )

                # Shimmer crosshairs for primary bright stars
                if s["has_cross"] and pulse > 0.65:
                    cross_len = r * 2.8
                    self.canvas.create_line(
                        s["x"] - cross_len, s["y"],
                        s["x"] + cross_len, s["y"],
                        fill="#FFFFFF", width=1,
                        tags="anim_particle"
                    )
                    self.canvas.create_line(
                        s["x"], s["y"] - cross_len,
                        s["x"], s["y"] + cross_len,
                        fill="#FFFFFF", width=1,
                        tags="anim_particle"
                    )

        # -------------------------------------------------------------
        # 7. Drifting Clouds
        # -------------------------------------------------------------
        elif self.animation_type == "clouds":
            for c in self.clouds:
                c["x"] += c["speed"]
                if c["x"] - c["size"] > w:
                    c["x"] = -c["size"] * 2.2
                    c["y"] = random.randint(30, int(h * 0.45))

                sz = c["size"]
                self.canvas.create_oval(
                    c["x"], c["y"], c["x"] + sz, c["y"] + sz * 0.55,
                    fill="#FFFFFF", stipple="gray25", outline="",
                    tags="anim_particle"
                )
                self.canvas.create_oval(
                    c["x"] + sz * 0.25, c["y"] - sz * 0.2,
                    c["x"] + sz * 0.85, c["y"] + sz * 0.5,
                    fill="#F1F5F9", stipple="gray25", outline="",
                    tags="anim_particle"
                )

        # -------------------------------------------------------------
        # Layering Enforcement: Above Background, strictly Below Glass Panels
        # -------------------------------------------------------------
        if self.canvas.find_withtag("glass_panel"):
            self.canvas.tag_lower("anim_particle", "glass_panel")
            self.canvas.tag_lower("lightning_overlay", "glass_panel")
        if self.canvas.find_withtag("bg_image"):
            self.canvas.tag_lower("bg_image")

        # Schedule next tick at ~30 FPS (33ms)
        self._after_id = self.canvas.after(33, self._tick)
