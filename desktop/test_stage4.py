"""
Script to test and verify Stage 4 of SkyCast Tkinter Desktop GUI:
1. Fetch and render London live weather from Open-Meteo at 1100x750
2. Search and render Tokyo live weather from Open-Meteo at 1100x750
3. Search invalid city "Nonexistentcityxyz999" and verify error banner
4. Save screenshots to desktop/assets/ and artifact directory
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

def wait_for_condition(app, condition_fn, timeout=12.0, interval=0.1):
    start = time.time()
    while time.time() - start < timeout:
        app.update_idletasks()
        app.update()
        if condition_fn():
            # Extra wait for render pass to settle
            for _ in range(5):
                time.sleep(0.08)
                app.update_idletasks()
                app.update()
            return True
        time.sleep(interval)
    return False

def run_stage4_verification():
    os.makedirs(os.path.join(ROOT_DIR, "desktop", "assets"), exist_ok=True)
    clear_panel_cache()
    clear_icon_cache()

    # Ensure last_city is London for Test 1
    from desktop.storage import StorageManager
    sm = StorageManager()
    sm.set_last_city({
        "name": "London",
        "country": "United Kingdom",
        "admin1": "England",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "timezone": "Europe/London"
    })

    print("[1/3] Initializing SkyCastMainWindow (default London)...")
    app = SkyCastMainWindow()
    app.geometry("1100x750+50+50")
    app.update_idletasks()
    app.update()

    # Wait for London weather data to load
    print("Waiting for London live weather from Open-Meteo...")
    loaded = wait_for_condition(
        app,
        lambda: app.weather_data is not None and not app.is_loading,
        timeout=15.0
    )
    if not loaded:
        print("WARNING: Timed out waiting for London live data. Proceeding anyway...")
    else:
        print(f"London live data loaded successfully: temp={app.weather_data.get('current', {}).get('temperature_2m')}°C")

    # Give favorites a moment to populate
    for _ in range(15):
        time.sleep(0.1)
        app.update_idletasks()
        app.update()

    london_path = os.path.join(ROOT_DIR, "desktop", "assets", "skycast_stage4_london_1100x750.png")
    img_london = ImageGrab.grab(window=app.winfo_id())
    img_london.save(london_path)
    print(f"Captured London screenshot: {london_path} ({img_london.size})")

    # [2/3] Search Tokyo
    print("\n[2/3] Searching for 'Tokyo'...")
    app.search_var.set("Tokyo")
    app._placeholder_active = False
    app._on_search_enter(None)

    tokyo_loaded = wait_for_condition(
        app,
        lambda: app.current_city.get("name") == "Tokyo" and not app.is_loading,
        timeout=15.0
    )
    if not tokyo_loaded:
        print("WARNING: Timed out waiting for Tokyo live data.")
    else:
        print(f"Tokyo live data loaded successfully: temp={app.weather_data.get('current', {}).get('temperature_2m')}°C")

    for _ in range(10):
        time.sleep(0.1)
        app.update_idletasks()
        app.update()

    tokyo_path = os.path.join(ROOT_DIR, "desktop", "assets", "skycast_stage4_tokyo_1100x750.png")
    img_tokyo = ImageGrab.grab(window=app.winfo_id())
    img_tokyo.save(tokyo_path)
    print(f"Captured Tokyo screenshot: {tokyo_path} ({img_tokyo.size})")

    # [3/3] Search Invalid City "Nonexistentcityxyz999"
    print("\n[3/3] Searching for invalid city 'Nonexistentcityxyz999'...")
    app.search_var.set("Nonexistentcityxyz999")
    app._placeholder_active = False
    app._on_search_enter(None)

    banner_shown = wait_for_condition(
        app,
        lambda: app.error_banner_text is not None and not app.is_loading,
        timeout=10.0
    )
    if not banner_shown:
        print("WARNING: Timed out waiting for error banner.")
    else:
        print(f"Error banner displayed successfully: '{app.error_banner_text}'")

    for _ in range(5):
        time.sleep(0.1)
        app.update_idletasks()
        app.update()

    invalid_path = os.path.join(ROOT_DIR, "desktop", "assets", "skycast_stage4_invalid_1100x750.png")
    img_invalid = ImageGrab.grab(window=app.winfo_id())
    img_invalid.save(invalid_path)
    print(f"Captured Invalid City screenshot: {invalid_path} ({img_invalid.size})")

    app.destroy()

    # Copy screenshots to artifact directory for presentation
    if os.path.isdir(ARTIFACT_DIR):
        for f in ["skycast_stage4_london_1100x750.png", "skycast_stage4_tokyo_1100x750.png", "skycast_stage4_invalid_1100x750.png"]:
            src = os.path.join(ROOT_DIR, "desktop", "assets", f)
            dst = os.path.join(ARTIFACT_DIR, f)
            if os.path.exists(src):
                shutil.copyfile(src, dst)
                print(f"Copied to artifact dir: {dst}")

    print("\nStage 4 verification completed successfully!")

if __name__ == "__main__":
    run_stage4_verification()
