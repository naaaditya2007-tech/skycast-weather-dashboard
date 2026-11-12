"""
SkyCast Desktop UI — Particle Animation Engine
----------------------------------------------
Renders dynamic atmospheric particle effects directly on the Tkinter Canvas:
- Rain (angled raindrops with variable velocity)
- Snow (swirling snowflakes with sinusoidal drift)
- Drifting Clouds (soft layered puffs drifting across horizon)
- Thunderstorms (heavy rain + intermittent canvas lightning flash)
- Sunbeams (soft ambient dust/sun motes)

Runs via non-blocking `canvas.after(33)` (~30 FPS).
"""

import random
import math
import tkinter as tk
from typing import List, Dict, Any, Optional

class WeatherAnimator:
    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self.animation_type = "none"
        self.is_running = False
        self.particles: List[Dict[str, Any]] = []
        self.clouds: List[Dict[str, Any]] = []
        self.lightning_flash = 0
        self._after_id: Optional[str] = None

    def set_animation(self, anim_type: str):
        """Switch active animation mode."""
        if self.animation_type == anim_type and self.is_running:
            return

        self.clear()
        self.animation_type = anim_type

        w = max(self.canvas.winfo_width(), 1000)
        h = max(self.canvas.winfo_height(), 700)

        if anim_type == "rain":
            self.particles = [
                {
                    "x": random.randint(0, w + 100),
                    "y": random.randint(-80, h),
                    "len": random.randint(12, 22),
                    "speed": random.uniform(10, 18),
                    "width": random.choice([1, 1, 2]),
                    "color": random.choice(["#7DD3FC", "#93C5FD", "#BAE6FD"])
                }
                for _ in range(85)
            ]
        elif anim_type == "snow":
            self.particles = [
                {
                    "x": random.randint(0, w),
                    "y": random.randint(-40, h),
                    "radius": random.uniform(1.8, 4.0),
                    "speed": random.uniform(1.2, 2.8),
                    "drift_freq": random.uniform(0.02, 0.05),
                    "drift_amp": random.uniform(15, 25),
                    "base_x": random.randint(0, w),
                    "angle": random.uniform(0, math.pi * 2),
                    "color": random.choice(["#FFFFFF", "#F1F5F9", "#E2E8F0"])
                }
                for _ in range(65)
            ]
        elif anim_type == "thunderstorm":
            self.particles = [
                {
                    "x": random.randint(0, w + 100),
                    "y": random.randint(-80, h),
                    "len": random.randint(16, 26),
                    "speed": random.uniform(14, 22),
                    "width": 2,
                    "color": "#93C5FD"
                }
                for _ in range(110)
            ]
            self.lightning_flash = 0
        elif anim_type == "clouds":
            self.clouds = [
                {
                    "x": random.randint(-200, w),
                    "y": random.randint(20, 180),
                    "speed": random.uniform(0.3, 0.8),
                    "size": random.randint(70, 130)
                }
                for _ in range(5)
            ]
        elif anim_type == "sunbeam":
            self.particles = [
                {
                    "x": random.randint(0, w),
                    "y": random.randint(0, h),
                    "radius": random.uniform(1.5, 3.0),
                    "speed_y": random.uniform(-0.4, 0.4),
                    "speed_x": random.uniform(-0.3, 0.3),
                    "alpha_color": random.choice(["#FDE047", "#FEF08A", "#FBBF24"])
                }
                for _ in range(35)
            ]

        if not self.is_running:
            self.is_running = True
            self._tick()

    def clear(self):
        """Remove existing particle tags from Canvas."""
        self.canvas.delete("anim_particle")
        self.canvas.delete("lightning_overlay")
        self.particles = []
        self.clouds = []

    def stop(self):
        """Halt animation loop."""
        self.is_running = False
        if self._after_id:
            try:
                self.canvas.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        self.clear()

    def _tick(self):
        if not self.is_running:
            return

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100 or h < 100:
            w, h = 1000, 700

        self.canvas.delete("anim_particle")

        if self.animation_type in ("rain", "thunderstorm"):
            for p in self.particles:
                p["y"] += p["speed"]
                p["x"] -= p["speed"] * 0.15
                if p["y"] > h + 20:
                    p["y"] = random.randint(-40, -10)
                    p["x"] = random.randint(0, w + 100)

                self.canvas.create_line(
                    p["x"], p["y"],
                    p["x"] - 2, p["y"] + p["len"],
                    fill=p["color"],
                    width=p["width"],
                    tags="anim_particle"
                )

            if self.animation_type == "thunderstorm":
                self.canvas.delete("lightning_overlay")
                if self.lightning_flash > 0:
                    self.lightning_flash -= 1
                    self.canvas.create_rectangle(
                        0, 0, w, h,
                        fill="#FFFFFF",
                        stipple="gray50" if self.lightning_flash == 1 else "gray25",
                        tags="lightning_overlay"
                    )
                elif random.random() < 0.012:
                    self.lightning_flash = 3

        elif self.animation_type == "snow":
            for p in self.particles:
                p["y"] += p["speed"]
                p["angle"] += p["drift_freq"]
                p["x"] = p["base_x"] + math.sin(p["angle"]) * p["drift_amp"]

                if p["y"] > h + 10:
                    p["y"] = -10
                    p["base_x"] = random.randint(0, w)

                r = p["radius"]
                self.canvas.create_oval(
                    p["x"] - r, p["y"] - r,
                    p["x"] + r, p["y"] + r,
                    fill=p["color"],
                    outline="",
                    tags="anim_particle"
                )

        elif self.animation_type == "clouds":
            for c in self.clouds:
                c["x"] += c["speed"]
                if c["x"] - c["size"] > w:
                    c["x"] = -c["size"] * 2
                    c["y"] = random.randint(20, 160)

                sz = c["size"]
                self.canvas.create_oval(
                    c["x"], c["y"], c["x"] + sz, c["y"] + sz * 0.6,
                    fill="#FFFFFF", stipple="gray25", outline="",
                    tags="anim_particle"
                )
                self.canvas.create_oval(
                    c["x"] + sz * 0.25, c["y"] - sz * 0.2, c["x"] + sz * 0.85, c["y"] + sz * 0.5,
                    fill="#F1F5F9", stipple="gray25", outline="",
                    tags="anim_particle"
                )

        elif self.animation_type == "sunbeam":
            for p in self.particles:
                p["x"] += p["speed_x"]
                p["y"] += p["speed_y"]
                if p["x"] < 0 or p["x"] > w:
                    p["speed_x"] *= -1
                if p["y"] < 0 or p["y"] > h:
                    p["speed_y"] *= -1

                r = p["radius"]
                self.canvas.create_oval(
                    p["x"] - r, p["y"] - r,
                    p["x"] + r, p["y"] + r,
                    fill=p["alpha_color"],
                    outline="",
                    tags="anim_particle"
                )

        # Re-schedule at ~30 FPS
        self._after_id = self.canvas.after(33, self._tick)
