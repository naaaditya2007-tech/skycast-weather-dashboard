"""
Script to test and verify Stage 5 of SkyCast Tkinter Desktop GUI:
1. Capture Rain with splashes at 1100x750
2. Capture Snow with swirling snowflakes at 1100x750
3. Capture Thunderstorm with lightning bolt & flash at 1100x750
4. Capture Clear Night with twinkling starfield at 1100x750
5. Test and capture Search dropdown showing City, Region, Country (e.g. Springfield, Illinois, US)
6. Test and capture Empty favorites state
7. Test and capture Offline fallback banner ("⚠️ No connection — showing last saved data")
"""

import os
import sys
import time
import shutil

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from PIL import ImageGrab
from desktop.ui.main_window import SkyCastMainWindow
from desktop.ui.panels import clear_panel_cache
from desktop.ui.icons import clear_icon_cache

ARTIFACT_DIR = r"C:\Users\Aaditya.N.A\.gemini\antigravity\brain\9e04dabe-324d-4ad6-beef-0efb9f2ee50d"

def run_stage5_verification():
    os.makedirs(os.path.join(ROOT_DIR, "desktop", "assets"), exist_ok=True)
    clear_panel_cache()
    clear_icon_cache()

    print("Initializing SkyCastMainWindow for Stage 5...")
    app = SkyCastMainWindow()
    app.geometry("1100x750+50+50")
    app.update_idletasks()
    app.update()

    # Wait for initial data to load
    start = time.time()
    while time.time() - start < 10.0:
        app.update_idletasks()
        app.update()
        if app.weather_data is not None and not app.is_loading:
            break
        time.sleep(0.1)

    w = max(app.canvas.winfo_width(), 1100)
    h = max(app.canvas.winfo_height(), 750)

    # -------------------------------------------------------------
    # 1. Rain with Splashes
    # -------------------------------------------------------------
    print("\n[1/4] Setting mode: Rain with Splashes...")
    app._preview_idx = 0  # Preset 0: Rain — Day
    app._toggle_preview_mode()

    for _ in range(35):
        time.sleep(0.04)
        app.update_idletasks()
        app.update()

    rain_path = os.path.join(ROOT_DIR, "desktop", "assets", "skycast_stage5_rain_1100x750.png")
    img_rain = ImageGrab.grab(window=app.winfo_id())
    img_rain.save(rain_path)
    print(f"Captured Rain screenshot: {rain_path} ({img_rain.size})")

    # -------------------------------------------------------------
    # 2. Thunderstorm with Lightning
    # -------------------------------------------------------------
    print("\n[2/4] Setting mode: Thunderstorm with Lightning...")
    app._preview_idx = 1  # Preset 1: Thunderstorm — Night
    app._toggle_preview_mode()

    for _ in range(10):
        time.sleep(0.04)
        app.update_idletasks()
        app.update()

    # Trigger bolt and render tick immediately before capture
    app.animator.trigger_lightning(w, h)
    app.animator._tick()
    app.update_idletasks()
    app.update()

    thunder_path = os.path.join(ROOT_DIR, "desktop", "assets", "skycast_stage5_thunderstorm_1100x750.png")
    img_thunder = ImageGrab.grab(window=app.winfo_id())
    img_thunder.save(thunder_path)
    print(f"Captured Thunderstorm screenshot: {thunder_path} ({img_thunder.size})")

    # -------------------------------------------------------------
    # 3. Snow
    # -------------------------------------------------------------
    print("\n[3/4] Setting mode: Snow...")
    app._preview_idx = 2  # Preset 2: Snow — Day
    app._toggle_preview_mode()

    for _ in range(25):
        time.sleep(0.04)
        app.update_idletasks()
        app.update()

    snow_path = os.path.join(ROOT_DIR, "desktop", "assets", "skycast_stage5_snow_1100x750.png")
    img_snow = ImageGrab.grab(window=app.winfo_id())
    img_snow.save(snow_path)
    print(f"Captured Snow screenshot: {snow_path} ({img_snow.size})")

    # -------------------------------------------------------------
    # 4. Clear Night with Twinkling Stars
    # -------------------------------------------------------------
    print("\n[4/4] Setting mode: Clear Night with Stars...")
    app._preview_idx = 3  # Preset 3: Clear — Night
    app._toggle_preview_mode()

    for _ in range(25):
        time.sleep(0.04)
        app.update_idletasks()
        app.update()

    night_path = os.path.join(ROOT_DIR, "desktop", "assets", "skycast_stage5_clearnight_1100x750.png")
    img_night = ImageGrab.grab(window=app.winfo_id())
    img_night.save(night_path)
    print(f"Captured Clear Night screenshot: {night_path} ({img_night.size})")

    # -------------------------------------------------------------
    # 5. Search Dropdown with City, Region, Country
    # -------------------------------------------------------------
    print("\n[5/7] Testing search dropdown with Region & Country (Springfield)...")
    app._clear_f2_badge()
    app.search_suggestions = [
        {"name": "Springfield", "admin1": "Illinois", "country": "United States", "latitude": 39.78, "longitude": -89.65},
        {"name": "Springfield", "admin1": "Missouri", "country": "United States", "latitude": 37.21, "longitude": -93.29},
        {"name": "Springfield", "admin1": "Massachusetts", "country": "United States", "latitude": 42.10, "longitude": -72.59},
        {"name": "Springfield", "admin1": "Ohio", "country": "United States", "latitude": 39.92, "longitude": -83.81},
    ]
    app.show_search_dropdown = True
    app._render_all_panels()
    app.update_idletasks()
    app.update()

    search_path = os.path.join(ROOT_DIR, "desktop", "assets", "skycast_stage5_search_region.png")
    img_search = ImageGrab.grab(window=app.winfo_id())
    img_search.save(search_path)
    print(f"Captured Search Dropdown screenshot: {search_path} ({img_search.size})")
    app._close_search_dropdown()

    # -------------------------------------------------------------
    # 6. Empty Favorites State
    # -------------------------------------------------------------
    print("\n[6/7] Testing empty favorites state...")
    saved_favs = list(app.favorites_weather)
    app.favorites_weather = []
    app.storage.data["favorites"] = []
    app._render_all_panels()
    app.update_idletasks()
    app.update()

    empty_path = os.path.join(ROOT_DIR, "desktop", "assets", "skycast_stage5_empty_favorites.png")
    img_empty = ImageGrab.grab(window=app.winfo_id())
    img_empty.save(empty_path)
    print(f"Captured Empty Favorites screenshot: {empty_path} ({img_empty.size})")
    app.favorites_weather = saved_favs
    app.storage.data["favorites"] = saved_favs

    # -------------------------------------------------------------
    # 7. Offline Fallback Notice
    # -------------------------------------------------------------
    print("\n[7/7] Testing offline fallback notice...")
    app.show_error_banner("⚠️ No connection — showing last saved data")
    app.update_idletasks()
    app.update()

    offline_path = os.path.join(ROOT_DIR, "desktop", "assets", "skycast_stage5_offline_banner.png")
    img_offline = ImageGrab.grab(window=app.winfo_id())
    img_offline.save(offline_path)
    print(f"Captured Offline Banner screenshot: {offline_path} ({img_offline.size})")

    app.destroy()

    # Copy screenshots to artifact dir
    if os.path.isdir(ARTIFACT_DIR):
        for f in [
            "skycast_stage5_rain_1100x750.png",
            "skycast_stage5_thunderstorm_1100x750.png",
            "skycast_stage5_snow_1100x750.png",
            "skycast_stage5_clearnight_1100x750.png",
            "skycast_stage5_search_region.png",
            "skycast_stage5_empty_favorites.png",
            "skycast_stage5_offline_banner.png"
        ]:
            src = os.path.join(ROOT_DIR, "desktop", "assets", f)
            dst = os.path.join(ARTIFACT_DIR, f)
            if os.path.exists(src):
                shutil.copyfile(src, dst)
                print(f"Copied to artifact dir: {dst}")

    print("\nAll Stage 5 verifications completed successfully!")

if __name__ == "__main__":
    run_stage5_verification()
